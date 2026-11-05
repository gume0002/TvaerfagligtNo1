"""US14: the analytics page shows the API's figures, in a real browser."""

import json
import os
from datetime import date
from uuid import uuid4

import pytest
from playwright.sync_api import expect, sync_playwright
from sqlalchemy import text

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://test-frontend")
YEAR = date.today().year


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture()
def context(browser, catalog):
    context = browser.new_context(base_url=FRONTEND_URL)
    yield context
    context.close()


def open_page(context):
    page = context.new_page()
    page.goto("/analytics.html")
    expect(page.locator("body")).to_have_attribute("data-ready", "true")
    return page


def book(context, catalog, **changes):
    payload = dict(guestName="Gæst", countryId=catalog.sweden, roomTypeId=catalog.large, arrival=f"{YEAR}-06-10",
                   departure=f"{YEAR}-06-13", guestCount=2, nightlyRate="1000.00") | changes
    response = context.request.post("/api/bookings", data=json.dumps(payload),
                                    headers={"Content-Type": "application/json", "Idempotency-Key": str(uuid4())})
    assert response.status == 201, response.text()
    return response.json()


def sell(context, drink_id, employee_id, quantity, price):
    payload = dict(drinkId=drink_id, employeeId=employee_id, quantity=quantity, unitPrice=price, saleDate=date.today().isoformat())
    response = context.request.post("/api/bar-sales", data=json.dumps(payload),
                                    headers={"Content-Type": "application/json", "Idempotency-Key": str(uuid4())})
    assert response.status == 201, response.text()
    return response.json()


@pytest.fixture()
def bar_sales(context, empty_database, catalog):
    with empty_database.begin() as connection:
        connection.execute(text("INSERT INTO drinks (name, category, suggested_unit_price) VALUES ('Latte', 'coffee', 50)"))
    catalogs = context.request.get("/api/catalogs").json()
    drinks = {item["name"]: item["id"] for item in catalogs["drinks"]}
    employee = catalogs["employees"][0]["id"]
    sell(context, drinks["Negroni"], employee, 3, "100.00")
    sell(context, drinks["Latte"], employee, 2, "50.00")


def test_page_is_linked_from_the_other_pages(context):
    page = context.new_page()
    for path in ("/", "/sales.html"):
        page.goto(path)
        expect(page.get_by_role("link", name="Analyser")).to_have_attribute("href", "analytics.html")


class TestHotel:
    def test_figures_from_the_api_are_shown(self, context, catalog):
        book(context, catalog)
        page = open_page(context)
        expect(page.locator("#hotel-revenue")).to_have_text("3.000,00 DKK")
        expect(page.locator("#hotel-adr")).to_have_text("1.000,00 DKK")
        expect(page.locator("#chart-room-types")).to_contain_text("1. Large Suite")
        expect(page.locator("#chart-countries")).to_contain_text("1. Sweden")
        expect(page.locator("#chart-guests")).to_contain_text("Sweden")
        expect(page.locator("#chart-guests")).to_contain_text("2")

    def test_filters_fetch_new_figures(self, context, catalog):
        book(context, catalog)
        book(context, catalog, countryId=catalog.germany, nightlyRate="500.00")
        page = open_page(context)
        expect(page.locator("#hotel-revenue")).to_have_text("4.500,00 DKK")
        with page.expect_request(lambda request: "countryId" in request.url):
            page.get_by_label("Land", exact=True).select_option(label="Germany")
        expect(page.locator("#hotel-revenue")).to_have_text("1.500,00 DKK")
        expect(page.locator("#hotel-tiles")).to_contain_text("Landets bidrag til belægningen")

    def test_season_without_bookings_shows_no_data(self, context, catalog):
        book(context, catalog)
        page = open_page(context)
        page.get_by_label("Sæson", exact=True).select_option(label="Lavsæson")
        expect(page.locator("#hotel-revenue")).to_have_text("0,00 DKK")
        expect(page.locator("#hotel-adr")).to_have_text("Intet datagrundlag")
        expect(page.locator("#chart-room-types")).to_contain_text("Ingen data for dette valg")

    def test_satisfaction_has_no_score(self, context):
        expect(open_page(context).locator("#hotel-satisfaction")).to_have_text("Intet datagrundlag")

    def test_new_and_cancelled_bookings_appear_when_the_page_is_loaded_again(self, context, catalog):
        page = open_page(context)
        expect(page.locator("#hotel-revenue")).to_have_text("0,00 DKK")
        created = book(context, catalog)
        page.reload()
        expect(page.locator("#hotel-revenue")).to_have_text("3.000,00 DKK")
        assert context.request.delete(f"/api/bookings/{created['id']}").status == 204
        page.reload()
        expect(page.locator("#hotel-revenue")).to_have_text("0,00 DKK")


    def test_edited_booking_gives_new_figures(self, context, catalog):
        created = book(context, catalog)
        page = open_page(context)
        expect(page.locator("#hotel-revenue")).to_have_text("3.000,00 DKK")
        payload = {key: created[key] for key in ("guestName", "countryId", "roomTypeId", "arrival", "departure", "guestCount")}
        response = context.request.put(f"/api/bookings/{created['id']}", data=json.dumps(payload | {"nightlyRate": "2000.00"}),
                                       headers={"Content-Type": "application/json"})
        assert response.status == 200, response.text()
        page.reload()
        expect(page.locator("#hotel-revenue")).to_have_text("6.000,00 DKK")

    def test_year_and_room_type_filters_fetch_new_figures(self, context, catalog):
        book(context, catalog)
        book(context, catalog, roomTypeId=catalog.double, nightlyRate="500.00")
        page = open_page(context)
        page.get_by_label("Værelsestype", exact=True).select_option(label="Double Room")
        expect(page.locator("#hotel-revenue")).to_have_text("1.500,00 DKK")
        page.get_by_label("Værelsestype", exact=True).select_option(label="Alle")
        expect(page.locator("#hotel-revenue")).to_have_text("4.500,00 DKK")
        page.get_by_label("År", exact=True).select_option(str(YEAR - 1))
        expect(page.locator("#hotel-revenue")).to_have_text("0,00 DKK")


