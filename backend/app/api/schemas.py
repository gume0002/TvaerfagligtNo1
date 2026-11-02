"""JSON transport models. They check format only, never business rules."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from app.business.models import Booking, BookingInput, Catalogs


def _parse_iso_date(value: object) -> date:
    if not isinstance(value, str) or len(value) != 10:
        raise ValueError("Expected a date formatted as YYYY-MM-DD")
    return date.fromisoformat(value)


IsoDate = Annotated[date, BeforeValidator(_parse_iso_date)]
StrictInt = Annotated[int, Field(strict=True)]
MoneyInput = Annotated[str, Field(pattern=r"^[0-9]+(\.[0-9]{1,2})?$", max_length=20)]


def money(amount: Decimal) -> str:
    return format(amount, ".2f")


def timestamp(value: datetime | None) -> str | None:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ") if value else None


class BookingBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    guestName: Annotated[str, Field(min_length=1, max_length=200)]
    countryId: StrictInt
    roomTypeId: StrictInt
    arrival: IsoDate
    departure: IsoDate
    guestCount: StrictInt
    nightlyRate: MoneyInput

    def to_domain(self) -> BookingInput:
        return BookingInput(
            guest_name=self.guestName,
            country_id=self.countryId,
            room_type_id=self.roomTypeId,
            arrival=self.arrival,
            departure=self.departure,
            guest_count=self.guestCount,
            nightly_rate=Decimal(self.nightlyRate),
        )


def booking_json(booking: Booking) -> dict:
    return {
        "id": booking.id,
        "guestName": booking.guest_name,
        "countryId": booking.country_id,
        "countryName": booking.country_name,
        "roomTypeId": booking.room_type_id,
        "roomTypeName": booking.room_type_name,
        "arrival": booking.arrival.isoformat(),
        "departure": booking.departure.isoformat(),
        "guestCount": booking.guest_count,
        "nightlyRate": money(booking.nightly_rate),
        "status": booking.status.value,
        "demoData": booking.demo_data,
        "createdAt": timestamp(booking.created_at),
        "updatedAt": timestamp(booking.updated_at),
        "cancelledAt": timestamp(booking.cancelled_at),
    }


def catalogs_json(catalogs: Catalogs) -> dict:
    return {
        "countries": [{"id": item.id, "code": item.code, "name": item.name} for item in catalogs.countries],
        "roomTypes": [
            {
                "id": item.id,
                "code": item.code,
                "name": item.name,
                "roomCount": item.room_count,
                "maxGuests": item.max_guests,
                "demoData": item.demo_data,
                "suggestedNightlyRates": {
                    season.value: money(rate) for season, rate in item.suggested_nightly_rates.items()
                },
            }
            for item in catalogs.room_types
        ],
        "employees": [{"id": item.id, "code": item.code, "name": item.name} for item in catalogs.employees],
        "drinks": [
            {
                "id": item.id,
                "name": item.name,
                "category": item.category.value,
                "suggestedUnitPrice": money(item.suggested_unit_price),
            }
            for item in catalogs.drinks
        ],
    }
