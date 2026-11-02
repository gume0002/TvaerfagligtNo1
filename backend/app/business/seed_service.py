"""First-time loading of catalogs, reference records and marked demo data.

Everything happens in one transaction with the marker last, so an interrupted
run leaves nothing behind and can simply be started again.
"""

import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from app.business.catalog_data import COUNTRY_CODES, DEMO_EMPLOYEE_CODE, EMPLOYEES, HELENE_CHRISTINE_CODE, ROOM_TYPES
from app.business.models import (
    BookingInput,
    Catalogs,
    Clock,
    DrinkCategory,
    ImportReport,
    NewBarSale,
    NewBooking,
    NewCountry,
    NewDrink,
    RawData,
    RawSheetRow,
    ReferenceRecord,
    ResourceStatus,
    RoomType,
    Season,
    SeedBlocked,
    SeedMarker,
    SeedResult,
)
from app.business.ports import UnitOfWork, UnitOfWorkFactory
from app.business.rules import amount_errors, first_overbooked_night, season_for_date

SEED_VERSION = "demo-v1"
PRNG_SEED = 42
DEMO_BOOKING_COUNT = 24
DEMO_SALE_COUNT = 12

DRINK_CATEGORIES = {"Cocktail": DrinkCategory.COCKTAIL, "Coffee": DrinkCategory.COFFEE}
EXPECTED_DRINKS = {DrinkCategory.COCKTAIL: 20, DrinkCategory.COFFEE: 10}


@dataclass(frozen=True)
class _DemoStay:
    arrival: date
    departure: date
    room_type_code: str
    nightly_rate: Decimal | None = None
    guest_count: int | None = None
    cancelled: bool = False


def _validated_hotel_rows(raw: RawData) -> tuple[list[RawSheetRow], list[dict]]:
    room_type_names = {room_type.name for room_type in ROOM_TYPES}
    seasons = {season.value for season in Season}
    valid = []
    reasons = []
    for row in raw.hotel_rows:
        values = row.values
        problems = []
        if values.get("Country") not in COUNTRY_CODES:
            problems.append(f"ukendt land: {values.get('Country')}")
        if values.get("Room Type") not in room_type_names:
            problems.append(f"ukendt værelsestype: {values.get('Room Type')}")
        if values.get("Season") not in seasons:
            problems.append(f"ukendt sæson: {values.get('Season')}")
        if problems:
            reasons.append({"row": row.row_number, "reason": "; ".join(problems)})
        else:
            valid.append(row)
    return valid, reasons


def _validated_drinks(raw: RawData) -> tuple[list[NewDrink], list[RawSheetRow], list[dict]]:
    drinks = []
    rows = []
    reasons = []
    for row in raw.bar_rows:
        values = row.values
        category = DRINK_CATEGORIES.get(values.get("Category"))
        try:
            price = Decimal(str(values.get("Price (DKK)")))
        except InvalidOperation:
            price = Decimal(0)
        problems = []
        if category is None:
            problems.append(f"ukendt kategori: {values.get('Category')}")
        if amount_errors("price", price):
            problems.append(f"ugyldig pris: {values.get('Price (DKK)')}")
        if not values.get("Drink Name"):
            problems.append("manglende navn")
        if problems:
            reasons.append({"row": row.row_number, "reason": "; ".join(problems)})
            continue
        drinks.append(NewDrink(name=values["Drink Name"], category=category, suggested_unit_price=price.quantize(Decimal("0.01"))))
        rows.append(row)
    for category, expected in EXPECTED_DRINKS.items():
        actual = sum(1 for drink in drinks if drink.category is category)
        if actual != expected:
            reasons.append({"reason": f"Forventede {expected} af kategorien {category.value}, fandt {actual}."})
    return drinks, rows, reasons


def _stray_reasons(cells) -> list[dict]:
    return [
        {"cell": cell.reference, "value": cell.value, "reason": "Løs værdi uden for de kendte poster. Udeladt."}
        for cell in cells
    ]