class TestBar:
    def test_us9_1_figures_and_shares(self, context, bar_sales):
        page = open_page(context)
        expect(page.locator("#bar-revenue")).to_have_text("400,00 DKK")
        expect(page.locator("#bar-quantity")).to_have_text("5")
        shares = page.locator("#chart-categories")
        expect(shares).to_contain_text("Cocktail 60,00 %")
        expect(shares).to_contain_text("Kaffe 40,00 %")
        expect(shares).to_contain_text("Cocktail 75,00 %")
        expect(shares).to_contain_text("Kaffe 25,00 %")
        expect(page.locator("#chart-drinks")).to_contain_text("Negroni")
        expect(page.locator("#bar-employee")).to_have_text("Helene Christine")

    def test_new_and_cancelled_sale_give_new_figures(self, context, bar_sales):
        page = open_page(context)
        expect(page.locator("#bar-revenue")).to_have_text("400,00 DKK")
        catalogs = context.request.get("/api/catalogs").json()
        negroni = next(item["id"] for item in catalogs["drinks"] if item["name"] == "Negroni")
        sale = sell(context, negroni, catalogs["employees"][0]["id"], 1, "100.00")
        page.reload()
        expect(page.locator("#bar-revenue")).to_have_text("500,00 DKK")
        assert context.request.delete(f"/api/bar-sales/{sale['id']}").status == 204
        page.reload()
        expect(page.locator("#bar-revenue")).to_have_text("400,00 DKK")

    def test_edited_sale_gives_new_figures(self, context, bar_sales):
        page = open_page(context)
        expect(page.locator("#bar-revenue")).to_have_text("400,00 DKK")
        sale = context.request.get("/api/bar-sales").json()["items"][0]
        payload = {key: sale[key] for key in ("drinkId", "employeeId", "quantity", "saleDate")}
        response = context.request.put(f"/api/bar-sales/{sale['id']}", data=json.dumps(payload | {"quantity": sale["quantity"] + 1, "unitPrice": sale["unitPrice"]}),
                                       headers={"Content-Type": "application/json"})
        assert response.status == 200, response.text()
        page.reload()
        expect(page.locator("#bar-revenue")).not_to_have_text("400,00 DKK")

    def test_employee_filter_fetches_that_employees_figures(self, context, empty_database, bar_sales):
        with empty_database.begin() as connection:
            connection.execute(text("INSERT INTO employees (code, name) VALUES ('anden', 'Anden Bartender')"))
        page = open_page(context)
        expect(page.locator("#bar-revenue")).to_have_text("400,00 DKK")
        page.get_by_label("Medarbejder (bar)", exact=True).select_option(label="Anden Bartender")
        expect(page.locator("#bar-employee")).to_have_text("Anden Bartender")
        expect(page.locator("#bar-revenue")).to_have_text("0,00 DKK")

    def test_drinks_without_sales_are_shown(self, context, empty_database, catalog):
        with empty_database.begin() as connection:
            connection.execute(text("INSERT INTO drinks (name, category, suggested_unit_price) VALUES ('Latte', 'coffee', 50)"))
        drinks = open_page(context).locator("#chart-drinks")
        expect(drinks).to_contain_text("Latte")
        expect(drinks).to_contain_text("0,00 DKK")

    def test_no_sales_shows_no_data_and_zero(self, context):
        page = open_page(context)
        expect(page.locator("#bar-revenue")).to_have_text("0,00 DKK")
        expect(page.locator("#chart-categories")).to_contain_text("Intet datagrundlag")


