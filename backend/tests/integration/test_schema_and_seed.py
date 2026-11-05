"""T011, T056 and T057: schema, first-time data and repeated starts."""

import os
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import func, inspect, select, text
from sqlalchemy.orm import Session

from app.business.catalog_data import ROOM_TYPES
from app.business.models import SeedBlocked
from app.business.seed_service import DEMO_BOOKING_COUNT, DEMO_SALE_COUNT, SEED_VERSION, SeedService
from app.data_access.orm_models import (
    BarSaleRow,
    Base,
    BookingRow,
    CountryRow,
    DrinkRow,
    EmployeeRow,
    HistoricalReferenceRecordRow,
    ImportReportRow,
    RoomTypeRow,
    SeedRunRow,
)
from app.data_access.raw_files import read_raw_data
from conftest import FrozenClock


@pytest.fixture(scope="module")
def raw():
    return read_raw_data(Path(os.environ["RAW_DATA_DIR"]))


@pytest.fixture()
def seed(uow_factory, raw, empty_database):
    def run(today=date(2026, 10, 29)):
        return SeedService(uow_factory, FrozenClock(today)).run(raw)

    return run


def count(engine, row_type, *conditions) -> int:
    with Session(engine) as session:
        return session.scalar(select(func.count()).select_from(row_type).where(*conditions))


def rows(engine, row_type, *conditions):
    with Session(engine) as session:
        return list(session.scalars(select(row_type).where(*conditions).order_by(row_type.id)))


class TestSchema:
    def test_migration_matches_the_orm_models(self, engine):
        with engine.connect() as connection:
            differences = compare_metadata(MigrationContext.configure(connection), Base.metadata)
        assert differences == []

    def test_database_is_postgresql_with_utf8(self, engine):
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version()")).startswith("PostgreSQL 17")
            assert connection.scalar(text("SHOW server_encoding")) == "UTF8"

    def test_planned_constraints_exist(self, engine):
        checks = {item["name"] for item in inspect(engine).get_check_constraints("bookings")}
        assert {"ck_bookings_dates", "ck_bookings_guest_count", "ck_bookings_nightly_rate", "ck_bookings_status"} <= checks
        foreign_keys = {item["referred_table"] for item in inspect(engine).get_foreign_keys("bookings")}
        assert foreign_keys == {"countries", "room_types"}

    def test_database_rejects_values_that_bypass_the_logic(self, catalog, engine):
        from sqlalchemy.exc import DBAPIError

        with pytest.raises(DBAPIError, match="ck_bookings_dates"), engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO bookings (guest_name, country_id, room_type_id, arrival, departure, guest_count, "
                    "nightly_rate, status, demo_data, created_at, updated_at) VALUES "
                    "('x', :country, :room, '2026-01-02', '2026-01-01', 1, 1, 'active', false, NOW(), NOW())"
                ),
                {"country": catalog.sweden, "room": catalog.tiny},
            )


class TestRawFiles:
    def test_hotel_file_has_1000_records_and_one_loose_cell(self, raw):
        assert len(raw.hotel_rows) == 1000
        assert [(cell.reference, cell.value) for cell in raw.hotel_stray_cells] == [("E1002", 5379)]
        assert raw.hotel_rows[0].row_number == 2
        assert raw.hotel_rows[0].values["First Name"] == "Liam"

    def test_bar_file_has_30_drinks_and_nothing_loose(self, raw):
        assert len(raw.bar_rows) == 30
        assert raw.bar_stray_cells == []

    def test_replacement_characters_are_found_in_the_csv(self, raw):
        assert raw.hotel_csv_replacement_characters == 54

    def test_checksums_cover_all_three_files(self, raw):
        assert len(raw.checksums) == 3


