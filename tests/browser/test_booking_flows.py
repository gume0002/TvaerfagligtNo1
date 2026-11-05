"""US1-US4 in a real browser against frontend, Nginx, backend and PostgreSQL."""

import os

import pytest
from playwright.sync_api import expect, sync_playwright
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.data_access.orm_models import BookingRow

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://test-frontend")


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture()
def page(browser, catalog):
    context = browser.new_context(base_url=FRONTEND_URL)
    page = context.new_page()
    page.goto("/")
    expect(page.locator("body")).to_have_attribute("data-ready", "true")
    yield page
    context.close()


def fill_booking(page, name="Anna Berg", room="Large Suite", arrival="2026-06-10", departure="2026-06-12", guests="2", rate="1000.00"):
    page.get_by_label("Gæstens navn").fill(name)
    page.get_by_label("Land", exact=True).select_option(label="Sweden")
    page.get_by_label("Værelsestype").select_option(label=room)
    page.get_by_label("Ankomst").fill(arrival)
    page.get_by_label("Afrejse").fill(departure)
    page.get_by_label("Antal gæster").fill(guests)
    page.get_by_label("Aftalt pris pr. nat (DKK)").fill(rate)


def create_booking(page, **values):
    fill_booking(page, **values)
    page.get_by_role("button", name="Opret booking").click()
    expect(page.locator("#global-message")).to_contain_text("er oprettet")


def row(page, name):
    return page.locator("#booking-rows tr").filter(has_text=name)


def booking_count(engine):
    with Session(engine) as session:
        return session.scalar(select(func.count()).select_from(BookingRow))


class TestUS1:
    def test_created_booking_is_still_there_after_reload(self, page):
        create_booking(page)
        expect(row(page, "Anna Berg")).to_contain_text("1000.00 DKK")
        page.reload()
        expect(row(page, "Anna Berg")).to_contain_text("Large Suite")
        expect(row(page, "Anna Berg")).to_contain_text("2026-06-10")

    def test_options_come_from_the_catalog_api(self, page):
        expect(page.locator("#roomTypeId option")).to_have_text(["Vælg værelsestype", "Tiny Room", "Double Room", "Large Suite"])
        page.get_by_label("Værelsestype").select_option(label="Tiny Room")
        expect(page.locator("#room-type-hint")).to_contain_text("Højst 2 gæster")

    def test_too_many_guests_show_an_understandable_error(self, page, engine):
        fill_booking(page, room="Tiny Room", guests="3")
        page.get_by_role("button", name="Opret booking").click()
        expect(page.locator('[data-error-for="guestCount"]')).to_contain_text("højst 2 gæster")
        expect(page.get_by_label("Gæstens navn")).to_have_value("Anna Berg")
        assert booking_count(engine) == 0

    def test_departure_before_arrival_shows_an_error(self, page, engine):
        fill_booking(page, arrival="2026-06-12", departure="2026-06-12")
        page.get_by_role("button", name="Opret booking").click()
        expect(page.locator('[data-error-for="departure"]')).to_contain_text("efter ankomst")
        assert booking_count(engine) == 0

    def test_invalid_price_shows_an_error(self, page, engine):
        fill_booking(page, rate="gratis")
        page.get_by_role("button", name="Opret booking").click()
        expect(page.locator('[data-error-for="nightlyRate"]')).not_to_be_empty()
        assert booking_count(engine) == 0

    def test_empty_form_shows_errors_and_creates_nothing(self, page, engine):
        page.get_by_role("button", name="Opret booking").click()
        expect(page.locator('[data-error-for="guestName"]')).not_to_be_empty()
        expect(page.locator('[data-error-for="countryId"]')).not_to_be_empty()
        assert booking_count(engine) == 0

    def test_full_room_type_shows_the_conflict(self, page, engine):
        create_booking(page, name="Første", room="Tiny Room")
        fill_booking(page, name="Anden", room="Tiny Room", arrival="2026-06-11", departure="2026-06-13")
        page.get_by_role("button", name="Opret booking").click()
        expect(page.locator("#global-message")).to_contain_text("fuldt booket")
        assert booking_count(engine) == 1

    def test_arrival_on_departure_day_is_accepted(self, page):
        create_booking(page, name="Første", room="Tiny Room")
        create_booking(page, name="Næste", room="Tiny Room", arrival="2026-06-12", departure="2026-06-14")
        expect(row(page, "Næste")).to_be_visible()

    def test_lost_response_does_not_create_a_duplicate_when_saving_again(self, page, engine):
        lost = []

        def lose_first_response(route):
            if not lost and route.request.method == "POST":
                lost.append(True)
                route.fetch()
                route.abort()
            else:
                route.continue_()

        page.route("**/api/bookings", lose_first_response)
        fill_booking(page)
        page.get_by_role("button", name="Opret booking").click()
        expect(page.locator("#global-message")).to_contain_text("Kunne ikke få kontakt")
        assert booking_count(engine) == 1

        page.get_by_role("button", name="Opret booking").click()
        expect(page.locator("#global-message")).to_contain_text("er oprettet")
        assert booking_count(engine) == 1

    def test_guest_name_is_shown_as_text_and_not_as_html(self, page):
        create_booking(page, name="<img src=x onerror=alert(1)>")
        expect(row(page, "<img src=x onerror=alert(1)>")).to_be_visible()
        expect(page.locator("#booking-rows img")).to_have_count(0)


def test_page_has_no_horizontal_scroll_on_a_phone(page):
    create_booking(page, name="Gæst med et langt navn til telefonvisningen")
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")


