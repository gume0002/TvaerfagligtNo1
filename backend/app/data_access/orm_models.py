"""SQLAlchemy mapping of the PostgreSQL schema. Used only inside data access."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import JSON, CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class CountryRow(Base):
    __tablename__ = "countries"
    __table_args__ = (UniqueConstraint("code", name="uq_countries_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(2))
    name: Mapped[str] = mapped_column(String(100))


class RoomTypeRow(Base):
    __tablename__ = "room_types"
    __table_args__ = (
        UniqueConstraint("code", name="uq_room_types_code"),
        CheckConstraint("room_count >= 0", name="ck_room_types_room_count"),
        CheckConstraint("max_guests BETWEEN 1 AND 4", name="ck_room_types_max_guests"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(100))
    room_count: Mapped[int]
    max_guests: Mapped[int]
    demo_data: Mapped[bool]
    prices: Mapped[list["RoomTypePriceRow"]] = relationship(lazy="selectin")


class RoomTypePriceRow(Base):
    __tablename__ = "room_type_prices"
    __table_args__ = (
        UniqueConstraint("room_type_id", "season", name="uq_room_type_prices_type_season"),
        CheckConstraint("season IN ('low', 'mid', 'high')", name="ck_room_type_prices_season"),
        CheckConstraint("suggested_nightly_rate > 0", name="ck_room_type_prices_rate"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    room_type_id: Mapped[int] = mapped_column(ForeignKey("room_types.id", name="fk_room_type_prices_room_type"))
    season: Mapped[str] = mapped_column(String(10))
    suggested_nightly_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2))


class BookingRow(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("departure > arrival", name="ck_bookings_dates"),
        CheckConstraint("guest_count > 0", name="ck_bookings_guest_count"),
        CheckConstraint("nightly_rate > 0", name="ck_bookings_nightly_rate"),
        CheckConstraint("status IN ('active', 'cancelled')", name="ck_bookings_status"),
        Index("ix_bookings_type_status_dates", "room_type_id", "status", "arrival", "departure"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    guest_name: Mapped[str] = mapped_column(String(200))
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id", name="fk_bookings_country"))
    room_type_id: Mapped[int] = mapped_column(ForeignKey("room_types.id", name="fk_bookings_room_type"))
    arrival: Mapped[date] = mapped_column(Date)
    departure: Mapped[date] = mapped_column(Date)
    guest_count: Mapped[int]
    nightly_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(10))
    demo_data: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime)
    country: Mapped[CountryRow] = relationship(lazy="joined")
    room_type: Mapped[RoomTypeRow] = relationship(lazy="joined")


class DrinkRow(Base):
    __tablename__ = "drinks"
    __table_args__ = (
        UniqueConstraint("name", name="uq_drinks_name"),
        CheckConstraint("category IN ('cocktail', 'coffee')", name="ck_drinks_category"),
        CheckConstraint("suggested_unit_price > 0", name="ck_drinks_price"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(10))
    suggested_unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))


class EmployeeRow(Base):
    __tablename__ = "employees"
    __table_args__ = (UniqueConstraint("code", name="uq_employees_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(100))


class BarSaleRow(Base):
    __tablename__ = "bar_sales"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_bar_sales_quantity"),
        CheckConstraint("unit_price > 0", name="ck_bar_sales_unit_price"),
        CheckConstraint("status IN ('active', 'cancelled')", name="ck_bar_sales_status"),
        Index("ix_bar_sales_employee_status_date", "employee_id", "status", "sale_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    drink_id: Mapped[int] = mapped_column(ForeignKey("drinks.id", name="fk_bar_sales_drink"))
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", name="fk_bar_sales_employee"))
    quantity: Mapped[int]
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    sale_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(10))
    demo_data: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime)


class IdempotencyRequestRow(Base):
    __tablename__ = "idempotency_requests"
    __table_args__ = (
        UniqueConstraint("http_method", "path", "idempotency_key", name="uq_idempotency_requests_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    http_method: Mapped[str] = mapped_column(String(10))
    path: Mapped[str] = mapped_column(String(100))
    idempotency_key: Mapped[str] = mapped_column(String(128))
    payload_hash: Mapped[str] = mapped_column(String(64))
    response_status: Mapped[int]
    response_body: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class SeedRunRow(Base):
    __tablename__ = "seed_runs"
    __table_args__ = (UniqueConstraint("version", name="uq_seed_runs_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[str] = mapped_column(String(50))
    source_checksums: Mapped[dict] = mapped_column(JSON)
    anchor_date: Mapped[date] = mapped_column(Date)
    anchor_year: Mapped[int]
    completed_at: Mapped[datetime] = mapped_column(DateTime)


class ImportReportRow(Base):
    __tablename__ = "import_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(100))
    catalog_count: Mapped[int]
    reference_count: Mapped[int]
    omitted_count: Mapped[int]
    reasons: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class HistoricalReferenceRecordRow(Base):
    __tablename__ = "historical_reference_records"
    __table_args__ = (
        UniqueConstraint("source", "row_number", name="uq_historical_reference_records_row"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(100))
    row_number: Mapped[int]
    original_values: Mapped[dict] = mapped_column(JSON)
