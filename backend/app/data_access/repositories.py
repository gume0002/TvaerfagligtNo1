"""Reads and writes MySQL and returns plain domain objects."""

from datetime import date, datetime

from sqlalchemy import exists, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.business.models import (
    Sale,
    Booking,
    BookingInput,
    BookingSearch,
    Catalogs,
    Country,
    Drink,
    DrinkCategory,
    DuplicateIdempotencyKey,
    Employee,
    IdempotencyContext,
    ImportReport,
    NewBarSale,
    NewBooking,
    NewCountry,
    NewDrink,
    NewEmployee,
    NewRoomType,
    ReferenceRecord,
    ResourceStatus,
    RoomType,
    Season,
    SeedMarker,
    StatusFilter,
    StoredIdempotentResult,
)
from app.data_access.orm_models import (
    BarSaleRow,
    BookingRow,
    CountryRow,
    DrinkRow,
    EmployeeRow,
    HistoricalReferenceRecordRow,
    IdempotencyRequestRow,
    ImportReportRow,
    RoomTypePriceRow,
    RoomTypeRow,
    SeedRunRow,
)


def _country(row: CountryRow) -> Country:
    return Country(id=row.id, code=row.code, name=row.name)


def _room_type(row: RoomTypeRow) -> RoomType:
    return RoomType(
        id=row.id,
        code=row.code,
        name=row.name,
        room_count=row.room_count,
        max_guests=row.max_guests,
        demo_data=row.demo_data,
        suggested_nightly_rates={Season(price.season): price.suggested_nightly_rate for price in row.prices},
    )


def _booking(row: BookingRow) -> Booking:
    return Booking(
        id=row.id,
        guest_name=row.guest_name,
        country_id=row.country_id,
        country_name=row.country.name,
        room_type_id=row.room_type_id,
        room_type_name=row.room_type.name,
        arrival=row.arrival,
        departure=row.departure,
        guest_count=row.guest_count,
        nightly_rate=row.nightly_rate,
        status=ResourceStatus(row.status),
        demo_data=row.demo_data,
        created_at=row.created_at,
        updated_at=row.updated_at,
        cancelled_at=row.cancelled_at,
    )


class SqlCatalogRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_all(self) -> Catalogs:
        return Catalogs(
            countries=[_country(row) for row in self._session.scalars(select(CountryRow).order_by(CountryRow.id))],
            room_types=[_room_type(row) for row in self._session.scalars(select(RoomTypeRow).order_by(RoomTypeRow.id))],
            employees=[
                Employee(id=row.id, code=row.code, name=row.name)
                for row in self._session.scalars(select(EmployeeRow).order_by(EmployeeRow.id))
            ],
            drinks=[
                Drink(
                    id=row.id,
                    name=row.name,
                    category=DrinkCategory(row.category),
                    suggested_unit_price=row.suggested_unit_price,
                )
                for row in self._session.scalars(select(DrinkRow).order_by(DrinkRow.id))
            ],
        )

    def get_country(self, country_id: int) -> Country | None:
        row = self._session.get(CountryRow, country_id)
        return _country(row) if row else None

    def lock_room_type(self, room_type_id: int) -> RoomType | None:
        # The lock serializes all booking changes for this room type, also when
        # the type has no bookings yet.
        row = self._session.scalars(
            select(RoomTypeRow).where(RoomTypeRow.id == room_type_id).with_for_update().execution_options(populate_existing=True)
        ).first()
        return _room_type(row) if row else None


class SqlBookingRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(self, booking: NewBooking) -> Booking:
        data = booking.data
        row = BookingRow(
            guest_name=data.guest_name,
            country_id=data.country_id,
            room_type_id=data.room_type_id,
            arrival=data.arrival,
            departure=data.departure,
            guest_count=data.guest_count,
            nightly_rate=data.nightly_rate,
            status=booking.status.value,
            demo_data=booking.demo_data,
            created_at=booking.created_at,
            updated_at=booking.created_at,
            cancelled_at=booking.cancelled_at,
        )
        self._session.add(row)
        self._session.flush()
        self._session.refresh(row)
        return _booking(row)

    def get(self, booking_id: int) -> Booking | None:
        row = self._session.get(BookingRow, booking_id)
        return _booking(row) if row else None

    def lock(self, booking_id: int) -> Booking | None:
        # of=BookingRow keeps the lock on the booking only, not the joined tables.
        row = self._session.scalars(
            select(BookingRow)
            .where(BookingRow.id == booking_id)
            .with_for_update(of=BookingRow)
            .execution_options(populate_existing=True)
        ).first()
        return _booking(row) if row else None

    def search(self, search: BookingSearch) -> tuple[list[Booking], int]:
        conditions = []
        if search.name:
            conditions.append(BookingRow.guest_name.contains(search.name, autoescape=True))
        if search.arrival_from is not None and search.departure_to is not None:
            conditions.append(BookingRow.arrival < search.departure_to)
            conditions.append(BookingRow.departure > search.arrival_from)
        if search.status is not StatusFilter.ALL:
            conditions.append(BookingRow.status == search.status.value)

        total = self._session.scalar(select(func.count()).select_from(BookingRow).where(*conditions))
        if search.offset >= total:
            return [], total
        rows = self._session.scalars(
            select(BookingRow).where(*conditions).order_by(BookingRow.id).offset(search.offset).limit(search.limit)
        )
        return [_booking(row) for row in rows], total

    def for_year(self, year: int) -> list[Booking]:
        rows = self._session.scalars(select(BookingRow).where(
            BookingRow.arrival < date(year + 1, 1, 1), BookingRow.departure > date(year, 1, 1)
        ).order_by(BookingRow.id))
        return [_booking(row) for row in rows]

    def active_stays_overlapping(
        self, room_type_id: int, arrival: date, departure: date, exclude_booking_id: int | None
    ) -> list[tuple[date, date]]:
        query = select(BookingRow.arrival, BookingRow.departure).where(
            BookingRow.room_type_id == room_type_id,
            BookingRow.status == ResourceStatus.ACTIVE.value,
            BookingRow.arrival < departure,
            BookingRow.departure > arrival,
        )
        if exclude_booking_id is not None:
            query = query.where(BookingRow.id != exclude_booking_id)
        return [(row.arrival, row.departure) for row in self._session.execute(query)]

    def update(self, booking_id: int, data: BookingInput, updated_at: datetime) -> Booking:
        row = self._session.get_one(BookingRow, booking_id)
        row.guest_name = data.guest_name
        row.country_id = data.country_id
        row.room_type_id = data.room_type_id
        row.arrival = data.arrival
        row.departure = data.departure
        row.guest_count = data.guest_count
        row.nightly_rate = data.nightly_rate
        row.updated_at = updated_at
        self._session.flush()
        self._session.refresh(row)
        return _booking(row)

    def cancel(self, booking_id: int, cancelled_at: datetime) -> None:
        row = self._session.get_one(BookingRow, booking_id)
        row.status = ResourceStatus.CANCELLED.value
        row.cancelled_at = cancelled_at
        row.updated_at = cancelled_at
        self._session.flush()


class SqlIdempotencyRepository:
    def __init__(self, session: Session):
        self._session = session

    def find(self, context: IdempotencyContext) -> StoredIdempotentResult | None:
        row = self._session.scalars(
            select(IdempotencyRequestRow)
            .where(
                IdempotencyRequestRow.http_method == context.http_method,
                IdempotencyRequestRow.path == context.path,
                IdempotencyRequestRow.idempotency_key == context.key,
            )
            .execution_options(populate_existing=True)
        ).first()
        if row is None:
            return None
        return StoredIdempotentResult(
            payload_hash=row.payload_hash,
            response_status=row.response_status,
            response_body=row.response_body,
        )

    def save(self, context: IdempotencyContext, result: StoredIdempotentResult, created_at: datetime) -> None:
        self._session.add(
            IdempotencyRequestRow(
                http_method=context.http_method,
                path=context.path,
                idempotency_key=context.key,
                payload_hash=result.payload_hash,
                response_status=result.response_status,
                response_body=result.response_body,
                created_at=created_at,
            )
        )
        try:
            self._session.flush()
        except IntegrityError as error:
            raise DuplicateIdempotencyKey() from error


class SqlSeedRepository:
    def __init__(self, session: Session):
        self._session = session

    def is_completed(self, version: str) -> bool:
        return bool(self._session.scalar(select(exists().where(SeedRunRow.version == version))))

    def any_completed(self) -> bool:
        return bool(self._session.scalar(select(exists().where(SeedRunRow.id.is_not(None)))))

    def database_has_data(self) -> bool:
        for row_type in (CountryRow, RoomTypeRow, EmployeeRow, DrinkRow, BookingRow, BarSaleRow, HistoricalReferenceRecordRow):
            if self._session.scalar(select(exists().where(row_type.id.is_not(None)))):
                return True
        return False

    def add_countries(self, countries: list[NewCountry]) -> None:
        self._session.add_all(CountryRow(code=item.code, name=item.name) for item in countries)
        self._session.flush()

    def add_room_types(self, room_types: list[NewRoomType]) -> None:
        for item in room_types:
            self._session.add(
                RoomTypeRow(
                    code=item.code,
                    name=item.name,
                    room_count=item.room_count,
                    max_guests=item.max_guests,
                    demo_data=True,
                    prices=[
                        RoomTypePriceRow(season=season.value, suggested_nightly_rate=rate)
                        for season, rate in item.suggested_nightly_rates.items()
                    ],
                )
            )
        self._session.flush()

    def add_employees(self, employees: list[NewEmployee]) -> None:
        self._session.add_all(EmployeeRow(code=item.code, name=item.name) for item in employees)
        self._session.flush()

    def add_drinks(self, drinks: list[NewDrink]) -> None:
        self._session.add_all(
            DrinkRow(name=item.name, category=item.category.value, suggested_unit_price=item.suggested_unit_price)
            for item in drinks
        )
        self._session.flush()

    def add_bar_sales(self, sales: list[NewBarSale]) -> None:
        self._session.add_all(
            BarSaleRow(
                drink_id=item.drink_id,
                employee_id=item.employee_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                sale_date=item.sale_date,
                status=item.status.value,
                demo_data=item.demo_data,
                created_at=item.created_at,
                updated_at=item.created_at,
                cancelled_at=item.cancelled_at,
            )
            for item in sales
        )
        self._session.flush()

    def add_reference_records(self, records: list[ReferenceRecord]) -> None:
        self._session.add_all(
            HistoricalReferenceRecordRow(source=item.source, row_number=item.row_number, original_values=item.original_values)
            for item in records
        )
        self._session.flush()

    def add_import_reports(self, reports: list[ImportReport], created_at: datetime) -> None:
        self._session.add_all(
            ImportReportRow(
                source=item.source,
                catalog_count=item.catalog_count,
                reference_count=item.reference_count,
                omitted_count=item.omitted_count,
                reasons=item.reasons,
                created_at=created_at,
            )
            for item in reports
        )
        self._session.flush()

    def add_marker(self, marker: SeedMarker) -> None:
        self._session.add(
            SeedRunRow(
                version=marker.version,
                source_checksums=marker.source_checksums,
                anchor_date=marker.anchor_date,
                anchor_year=marker.anchor_year,
                completed_at=marker.completed_at,
            )
        )
        self._session.flush()


