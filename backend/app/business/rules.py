"""Domain rules without any dependency on storage."""

from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from decimal import Decimal

from app.business.models import FieldError, Season

MAX_AMOUNT = Decimal("9999999999.99")
EARLIEST_DATE = date(1000, 1, 1)
LOW_SEASON_MONTHS = {1, 2}
HIGH_SEASON_MONTHS = {6, 7, 8, 12}


def season_for_date(night: date) -> Season:
    if night.month in LOW_SEASON_MONTHS:
        return Season.LOW
    if night.month in HIGH_SEASON_MONTHS:
        return Season.HIGH
    return Season.MID


def amount_errors(field: str, amount: Decimal) -> list[FieldError]:
    """An amount must be positive, have at most two decimals and fit DECIMAL(12,2)."""
    if not amount.is_finite() or amount <= 0:
        return [FieldError(field, "Beløbet skal være større end 0.")]
    if amount.as_tuple().exponent < -2:
        return [FieldError(field, "Beløbet må højst have to decimaler.")]
    if amount > MAX_AMOUNT:
        return [FieldError(field, "Beløbet er for stort.")]
    return []


def first_overbooked_night(
    arrival: date,
    departure: date,
    existing_stays: Iterable[tuple[date, date]],
    room_count: int,
) -> date | None:
    """Return the first night in [arrival, departure) without a free room.

    A departure day is not a night, so arriving on another guest's departure day
    is allowed. Only start and end of each stay are visited, so the work follows
    the number of bookings and not the length of the stay.
    """
    if room_count <= 0:
        return arrival
    changes: dict[date, int] = defaultdict(int)
    for stay_arrival, stay_departure in existing_stays:
        start = max(stay_arrival, arrival)
        end = min(stay_departure, departure)
        if start < end:
            changes[start] += 1
            changes[end] -= 1
    occupied = 0
    for night in sorted(changes):
        occupied += changes[night]
        if night < departure and occupied >= room_count:
            return night
    return None