class TestOnlyShowsTheApi:
    def test_page_shows_shares_from_the_api_and_does_not_calculate_them(self, context, bar_sales):
        """Deliberately wrong figures from the API must be shown as they are."""
        page = context.new_page()

        def changed(route):
            response = route.fetch()
            data = response.json()
            data["totals"]["revenue"] = "111.11"
            for item in data["byCategory"]:
                item["quantitySharePercent"] = "12.34"
            route.fulfill(response=response, json=data)

        page.route("**/api/analytics/bar*", changed)
        page.goto("/analytics.html")
        expect(page.locator("#bar-revenue")).to_have_text("111,11 DKK")
        expect(page.locator("#chart-categories")).to_contain_text("Cocktail 12,34 %")

    def test_demo_marking_and_time_are_shown(self, context, empty_database):
        with empty_database.begin() as connection:
            connection.execute(text("UPDATE room_types SET demo_data = true"))
        status = open_page(context).locator("#data-status")
        expect(status).to_contain_text("Data fra")
        expect(status).to_contain_text("dansk tid")
        expect(status).to_contain_text("Demodata")


class TestErrorsAndLayout:
    def test_lost_api_gives_an_error_and_hides_old_figures(self, context, catalog):
        book(context, catalog)
        page = open_page(context)
        expect(page.locator("#hotel-revenue")).to_be_visible()
        page.route("**/api/analytics/**", lambda route: route.abort())
        page.get_by_label("Sæson", exact=True).select_option(label="Højsæson")
        expect(page.locator("#analytics-error")).to_contain_text("Kunne ikke få kontakt")
        expect(page.locator("#hotel-revenue")).to_be_hidden()
        page.unroute("**/api/analytics/**")
        page.get_by_label("Sæson", exact=True).select_option(label="Alle")
        expect(page.locator("#hotel-revenue")).to_have_text("3.000,00 DKK")
        expect(page.locator("#analytics-error")).to_be_hidden()

    def test_names_are_shown_as_text_and_not_as_html(self, context, empty_database, catalog):
        with empty_database.begin() as connection:
            connection.execute(text("UPDATE countries SET name = '<img src=x onerror=alert(1)>' WHERE code = 'SE'"))
        book(context, catalog)
        page = open_page(context)
        expect(page.locator("#chart-countries")).to_contain_text("<img src=x")
        expect(page.locator("#chart-countries img")).to_have_count(0)

    def test_tooltip_and_keyboard_show_the_value(self, context, catalog):
        book(context, catalog)
        page = open_page(context)
        page.locator("#chart-countries .bar-segment").first.focus()
        expect(page.locator("#chart-tooltip")).to_contain_text("3.000,00 DKK")

    def test_table_view_has_the_values(self, context, catalog):
        book(context, catalog)
        page = open_page(context)
        page.locator("#chart-countries").locator("xpath=following-sibling::details").locator("summary").click()
        expect(page.locator("#table-countries")).to_contain_text("3.000,00 DKK")

    def test_no_horizontal_scroll_on_a_phone(self, context, catalog):
        book(context, catalog)
        page = context.new_page()
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto("/analytics.html")
        expect(page.locator("body")).to_have_attribute("data-ready", "true")
        expect(page.locator("#hotel-revenue")).to_be_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
