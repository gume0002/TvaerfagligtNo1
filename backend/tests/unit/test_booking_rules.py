"""Booking rules that can be checked without a database."""

from datetime import date
from decimal import Decimal

import pytest

from app.business.booking_service import BookingService
from app.business.catalog_data import COUNTRY_CODES, ROOM_TYPES
from app.business.models import BookingInput, BookingSearch, Clock, IdempotencyContext, Season, ValidationFailed
from app.business.rules import amount_errors, first_overbooked_night, season_for_date

D = date


def must_not_use_database():
    raise AssertionError("Invalid input must be rejected before the database is used.")


SERVICE = BookingService(must_not_use_database, Clock())
CONTEXT = IdempotencyContext("POST", "/api/bookings", "key")


def booking_input(**changes) -> BookingInput:
    values = dict(
        guest_name="Anna Berg",
        country_id=1,
        room_type_id=1,
        arrival=D(2026, 6, 10),
        departure=D(2026, 6, 12),
        guest_count=2,
        nightly_rate=Decimal("1000.00"),
    )
    return BookingInput(**(values | changes))


def field_errors(error) -> set[str]:
    return {item.field for item in error.value.field_errors}


class TestCapacity:
    def test_free_room_gives_no_conflict(self):
        assert first_overbooked_night(D(2026, 6, 10), D(2026, 6, 12), [], 1) is None

    def test_arrival_on_another_guests_departure_day_is_allowed(self):
        assert first_overbooked_night(D(2026, 6, 12), D(2026, 6, 14), [(D(2026, 6, 10), D(2026, 6, 12))], 1) is None

    def test_departure_on_another_guests_arrival_day_is_allowed(self):
        assert first_overbooked_night(D(2026, 6, 8), D(2026, 6, 10), [(D(2026, 6, 10), D(2026, 6, 12))], 1) is None

    def test_one_full_night_rejects_the_whole_stay(self):
        stays = [(D(2026, 6, 13), D(2026, 6, 14))]
        assert first_overbooked_night(D(2026, 6, 10), D(2026, 6, 20), stays, 1) == D(2026, 6, 13)

    def test_overlapping_stays_on_different_nights_can_share_capacity(self):
        stays = [(D(2026, 6, 10), D(2026, 6, 11)), (D(2026, 6, 11), D(2026, 6, 12))]
        assert first_overbooked_night(D(2026, 6, 10), D(2026, 6, 12), stays, 2) is None

    def test_two_rooms_are_full_only_when_both_are_taken_the_same_night(self):
        stays = [(D(2026, 6, 10), D(2026, 6, 12)), (D(2026, 6, 11), D(2026, 6, 13))]
        assert first_overbooked_night(D(2026, 6, 10), D(2026, 6, 13), stays, 2) == D(2026, 6, 11)

    def test_room_type_without_rooms_is_always_full(self):
        assert first_overbooked_night(D(2026, 6, 10), D(2026, 6, 11), [], 0) == D(2026, 6, 10)


class TestSeason:
    @pytest.mark.parametrize(
        ("night", "season"),
        [
            (D(2026, 1, 1), Season.LOW),
            (D(2026, 2, 28), Season.LOW),
            (D(2028, 2, 29), Season.LOW),
            (D(2026, 3, 1), Season.MID),
            (D(2026, 5, 31), Season.MID),
            (D(2026, 6, 1), Season.HIGH),
            (D(2026, 8, 31), Season.HIGH),
            (D(2026, 9, 1), Season.MID),
            (D(2026, 11, 30), Season.MID),
            (D(2026, 12, 1), Season.HIGH),
        ],
    )
    def test_each_date_has_the_specified_season(self, night, season):
        assert season_for_date(night) is season


class TestAmount:
    @pytest.mark.parametrize("amount", ["0.01", "1000", "1000.5", "9999999999.99"])
    def test_valid_amounts(self, amount):
        assert amount_errors("price", Decimal(amount)) == []

    @pytest.mark.parametrize("amount", ["0", "0.00", "-1", "1.234", "10000000000.00", "NaN", "Infinity"])
    def test_invalid_amounts(self, amount):
        assert amount_errors("price", Decimal(amount))


class TestValidationBeforeDatabase:
    @pytest.mark.parametrize(
        ("changes", "field"),
        [
            ({"guest_name": "   "}, "guestName"),
            ({"guest_name": "x" * 201}, "guestName"),
            ({"departure": D(2026, 6, 10)}, "departure"),
            ({"departure": D(2026, 6, 9)}, "departure"),
            ({"guest_count": 0}, "guestCount"),
            ({"guest_count": -1}, "guestCount"),
            ({"nightly_rate": Decimal("0")}, "nightlyRate"),
            ({"nightly_rate": Decimal("10.123")}, "nightlyRate"),
        ],
    )
    def test_create_and_update_reject_invalid_fields(self, changes, field):
        with pytest.raises(ValidationFailed) as create_error:
            SERVICE.create(booking_input(**changes), CONTEXT)
        assert field in field_errors(create_error)
        with pytest.raises(ValidationFailed) as update_error:
            SERVICE.update(1, booking_input(**changes))
        assert field in field_errors(update_error)

    def test_several_errors_are_returned_together(self):
        with pytest.raises(ValidationFailed) as error:
            SERVICE.create(booking_input(guest_name="", guest_count=0), CONTEXT)
        assert field_errors(error) == {"guestName", "guestCount"}

    @pytest.mark.parametrize(
        "search",
        [
            BookingSearch(arrival_from=D(2026, 6, 10)),
            BookingSearch(departure_to=D(2026, 6, 12)),
            BookingSearch(arrival_from=D(2026, 6, 12), departure_to=D(2026, 6, 12)),
        ],
    )
    def test_search_rejects_incomplete_or_empty_date_interval(self, search):
        with pytest.raises(ValidationFailed):
            SERVICE.search(search)


class TestCatalogData:
    def test_room_types_sum_to_214_rooms_in_8_types(self):
        assert len(ROOM_TYPES) == 8
        assert sum(room_type.room_count for room_type in ROOM_TYPES) == 214

    def test_guest_limits_and_prices_follow_the_plan(self):
        assert all(1 <= room_type.max_guests <= 4 for room_type in ROOM_TYPES)
        assert all(set(room_type.suggested_nightly_rates) == set(Season) for room_type in ROOM_TYPES)

    def test_countries_have_unique_iso_codes(self):
        assert len(COUNTRY_CODES) == 21
        assert len(set(COUNTRY_CODES.values())) == 21
        assert COUNTRY_CODES["Denmark"] == "DK"