class TestFirstTimeData:
    def test_catalogs_are_loaded(self, seed, engine):
        seed()
        assert count(engine, CountryRow) == 21
        assert count(engine, CountryRow, CountryRow.code == "DK") == 1
        room_types = rows(engine, RoomTypeRow)
        assert len(room_types) == 8
        assert sum(row.room_count for row in room_types) == 214
        assert {row.code for row in room_types} == {item.code for item in ROOM_TYPES}
        assert all(row.demo_data for row in room_types)
        assert {row.name for row in rows(engine, EmployeeRow)} == {"Helene Christine", "Demomedarbejder"}

    def test_drinks_are_20_cocktails_and_10_coffees_with_exact_prices(self, seed, engine):
        seed()
        assert count(engine, DrinkRow, DrinkRow.category == "cocktail") == 20
        assert count(engine, DrinkRow, DrinkRow.category == "coffee") == 10
        margarita = rows(engine, DrinkRow, DrinkRow.name == "Margarita")[0]
        assert margarita.suggested_unit_price == Decimal("72.47")

    def test_reference_records_are_kept_apart_from_real_bookings(self, seed, engine):
        result = seed()
        assert result.reference_records == 1030
        assert count(engine, HistoricalReferenceRecordRow) == 1030
        assert count(engine, BookingRow) == DEMO_BOOKING_COUNT
        assert count(engine, BookingRow, BookingRow.demo_data.is_(False)) == 0

    def test_original_values_are_stored_unchanged(self, seed, engine):
        seed()
        record = rows(
            engine,
            HistoricalReferenceRecordRow,
            HistoricalReferenceRecordRow.source == "international_names_with_rooms_1000.xlsx",
            HistoricalReferenceRecordRow.row_number == 2,
        )[0]
        assert record.original_values == {
            "First Name": "Liam",
            "Family Name": "Nguyen",
            "Country": "China",
            "Room Type": "Spa Executive",
            "Days Rented": 1,
            "Season": "mid",
            "Price": 2577,
        }

    def test_import_report_explains_what_was_left_out(self, seed, engine):
        seed()
        reports = {row.source: row for row in rows(engine, ImportReportRow)}
        hotel = reports["international_names_with_rooms_1000.xlsx"]
        assert hotel.reference_count == 1000
        assert hotel.omitted_count == 1
        assert hotel.reasons[0]["cell"] == "E1002"
        bar = reports["drinks_menu_with_sales.xlsx"]
        assert (bar.catalog_count, bar.reference_count, bar.omitted_count) == (30, 30, 0)
        csv = reports["international_names_with_rooms_1000.csv"]
        assert csv.reference_count == 0
        assert csv.reasons[0]["replacementCharacters"] == 54

    def test_marker_stores_date_year_and_checksums(self, seed, engine, raw):
        seed()
        marker = rows(engine, SeedRunRow)[0]
        assert marker.version == SEED_VERSION
        assert marker.anchor_date == date(2026, 10, 29)
        assert marker.anchor_year == 2026
        assert marker.source_checksums == raw.checksums


def demo_snapshot(engine):
    bookings = [
        (row.guest_name, row.country_id, row.room_type_id, row.arrival, row.departure, row.guest_count, row.nightly_rate, row.status)
        for row in rows(engine, BookingRow)
    ]
    sales = [
        (row.drink_id, row.employee_id, row.quantity, row.unit_price, row.sale_date, row.status)
        for row in rows(engine, BarSaleRow)
    ]
    return bookings, sales