class SeedService:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock):
        self._uow_factory = uow_factory
        self._clock = clock

    def run(self, raw: RawData) -> SeedResult:
        with self._uow_factory() as uow:
            if uow.seed.is_completed(SEED_VERSION):
                return SeedResult(version=SEED_VERSION, already_completed=True)
            if uow.seed.database_has_data():
                raise SeedBlocked(
                    "Databasen indeholder data, men ingen fuldført startdata-markør. "
                    "Intet er overskrevet. Undersøg databasen, eller nulstil den bevidst med docker compose down -v."
                )

            hotel_rows, hotel_reasons = _validated_hotel_rows(raw)
            drinks, bar_rows, bar_reasons = _validated_drinks(raw)

            uow.seed.add_countries([NewCountry(code=code, name=name) for name, code in COUNTRY_CODES.items()])
            uow.seed.add_room_types(ROOM_TYPES)
            uow.seed.add_employees(EMPLOYEES)
            uow.seed.add_drinks(drinks)
            references = [
                ReferenceRecord(source=raw.hotel_source, row_number=row.row_number, original_values=row.values)
                for row in hotel_rows
            ] + [
                ReferenceRecord(source=raw.bar_source, row_number=row.row_number, original_values=row.values)
                for row in bar_rows
            ]
            uow.seed.add_reference_records(references)

            hotel_omissions = _stray_reasons(raw.hotel_stray_cells) + hotel_reasons
            bar_omissions = _stray_reasons(raw.bar_stray_cells) + bar_reasons
            now = self._clock.now_utc()
            uow.seed.add_import_reports(
                [
                    ImportReport(raw.hotel_source, len(COUNTRY_CODES) + len(ROOM_TYPES), len(hotel_rows), len(hotel_omissions), hotel_omissions),
                    ImportReport(raw.bar_source, len(drinks), len(bar_rows), len(bar_omissions), bar_omissions),
                    ImportReport(
                        raw.hotel_csv_source,
                        0,
                        0,
                        len(raw.hotel_rows),
                        [
                            {
                                "reason": "Samme poster som Excel-filen, som er navnekilden. Ikke importeret.",
                                "replacementCharacters": raw.hotel_csv_replacement_characters,
                            }
                        ],
                    ),
                ],
                now,
            )

            anchor = self._clock.business_date()
            catalogs = uow.catalogs.get_all()
            rng = random.Random(PRNG_SEED)
            bookings = self._add_demo_bookings(uow, catalogs, hotel_rows, anchor, rng, now)
            sales = self._add_demo_sales(uow, catalogs, anchor, rng, now)

            uow.seed.add_marker(
                SeedMarker(
                    version=SEED_VERSION,
                    source_checksums=raw.checksums,
                    anchor_date=anchor,
                    anchor_year=anchor.year,
                    completed_at=now,
                )
            )
            uow.commit()
            return SeedResult(
                version=SEED_VERSION,
                already_completed=False,
                bookings=bookings,
                bar_sales=sales,
                reference_records=len(references),
            )

    @staticmethod
    def _demo_stays(anchor: date, room_types: list[RoomType], rng: random.Random) -> list[_DemoStay]:
        year = anchor.year
        stays = [
            # US7.1: three nights across New Year at 1000.00.
            _DemoStay(date(year - 1, 12, 30), date(year, 1, 2), "standard-double", Decimal("1000.00"), 2),
            # US7.5: two nights across the change from low to mid season.
            _DemoStay(date(year, 2, 28), date(year, 3, 2), "standard-double", Decimal("1000.00"), 2),
            _DemoStay(date(year, 5, 10), date(year, 5, 13), "suite", cancelled=True),
            _DemoStay(anchor + timedelta(days=20), anchor + timedelta(days=22), "grand-lit", cancelled=True),
            _DemoStay(anchor + timedelta(days=10), anchor + timedelta(days=13), "junior-suite"),
            _DemoStay(anchor + timedelta(days=30), anchor + timedelta(days=34), "loft-suite"),
        ]
        days_in_year = (date(year + 1, 1, 1) - date(year, 1, 1)).days
        for index in range(DEMO_BOOKING_COUNT - len(stays)):
            arrival = date(year, 1, 1) + timedelta(days=rng.randrange(days_in_year))
            stays.append(
                _DemoStay(arrival, arrival + timedelta(days=rng.randint(1, 5)), room_types[index % len(room_types)].code)
            )
        return stays

    def _add_demo_bookings(
        self,
        uow: UnitOfWork,
        catalogs: Catalogs,
        hotel_rows: list[RawSheetRow],
        anchor: date,
        rng: random.Random,
        now,
    ) -> int:
        room_types = {room_type.code: room_type for room_type in catalogs.room_types}
        active_stays: dict[str, list[tuple[date, date]]] = defaultdict(list)
        added = 0
        for stay in self._demo_stays(anchor, catalogs.room_types, rng):
            room_type = room_types[stay.room_type_code]
            guest_row = rng.choice(hotel_rows)
            country = rng.choice(catalogs.countries)
            guest_count = stay.guest_count or rng.randint(1, room_type.max_guests)
            rate = stay.nightly_rate or room_type.suggested_nightly_rates[season_for_date(stay.arrival)]
            if not stay.cancelled:
                # Demo data follows the same capacity rule as real bookings.
                if first_overbooked_night(stay.arrival, stay.departure, active_stays[room_type.code], room_type.room_count):
                    continue
                active_stays[room_type.code].append((stay.arrival, stay.departure))
            uow.bookings.add(
                NewBooking(
                    data=BookingInput(
                        guest_name=f"{guest_row.values['First Name']} {guest_row.values['Family Name']}",
                        country_id=country.id,
                        room_type_id=room_type.id,
                        arrival=stay.arrival,
                        departure=stay.departure,
                        guest_count=guest_count,
                        nightly_rate=rate,
                    ),
                    status=ResourceStatus.CANCELLED if stay.cancelled else ResourceStatus.ACTIVE,
                    demo_data=True,
                    created_at=now,
                    cancelled_at=now if stay.cancelled else None,
                )
            )
            added += 1
        return added

    @staticmethod
    def _add_demo_sales(uow: UnitOfWork, catalogs: Catalogs, anchor: date, rng: random.Random, now) -> int:
        employees = {employee.code: employee for employee in catalogs.employees}
        helene = employees[HELENE_CHRISTINE_CODE]
        demo_employee = employees[DEMO_EMPLOYEE_CODE]
        cocktails = [drink for drink in catalogs.drinks if drink.category is DrinkCategory.COCKTAIL]
        coffees = [drink for drink in catalogs.drinks if drink.category is DrinkCategory.COFFEE]

        def sale(drink, employee, quantity, unit_price, sale_date, cancelled=False):
            return NewBarSale(
                drink_id=drink.id,
                employee_id=employee.id,
                quantity=quantity,
                unit_price=unit_price,
                sale_date=sale_date,
                status=ResourceStatus.CANCELLED if cancelled else ResourceStatus.ACTIVE,
                demo_data=True,
                created_at=now,
                cancelled_at=now if cancelled else None,
            )

        # US9.1: three cocktails at 100.00 and two coffees at 50.00.
        sales = [
            sale(cocktails[0], helene, 3, Decimal("100.00"), anchor),
            sale(coffees[0], helene, 2, Decimal("50.00"), anchor),
            sale(cocktails[1], helene, 1, cocktails[1].suggested_unit_price, anchor, cancelled=True),
        ]
        days_this_year = anchor.timetuple().tm_yday
        drinks = cocktails + coffees
        for index in range(DEMO_SALE_COUNT - len(sales)):
            drink = rng.choice(drinks)
            employee = demo_employee if index % 4 == 3 else helene
            sale_date = anchor - timedelta(days=rng.randrange(days_this_year))
            sales.append(sale(drink, employee, rng.randint(1, 4), drink.suggested_unit_price, sale_date))
        uow.seed.add_bar_sales(sales)
        return len(sales)
