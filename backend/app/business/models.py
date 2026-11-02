"""Domain objects and domain errors shared by the business and data access layers."""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import StrEnum
from zoneinfo import ZoneInfo

HOTEL_TIMEZONE = ZoneInfo("Europe/Copenhagen")


class Season(StrEnum):
    LOW = "low"
    MID = "mid"
    HIGH = "high"


class ResourceStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"


class StatusFilter(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    ALL = "all"


class DrinkCategory(StrEnum):
    COCKTAIL = "cocktail"
    COFFEE = "coffee"


class Clock:
    """Current time. Tests replace it with a frozen clock."""

    def now_utc(self) -> datetime:
        """Current UTC time without tzinfo and microseconds, as stored in MySQL."""
        return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)

    def business_date(self) -> date:
        return datetime.now(HOTEL_TIMEZONE).date()


# Errors
@dataclass(frozen=True)
class FieldError:
    field: str
    message: str


class DomainError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ValidationFailed(DomainError):
    def __init__(self, message: str, field_errors: list[FieldError]):
        super().__init__(message)
        self.field_errors = field_errors


class ResourceNotFound(DomainError):
    pass


class CapacityConflict(DomainError):
    pass


class ResourceCancelled(DomainError):
    pass


class IdempotencyConflict(DomainError):
    pass


class TemporarilyUnavailable(DomainError):
    pass


class RetryableTransactionError(Exception):
    """A deadlock or lock timeout. The whole transaction may be tried again."""


class DuplicateIdempotencyKey(Exception):
    """Another transaction saved the same key first. Read its result on retry."""


class SeedBlocked(DomainError):
    """The database has data but no seed marker, so nothing is overwritten."""


# Catalogs
@dataclass(frozen=True)
class Country:
    id: int
    code: str
    name: str


@dataclass(frozen=True)
class RoomType:
    id: int
    code: str
    name: str
    room_count: int
    max_guests: int
    demo_data: bool
    suggested_nightly_rates: dict[Season, Decimal]


@dataclass(frozen=True)
class Employee:
    id: int
    code: str
    name: str


@dataclass(frozen=True)
class Drink:
    id: int
    name: str
    category: DrinkCategory
    suggested_unit_price: Decimal


@dataclass(frozen=True)
class Catalogs:
    countries: list[Country]
    room_types: list[RoomType]
    employees: list[Employee]
    drinks: list[Drink]


# Bookings
@dataclass(frozen=True)
class BookingInput:
    guest_name: str
    country_id: int
    room_type_id: int
    arrival: date
    departure: date
    guest_count: int
    nightly_rate: Decimal


@dataclass(frozen=True)
class NewBooking:
    data: BookingInput
    status: ResourceStatus
    demo_data: bool
    created_at: datetime
    cancelled_at: datetime | None = None


@dataclass(frozen=True)
class Booking:
    id: int
    guest_name: str
    country_id: int
    country_name: str
    room_type_id: int
    room_type_name: str
    arrival: date
    departure: date
    guest_count: int
    nightly_rate: Decimal
    status: ResourceStatus
    demo_data: bool
    created_at: datetime
    updated_at: datetime
    cancelled_at: datetime | None


@dataclass(frozen=True)
class BookingSearch:
    name: str | None = None
    arrival_from: date | None = None
    departure_to: date | None = None
    status: StatusFilter = StatusFilter.ACTIVE
    offset: int = 0
    limit: int = 50


@dataclass(frozen=True)
class BookingPage:
    items: list[Booking]
    total: int


@dataclass(frozen=True)
class IdempotencyContext:
    http_method: str
    path: str
    key: str


@dataclass(frozen=True)
class StoredIdempotentResult:
    payload_hash: str
    response_status: int
    response_body: dict


# Seed
@dataclass(frozen=True)
class NewCountry:
    code: str
    name: str


@dataclass(frozen=True)
class NewRoomType:
    code: str
    name: str
    room_count: int
    max_guests: int
    suggested_nightly_rates: dict[Season, Decimal]


@dataclass(frozen=True)
class NewEmployee:
    code: str
    name: str


@dataclass(frozen=True)
class NewDrink:
    name: str
    category: DrinkCategory
    suggested_unit_price: Decimal


@dataclass(frozen=True)
class NewBarSale:
    drink_id: int
    employee_id: int
    quantity: int
    unit_price: Decimal
    sale_date: date
    status: ResourceStatus
    demo_data: bool
    created_at: datetime
    cancelled_at: datetime | None = None


@dataclass(frozen=True)
class ReferenceRecord:
    source: str
    row_number: int
    original_values: dict


@dataclass(frozen=True)
class ImportReport:
    source: str
    catalog_count: int
    reference_count: int
    omitted_count: int
    reasons: list[dict]


@dataclass(frozen=True)
class SeedMarker:
    version: str
    source_checksums: dict[str, str]
    anchor_date: date
    anchor_year: int
    completed_at: datetime


@dataclass(frozen=True)
class RawSheetRow:
    row_number: int
    values: dict


@dataclass(frozen=True)
class RawCell:
    reference: str
    value: object


@dataclass(frozen=True)
class RawData:
    """The original files, read but not interpreted."""

    hotel_source: str
    hotel_rows: list[RawSheetRow]
    hotel_stray_cells: list[RawCell]
    bar_source: str
    bar_rows: list[RawSheetRow]
    bar_stray_cells: list[RawCell]
    hotel_csv_source: str
    hotel_csv_replacement_characters: int
    checksums: dict[str, str]


@dataclass(frozen=True)
class SeedResult:
    version: str
    already_completed: bool
    bookings: int = 0
    bar_sales: int = 0
    reference_records: int = 0


@dataclass(frozen=True)
class SaleInput:
    drink_id: int
    employee_id: int
    quantity: int
    unit_price: Decimal
    sale_date: date


@dataclass(frozen=True)
class Sale:
    id: int
    drink_id: int
    drink_name: str
    category: DrinkCategory
    employee_id: int
    employee_name: str
    quantity: int
    unit_price: Decimal
    sale_date: date
    status: ResourceStatus
    demo_data: bool
    created_at: datetime
    updated_at: datetime
    cancelled_at: datetime | None

    @property
    def total_amount(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class SaleSearch:
    sale_date_from: date | None = None
    sale_date_to: date | None = None
    employee_id: int | None = None
    status: StatusFilter = StatusFilter.ACTIVE
    offset: int = 0
    limit: int = 50