class TestDemoData:
    TODAY = date(2026, 10, 29)

    def test_counts_and_marking(self, seed, engine):
        result = seed(self.TODAY)
        assert (result.bookings, result.bar_sales) == (DEMO_BOOKING_COUNT, DEMO_SALE_COUNT)
        assert count(engine, BookingRow, BookingRow.demo_data.is_(True)) == 24
        assert count(engine, BarSaleRow, BarSaleRow.demo_data.is_(True)) == 12

    def test_is_reproducible(self, seed, engine):
        seed(self.TODAY)
        first = demo_snapshot(engine)
        with engine.begin() as connection:
            tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
            connection.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))
        seed(self.TODAY)
        assert demo_snapshot(engine) == first

    def test_contains_the_planned_controlled_examples(self, seed, engine):
        seed(self.TODAY)
        bookings = rows(engine, BookingRow)
        assert any(row.arrival == date(2025, 12, 30) and row.departure == date(2026, 1, 2) for row in bookings)
        assert any(row.arrival == date(2026, 2, 28) and row.departure == date(2026, 3, 2) for row in bookings)
        assert sum(row.status == "cancelled" for row in bookings) == 2
        assert all(row.cancelled_at for row in bookings if row.status == "cancelled")
        assert any(row.arrival > self.TODAY and row.status == "active" for row in bookings)

    def test_follows_the_booking_rules(self, seed, engine):
        seed(self.TODAY)
        room_types = {row.id: row for row in rows(engine, RoomTypeRow)}
        active_by_type = {}
        for row in rows(engine, BookingRow):
            assert row.departure > row.arrival
            assert 1 <= row.guest_count <= room_types[row.room_type_id].max_guests
            assert row.nightly_rate > 0
            if row.status == "active":
                active_by_type.setdefault(row.room_type_id, []).append(row)
        assert len(active_by_type) > 1
        for room_type_id, bookings in active_by_type.items():
            nights = {}
            for row in bookings:
                current = row.arrival
                while current < row.departure:
                    nights[current] = nights.get(current, 0) + 1
                    current = date.fromordinal(current.toordinal() + 1)
            assert max(nights.values()) <= room_types[room_type_id].room_count

    def test_sales_contain_the_us9_mix_and_are_never_in_the_future(self, seed, engine):
        seed(self.TODAY)
        sales = rows(engine, BarSaleRow)
        assert all(row.sale_date <= self.TODAY for row in sales)
        assert all(row.sale_date.year == self.TODAY.year for row in sales)
        assert any(row.quantity == 3 and row.unit_price == Decimal("100.00") for row in sales)
        assert any(row.quantity == 2 and row.unit_price == Decimal("50.00") for row in sales)
        assert any(row.status == "cancelled" for row in sales)
        assert len({row.employee_id for row in sales}) == 2

    @pytest.mark.parametrize("today", [date(2026, 1, 1), date(2028, 2, 29), date(2026, 12, 31)])
    def test_works_on_edge_dates(self, seed, engine, today):
        result = seed(today)
        assert result.bookings == DEMO_BOOKING_COUNT
        sales = rows(engine, BarSaleRow)
        assert all(row.sale_date <= today for row in sales)


class TestRepeatedStart:
    def test_second_run_changes_nothing(self, seed, engine):
        seed()
        first = demo_snapshot(engine)
        result = seed()
        assert result.already_completed is True
        assert demo_snapshot(engine) == first
        assert count(engine, HistoricalReferenceRecordRow) == 1030
        assert count(engine, SeedRunRow) == 1

    def test_later_changes_survive_a_new_run(self, seed, engine, session_factory):
        seed()
        with session_factory() as session:
            booking = session.scalars(select(BookingRow).where(BookingRow.status == "active")).first()
            booking.guest_name = "Rettet af receptionisten"
            booking_id = booking.id
            session.commit()
        seed()
        assert rows(engine, BookingRow, BookingRow.id == booking_id)[0].guest_name == "Rettet af receptionisten"

    def test_interrupted_run_leaves_nothing_and_can_be_repeated(self, uow_factory, raw, empty_database):
        class StopAtMarker:
            """Works like the real unit of work, but fails just before the marker."""

            def __init__(self):
                self._inner = uow_factory()

            def __enter__(self):
                uow = self._inner.__enter__()

                def fail(_marker):
                    raise RuntimeError("Afbrudt under indlæsning")

                uow.seed.add_marker = fail
                return uow

            def __exit__(self, *args):
                return self._inner.__exit__(*args)

        with pytest.raises(RuntimeError):
            SeedService(StopAtMarker, FrozenClock()).run(raw)
        for row_type in (CountryRow, RoomTypeRow, BookingRow, BarSaleRow, HistoricalReferenceRecordRow, ImportReportRow, SeedRunRow):
            assert count(empty_database, row_type) == 0

        result = SeedService(uow_factory, FrozenClock()).run(raw)
        assert result.bookings == DEMO_BOOKING_COUNT
        assert count(empty_database, HistoricalReferenceRecordRow) == 1030

    def test_data_without_marker_stops_the_seed_without_overwriting(self, seed, engine):
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO countries (code, name) VALUES ('SE', 'Sweden')"))
        with pytest.raises(SeedBlocked):
            seed()
        assert [row.code for row in rows(engine, CountryRow)] == ["SE"]
