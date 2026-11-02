"""US1-US4 through HTTP, the three layers and real MySQL.

Every response is also compared with the OpenAPI contract.
"""

from itertools import count
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.data_access.orm_models import BookingRow, IdempotencyRequestRow
from app.main import create_app
from testsupport.contract import assert_matches_contract

COLLECTION = "/api/bookings"
ITEM = "/api/bookings/{id}"


@pytest.fixture()
def client(settings, frozen_clock, catalog):
    with TestClient(create_app(settings, frozen_clock), raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture()
def body(catalog):
    numbers = count(1)

    def make(**changes):
        values = dict(
            guestName=f"Gæst {next(numbers)}",
            countryId=catalog.sweden,
            roomTypeId=catalog.large,
            arrival="2026-06-10",
            departure="2026-06-12",
            guestCount=2,
            nightlyRate="1000.00",
        )
        return values | changes

    return make


def post(client, payload, key=None):
    response = client.post(COLLECTION, json=payload, headers={"Idempotency-Key": key or str(uuid4())})
    assert_matches_contract(response, "POST", COLLECTION)
    return response


def create(client, payload):
    response = post(client, payload)
    assert response.status_code == 201, response.text
    return response.json()


def search(client, **params):
    response = client.get(COLLECTION, params=params)
    assert_matches_contract(response, "GET", COLLECTION)
    assert response.status_code == 200, response.text
    return response.json()


def get(client, booking_id, **params):
    response = client.get(f"{COLLECTION}/{booking_id}", params=params)
    assert_matches_contract(response, "GET", ITEM)
    return response


def put(client, booking_id, payload):
    response = client.put(f"{COLLECTION}/{booking_id}", json=payload)
    assert_matches_contract(response, "PUT", ITEM)
    return response


def delete(client, booking_id):
    response = client.delete(f"{COLLECTION}/{booking_id}")
    assert_matches_contract(response, "DELETE", ITEM)
    return response


def fields(response) -> set[str]:
    return {item["field"] for item in response.json()["fieldErrors"]}


def booking_count(engine) -> int:
    with Session(engine) as session:
        return session.scalar(select(func.count()).select_from(BookingRow))


class TestUS1Create:
    def test_valid_booking_gets_an_identity_and_can_be_found_again(self, client, body):
        response = post(client, body(guestName="Anna Berg"))
        assert response.status_code == 201
        created = response.json()
        assert response.headers["Location"] == f"{COLLECTION}/{created['id']}"
        assert created["guestName"] == "Anna Berg"
        assert created["countryName"] == "Sweden"
        assert created["roomTypeName"] == "Large Suite"
        assert created["nightlyRate"] == "1000.00"
        assert created["status"] == "active"
        assert created["demoData"] is False
        assert created["cancelledAt"] is None
        assert get(client, created["id"]).json() == created

    def test_too_many_guests_are_rejected_and_nothing_is_created(self, client, body, catalog, engine):
        response = post(client, body(roomTypeId=catalog.tiny, guestCount=3))
        assert response.status_code == 400
        assert response.json()["code"] == "validation_error"
        assert fields(response) == {"guestCount"}
        assert "højst 2 gæster" in response.json()["fieldErrors"][0]["message"]
        assert booking_count(engine) == 0

    @pytest.mark.parametrize(
        ("changes", "field"),
        [
            ({"departure": "2026-06-10"}, "departure"),
            ({"departure": "2026-06-09"}, "departure"),
            ({"nightlyRate": "0"}, "nightlyRate"),
            ({"nightlyRate": "0.00"}, "nightlyRate"),
            ({"nightlyRate": "-10.00"}, "nightlyRate"),
            ({"nightlyRate": "10.123"}, "nightlyRate"),
            ({"nightlyRate": 1000}, "nightlyRate"),
            ({"nightlyRate": "abc"}, "nightlyRate"),
            ({"guestCount": 0}, "guestCount"),
            ({"guestCount": "2"}, "guestCount"),
            ({"guestCount": 2.5}, "guestCount"),
            ({"guestName": ""}, "guestName"),
            ({"guestName": "   "}, "guestName"),
            ({"guestName": "x" * 201}, "guestName"),
            ({"arrival": "10-06-2026"}, "arrival"),
            ({"arrival": "2026-02-30"}, "arrival"),
            ({"arrival": 20260610}, "arrival"),
            ({"countryId": 9999}, "countryId"),
            ({"roomTypeId": 9999}, "roomTypeId"),
            ({"somethingElse": 1}, "somethingElse"),
        ],
    )
    def test_invalid_input_is_rejected_and_nothing_is_created(self, client, body, engine, changes, field):
        response = post(client, body(**changes))
        assert response.status_code == 400, response.text
        assert field in fields(response)
        assert response.json()["requestId"]
        assert booking_count(engine) == 0

    def test_missing_field_is_named(self, client, body):
        payload = body()
        del payload["guestName"]
        response = post(client, payload)
        assert response.status_code == 400
        assert fields(response) == {"guestName"}

    def test_invalid_json_gives_the_shared_error_format(self, client):
        response = client.post(
            COLLECTION,
            content="{not json",
            headers={"Idempotency-Key": "k", "Content-Type": "application/json"},
        )
        assert_matches_contract(response, "POST", COLLECTION)
        assert response.status_code == 400

    def test_missing_idempotency_key_is_rejected(self, client, body):
        response = client.post(COLLECTION, json=body())
        assert_matches_contract(response, "POST", COLLECTION)
        assert response.status_code == 400
        assert fields(response) == {"Idempotency-Key"}

    def test_full_room_type_gives_409(self, client, body, catalog, engine):
        create(client, body(roomTypeId=catalog.tiny))
        response = post(client, body(roomTypeId=catalog.tiny, arrival="2026-06-11", departure="2026-06-13"))
        assert response.status_code == 409
        assert response.json()["code"] == "capacity_conflict"
        assert "2026-06-11" in response.json()["message"]
        assert booking_count(engine) == 1

    def test_arrival_on_departure_day_is_allowed(self, client, body, catalog):
        create(client, body(roomTypeId=catalog.tiny))
        create(client, body(roomTypeId=catalog.tiny, arrival="2026-06-12", departure="2026-06-14"))
        create(client, body(roomTypeId=catalog.tiny, arrival="2026-06-08", departure="2026-06-10"))

    def test_historical_booking_is_allowed(self, client, body):
        create(client, body(arrival="2020-01-01", departure="2020-01-03"))


class TestIdempotency:
    def test_repeating_a_request_returns_the_first_result_without_a_new_booking(self, client, body, engine):
        payload = body()
        first = post(client, payload, key="same-key")
        second = post(client, payload, key="same-key")
        assert first.status_code == second.status_code == 201
        assert second.json() == first.json()
        assert second.headers["Location"] == first.headers["Location"]
        assert booking_count(engine) == 1

    def test_same_amount_written_differently_counts_as_the_same_input(self, client, body, engine):
        post(client, body(guestName="A", nightlyRate="1000"), key="same-key")
        assert post(client, body(guestName="A", nightlyRate="1000.00"), key="same-key").status_code == 201
        assert booking_count(engine) == 1

    def test_same_key_with_other_input_gives_409(self, client, body, engine):
        post(client, body(guestName="A"), key="same-key")
        response = post(client, body(guestName="B"), key="same-key")
        assert response.status_code == 409
        assert response.json()["code"] == "idempotency_conflict"
        assert booking_count(engine) == 1

    def test_replay_returns_the_original_result_after_a_later_change(self, client, body):
        payload = body(guestName="Original")
        first = post(client, payload, key="same-key").json()
        assert put(client, first["id"], body(guestName="Rettet")).status_code == 200
        assert post(client, payload, key="same-key").json() == first

    def test_rejected_request_does_not_use_up_the_key(self, client, body, engine):
        payload = body(guestCount=99)
        assert post(client, payload, key="same-key").status_code == 400
        with Session(engine) as session:
            assert session.scalar(select(func.count()).select_from(IdempotencyRequestRow)) == 0
        assert post(client, body(), key="same-key").status_code == 201


class TestUS2Search:
    def test_name_search_ignores_case_and_shows_all_booking_details(self, client, body):
        anna = create(client, body(guestName="Anna Berg"))
        create(client, body(guestName="Bo Lund"))
        result = search(client, name="aNnA")
        assert result["total"] == 1
        assert result["items"] == [anna]

    @pytest.mark.parametrize("term", ["%", "_", "100%", "a_b"])
    def test_wildcards_are_treated_literally(self, client, body, term):
        create(client, body(guestName="Anna Berg"))
        assert search(client, name=term)["total"] == 0

    def test_wildcards_find_literal_matches(self, client, body):
        create(client, body(guestName="100% Gæst"))
        create(client, body(guestName="a_b"))
        create(client, body(guestName="aXb"))
        assert search(client, name="100%")["total"] == 1
        assert search(client, name="a_b")["total"] == 1

    def test_date_interval_shows_stays_with_at_least_one_common_night(self, client, body):
        ends_on_start = create(client, body(guestName="Slut", arrival="2026-06-08", departure="2026-06-10"))
        starts_on_end = create(client, body(guestName="Start", arrival="2026-06-12", departure="2026-06-14"))
        overlap_first = create(client, body(guestName="Første", arrival="2026-06-09", departure="2026-06-11"))
        overlap_last = create(client, body(guestName="Sidste", arrival="2026-06-11", departure="2026-06-13"))
        result = search(client, arrivalFrom="2026-06-10", departureTo="2026-06-12")
        ids = {item["id"] for item in result["items"]}
        assert ids == {overlap_first["id"], overlap_last["id"]}
        assert ends_on_start["id"] not in ids
        assert starts_on_end["id"] not in ids

    def test_name_and_date_filters_combine(self, client, body):
        create(client, body(guestName="Anna A", arrival="2026-06-10", departure="2026-06-11"))
        match = create(client, body(guestName="Anna B", arrival="2026-07-10", departure="2026-07-11"))
        create(client, body(guestName="Bo", arrival="2026-07-10", departure="2026-07-11"))
        result = search(client, name="anna", arrivalFrom="2026-07-01", departureTo="2026-07-31")
        assert [item["id"] for item in result["items"]] == [match["id"]]

    def test_no_match_gives_an_empty_result(self, client):
        assert search(client, name="findes ikke") == {"items": [], "total": 0}

    def test_cancelled_bookings_are_only_shown_when_chosen(self, client, body):
        active = create(client, body(guestName="Aktiv"))
        cancelled = create(client, body(guestName="Aflyst"))
        delete(client, cancelled["id"])
        assert [item["id"] for item in search(client)["items"]] == [active["id"]]
        historic = search(client, status="cancelled")["items"]
        assert [item["id"] for item in historic] == [cancelled["id"]]
        assert historic[0]["status"] == "cancelled"
        assert historic[0]["cancelledAt"]
        assert {item["id"] for item in search(client, status="all")["items"]} == {active["id"], cancelled["id"]}

    def test_pagination_is_stable_and_total_counts_all_matches(self, client, body):
        ids = [create(client, body(guestName=f"G{number}"))["id"] for number in range(5)]
        first = search(client, limit=2, offset=0)
        second = search(client, limit=2, offset=2)
        beyond = search(client, limit=2, offset=100)
        assert first["total"] == second["total"] == beyond["total"] == 5
        assert [item["id"] for item in first["items"] + second["items"]] == ids[:4]
        assert beyond["items"] == []

    @pytest.mark.parametrize(
        "params",
        [
            {"arrivalFrom": "2026-06-10"},
            {"departureTo": "2026-06-10"},
            {"arrivalFrom": "2026-06-12", "departureTo": "2026-06-10"},
            {"arrivalFrom": "not-a-date", "departureTo": "2026-06-10"},
            {"status": "unknown"},
            {"limit": 0},
            {"limit": 201},
            {"offset": -1},
        ],
    )
    def test_invalid_filters_give_400(self, client, params):
        response = client.get(COLLECTION, params=params)
        assert_matches_contract(response, "GET", COLLECTION)
        assert response.status_code == 400


class TestUS3Update:
    def test_all_fields_are_saved_on_the_same_identity(self, client, body, catalog):
        created = create(client, body())
        response = put(
            client,
            created["id"],
            {
                "guestName": "Nyt Navn",
                "countryId": catalog.germany,
                "roomTypeId": catalog.double,
                "arrival": "2026-08-01",
                "departure": "2026-08-05",
                "guestCount": 1,
                "nightlyRate": "1250.50",
            },
        )
        assert response.status_code == 200
        updated = response.json()
        assert updated["id"] == created["id"]
        assert updated["guestName"] == "Nyt Navn"
        assert updated["countryName"] == "Germany"
        assert updated["roomTypeName"] == "Double Room"
        assert updated["arrival"] == "2026-08-01"
        assert updated["departure"] == "2026-08-05"
        assert updated["guestCount"] == 1
        assert updated["nightlyRate"] == "1250.50"
        assert get(client, created["id"]).json() == updated

    def test_unchanged_dates_do_not_count_the_booking_twice(self, client, body, catalog):
        created = create(client, body(roomTypeId=catalog.tiny))
        response = put(client, created["id"], body(roomTypeId=catalog.tiny, guestName="Rettet"))
        assert response.status_code == 200
        assert response.json()["guestName"] == "Rettet"

    def test_change_that_overbooks_is_rejected_and_the_booking_is_preserved(self, client, body, catalog):
        create(client, body(roomTypeId=catalog.tiny, arrival="2026-06-20", departure="2026-06-22"))
        moved = create(client, body(roomTypeId=catalog.tiny))
        response = put(client, moved["id"], body(roomTypeId=catalog.tiny, guestName="Må ikke gemmes", arrival="2026-06-19", departure="2026-06-21"))
        assert response.status_code == 409
        assert response.json()["code"] == "capacity_conflict"
        assert get(client, moved["id"]).json() == moved

    def test_change_to_a_full_type_is_rejected(self, client, body, catalog):
        create(client, body(roomTypeId=catalog.tiny))
        other = create(client, body(roomTypeId=catalog.double))
        assert put(client, other["id"], body(roomTypeId=catalog.tiny)).status_code == 409
        assert get(client, other["id"]).json() == other

    @pytest.mark.parametrize(
        "changes",
        [{"departure": "2026-06-01"}, {"guestCount": 99}, {"nightlyRate": "0"}, {"countryId": 9999}, {"roomTypeId": 9999}],
    )
    def test_invalid_change_preserves_the_booking(self, client, body, changes):
        created = create(client, body())
        assert put(client, created["id"], body(guestName="Må ikke gemmes", **changes)).status_code == 400
        assert get(client, created["id"]).json() == created

    def test_agreed_rate_is_kept_unless_it_is_changed(self, client, body):
        created = create(client, body(nightlyRate="777.00"))
        assert put(client, created["id"], body(nightlyRate="777.00", guestName="Rettet")).json()["nightlyRate"] == "777.00"
        assert put(client, created["id"], body(nightlyRate="888.00")).json()["nightlyRate"] == "888.00"

    def test_unknown_booking_gives_404(self, client, body):
        assert put(client, 999999, body()).status_code == 404

    def test_cancelled_booking_cannot_be_changed(self, client, body):
        created = create(client, body())
        delete(client, created["id"])
        response = put(client, created["id"], body())
        assert response.status_code == 409
        assert response.json()["code"] == "resource_cancelled"


class TestUS4Delete:
    def test_delete_hides_the_booking_but_keeps_it_in_history(self, client, body):
        created = create(client, body())
        assert delete(client, created["id"]).status_code == 204
        assert get(client, created["id"]).status_code == 404
        kept = get(client, created["id"], includeCancelled="true")
        assert kept.status_code == 200
        assert kept.json()["status"] == "cancelled"
        assert kept.json()["cancelledAt"]

    def test_delete_frees_capacity(self, client, body, catalog):
        created = create(client, body(roomTypeId=catalog.tiny))
        assert post(client, body(roomTypeId=catalog.tiny)).status_code == 409
        delete(client, created["id"])
        assert post(client, body(roomTypeId=catalog.tiny)).status_code == 201

    def test_repeated_delete_changes_nothing(self, client, body, frozen_clock):
        from datetime import date

        created = create(client, body())
        delete(client, created["id"])
        first = get(client, created["id"], includeCancelled="true").json()
        frozen_clock.today = date(2027, 1, 1)
        assert delete(client, created["id"]).status_code == 204
        assert get(client, created["id"], includeCancelled="true").json() == first

    def test_unknown_booking_gives_404_and_others_are_untouched(self, client, body):
        other = create(client, body())
        response = delete(client, 999999)
        assert response.status_code == 404
        assert response.json()["code"] == "not_found"
        assert get(client, other["id"]).json() == other

    @pytest.mark.parametrize("operation", ["get", "put", "delete"])
    def test_invalid_id_gives_400(self, client, body, operation):
        response = getattr(client, operation)(f"{COLLECTION}/abc", **({"json": body()} if operation == "put" else {}))
        assert_matches_contract(response, operation.upper(), ITEM)
        assert response.status_code == 400


class TestCatalogsAndHealth:
    def test_catalogs_come_through_all_layers(self, client, catalog):
        response = client.get("/api/catalogs")
        assert_matches_contract(response, "GET", "/api/catalogs")
        assert response.status_code == 200
        data = response.json()
        assert {item["name"] for item in data["countries"]} == {"Sweden", "Germany"}
        tiny = next(item for item in data["roomTypes"] if item["id"] == catalog.tiny)
        assert tiny["maxGuests"] == 2
        assert tiny["demoData"] is True
        assert tiny["suggestedNightlyRates"] == {"low": "900.00", "mid": "1000.00", "high": "1100.00"}

    def test_health_is_ready_with_marker(self, client):
        response = client.get("/api/health")
        assert_matches_contract(response, "GET", "/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}

    def test_health_is_unavailable_without_marker(self, settings, frozen_clock, empty_database):
        with TestClient(create_app(settings, frozen_clock)) as client:
            response = client.get("/api/health")
        assert_matches_contract(response, "GET", "/api/health")
        assert response.status_code == 503
        assert response.json()["code"] == "service_unavailable"
        assert response.headers["Retry-After"]


class TestErrors:
    def test_lost_database_gives_503_without_technical_details(self, settings, frozen_clock):
        from dataclasses import replace

        broken = replace(settings, database_host="host-that-does-not-exist")
        with TestClient(create_app(broken, frozen_clock), raise_server_exceptions=False) as client:
            response = client.get(COLLECTION)
        assert_matches_contract(response, "GET", COLLECTION)
        assert response.status_code == 503
        assert "pymysql" not in response.text.lower()
        assert "sql" not in response.text.lower()

    def test_unknown_path_and_method_use_the_shared_format(self, client):
        unknown = client.get("/api/does-not-exist")
        assert unknown.status_code == 404
        assert unknown.json()["code"] == "not_found"
        wrong_method = client.patch(COLLECTION)
        assert wrong_method.status_code == 405
        assert wrong_method.json()["code"] == "method_not_allowed"

    def test_unexpected_error_hides_details(self, settings, frozen_clock, catalog):
        app = create_app(settings, frozen_clock)

        def explode(*_args, **_kwargs):
            raise RuntimeError("secret technical detail")

        app.state.booking_service.search = explode
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get(COLLECTION)
        assert response.status_code == 500
        assert response.json()["code"] == "internal_error"
        assert response.json()["requestId"]
        assert "secret" not in response.text