class TestUS2:
    def test_name_and_dates_can_be_combined(self, page):
        create_booking(page, name="Anna Juni", arrival="2026-06-10", departure="2026-06-12")
        create_booking(page, name="Anna Juli", arrival="2026-07-10", departure="2026-07-12")
        create_booking(page, name="Bo Juli", arrival="2026-07-10", departure="2026-07-12")
        page.get_by_label("Navn", exact=True).fill("aNnA")
        page.get_by_label("Ophold fra").fill("2026-07-01")
        page.get_by_label("Ophold til").fill("2026-07-31")
        page.get_by_role("button", name="Søg").click()
        expect(page.locator("#booking-rows tr")).to_have_count(1)
        expect(row(page, "Anna Juli")).to_be_visible()

    def test_stays_touching_the_interval_are_not_shown(self, page):
        create_booking(page, name="Slutter den 10.", arrival="2026-06-08", departure="2026-06-10")
        create_booking(page, name="Starter den 12.", arrival="2026-06-12", departure="2026-06-14")
        create_booking(page, name="Overlapper", arrival="2026-06-11", departure="2026-06-13")
        page.get_by_label("Ophold fra").fill("2026-06-10")
        page.get_by_label("Ophold til").fill("2026-06-12")
        page.get_by_role("button", name="Søg").click()
        expect(page.locator("#booking-rows tr")).to_have_count(1)
        expect(row(page, "Overlapper")).to_be_visible()

    def test_no_match_shows_the_empty_state(self, page):
        create_booking(page)
        page.get_by_label("Navn", exact=True).fill("findes ikke")
        page.get_by_role("button", name="Søg").click()
        expect(page.locator("#empty-state")).to_be_visible()
        page.get_by_role("button", name="Nulstil").click()
        expect(row(page, "Anna Berg")).to_be_visible()
        expect(page.locator("#empty-state")).to_be_hidden()

    def test_only_one_date_shows_an_error(self, page):
        page.get_by_label("Ophold fra").fill("2026-06-10")
        page.get_by_role("button", name="Søg").click()
        expect(page.locator("#search-message")).to_contain_text("Filtrene er ugyldige")


class TestUS3:
    def test_edit_saves_on_the_same_booking(self, page):
        create_booking(page)
        booking_id = row(page, "Anna Berg").get_attribute("data-booking-id")
        row(page, "Anna Berg").get_by_role("button", name="Ret").click()
        expect(page.locator("#form-title")).to_contain_text(f"Ret booking nr. {booking_id}")
        expect(page.get_by_label("Aftalt pris pr. nat (DKK)")).to_have_value("1000.00")
        page.get_by_label("Gæstens navn").fill("Anna Rettet")
        page.get_by_role("button", name="Gem ændringer").click()
        expect(page.locator("#global-message")).to_contain_text("er gemt")
        expect(row(page, "Anna Rettet")).to_have_attribute("data-booking-id", booking_id)
        expect(page.locator("#booking-rows tr")).to_have_count(1)

    def test_rejected_edit_keeps_the_form_values_and_the_saved_booking(self, page):
        create_booking(page, name="Optager", room="Tiny Room", arrival="2026-06-20", departure="2026-06-22")
        create_booking(page, name="Flyttes", room="Tiny Room")
        row(page, "Flyttes").get_by_role("button", name="Ret").click()
        page.get_by_label("Gæstens navn").fill("Må ikke gemmes")
        page.get_by_label("Ankomst").fill("2026-06-19")
        page.get_by_label("Afrejse").fill("2026-06-21")
        page.get_by_role("button", name="Gem ændringer").click()
        expect(page.locator("#global-message")).to_contain_text("fuldt booket")
        expect(page.get_by_label("Gæstens navn")).to_have_value("Må ikke gemmes")
        expect(row(page, "Flyttes")).to_contain_text("2026-06-10")
        page.reload()
        expect(row(page, "Flyttes")).to_contain_text("2026-06-10")
        expect(row(page, "Må ikke gemmes")).to_have_count(0)

    def test_cancel_edit_returns_to_create(self, page):
        create_booking(page)
        row(page, "Anna Berg").get_by_role("button", name="Ret").click()
        page.get_by_role("button", name="Annullér rettelse").click()
        expect(page.locator("#form-title")).to_have_text("Opret booking")
        expect(page.get_by_label("Gæstens navn")).to_have_value("")


class TestUS4:
    def test_confirmed_delete_moves_the_booking_to_history(self, page):
        create_booking(page)
        page.once("dialog", lambda dialog: dialog.accept())
        row(page, "Anna Berg").get_by_role("button", name="Slet").click()
        expect(page.locator("#global-message")).to_contain_text("er aflyst")
        expect(row(page, "Anna Berg")).to_have_count(0)

        page.get_by_label("Vis").select_option(label="Aflyste (historik)")
        page.get_by_role("button", name="Søg").click()
        expect(row(page, "Anna Berg")).to_contain_text("Aflyst")
        expect(row(page, "Anna Berg").get_by_role("button")).to_have_count(0)

    def test_declined_delete_changes_nothing(self, page):
        create_booking(page)
        page.once("dialog", lambda dialog: dialog.dismiss())
        row(page, "Anna Berg").get_by_role("button", name="Slet").click()
        expect(row(page, "Anna Berg")).to_contain_text("Aktiv")

    def test_deleted_booking_frees_the_room(self, page):
        create_booking(page, name="Første", room="Tiny Room")
        page.once("dialog", lambda dialog: dialog.accept())
        row(page, "Første").get_by_role("button", name="Slet").click()
        expect(page.locator("#global-message")).to_contain_text("er aflyst")
        create_booking(page, name="Anden", room="Tiny Room")
        expect(row(page, "Anden")).to_be_visible()