class SqlHealthRepository:
    def __init__(self, session: Session):
        self._session = session

    def ping(self) -> None:
        self._session.execute(text("SELECT 1"))


class SqlSaleRepository:
    def __init__(self, session: Session):
        self._session = session

    def _sale(self, row: BarSaleRow) -> Sale:
        drink = self._session.get_one(DrinkRow, row.drink_id)
        employee = self._session.get_one(EmployeeRow, row.employee_id)
        return Sale(
            id=row.id, drink_id=row.drink_id, drink_name=drink.name,
            category=DrinkCategory(drink.category), employee_id=row.employee_id,
            employee_name=employee.name, quantity=row.quantity, unit_price=row.unit_price,
            sale_date=row.sale_date, status=ResourceStatus(row.status), demo_data=row.demo_data,
            created_at=row.created_at, updated_at=row.updated_at, cancelled_at=row.cancelled_at,
        )

    def add(self, sale: NewBarSale) -> Sale:
        row = BarSaleRow(
            drink_id=sale.drink_id, employee_id=sale.employee_id, quantity=sale.quantity,
            unit_price=sale.unit_price, sale_date=sale.sale_date, status=sale.status.value,
            demo_data=sale.demo_data, created_at=sale.created_at, updated_at=sale.created_at,
            cancelled_at=sale.cancelled_at,
        )
        self._session.add(row)
        self._session.flush()
        return self._sale(row)

    def get(self, sale_id: int) -> Sale | None:
        row = self._session.get(BarSaleRow, sale_id)
        return self._sale(row) if row else None

    def lock(self, sale_id: int) -> Sale | None:
        row = self._session.scalars(select(BarSaleRow).where(BarSaleRow.id == sale_id)
            .with_for_update().execution_options(populate_existing=True)).first()
        return self._sale(row) if row else None

    def update(self, sale_id: int, data, updated_at: datetime) -> Sale:
        row = self._session.get_one(BarSaleRow, sale_id)
        row.drink_id = data.drink_id
        row.employee_id = data.employee_id
        row.quantity = data.quantity
        row.unit_price = data.unit_price
        row.sale_date = data.sale_date
        row.updated_at = updated_at
        self._session.flush()
        return self._sale(row)

    def cancel(self, sale_id: int, cancelled_at: datetime) -> None:
        row = self._session.get_one(BarSaleRow, sale_id)
        row.status = ResourceStatus.CANCELLED.value
        row.cancelled_at = cancelled_at
        row.updated_at = cancelled_at
        self._session.flush()

    def search(self, search):
        conditions = []
        if search.sale_date_from:
            conditions.append(BarSaleRow.sale_date >= search.sale_date_from)
        if search.sale_date_to:
            conditions.append(BarSaleRow.sale_date <= search.sale_date_to)
        if search.employee_id is not None:
            conditions.append(BarSaleRow.employee_id == search.employee_id)
        if search.status is not StatusFilter.ALL:
            conditions.append(BarSaleRow.status == search.status.value)
        total = self._session.scalar(select(func.count()).select_from(BarSaleRow).where(*conditions))
        rows = self._session.scalars(select(BarSaleRow).where(*conditions).order_by(BarSaleRow.id)
            .offset(search.offset).limit(search.limit))
        return [self._sale(row) for row in rows], total

    def for_year(self, year: int) -> list[Sale]:
        rows = self._session.scalars(select(BarSaleRow).where(
            BarSaleRow.sale_date >= date(year, 1, 1), BarSaleRow.sale_date < date(year + 1, 1, 1)
        ).order_by(BarSaleRow.id))
        return [self._sale(row) for row in rows]
