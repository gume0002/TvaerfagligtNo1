"""Official analytics: one read snapshot, Decimal amounts and dated room nights."""
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from app.business.models import Clock, FieldError, ResourceStatus, ValidationFailed
from app.business.ports import UnitOfWorkFactory
from app.business.rules import season_for_date

ZERO = Decimal('0.00')


def dates_between(start: date, end: date):
    while start < end:
        yield start
        start += timedelta(days=1)


def hotel_nights(bookings, year, season=None, country_id=None, room_type_id=None):
    """One booking contributes one room night, regardless of guest count."""
    selected = []
    for booking in bookings:
        if booking.status is ResourceStatus.CANCELLED:
            continue
        if country_id is not None and booking.country_id != country_id:
            continue
        if room_type_id is not None and booking.room_type_id != room_type_id:
            continue
        nights = [night for night in dates_between(max(booking.arrival, date(year, 1, 1)),
            min(booking.departure, date(year + 1, 1, 1))) if season is None or season_for_date(night) == season]
        if nights:
            selected.append((booking, nights))
    return selected


def revenue_periods(selected, today):
    past = sum((booking.nightly_rate for booking, nights in selected for night in nights if night < today), ZERO)
    upcoming = sum((booking.nightly_rate for booking, nights in selected for night in nights if night >= today), ZERO)
    return {'past': past, 'upcoming': upcoming, 'all': past + upcoming}


class AnalyticsService:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock):
        self._uow_factory = uow_factory
        self._clock = clock

    @staticmethod
    def _reference(items, id, field):
        if id is not None and not any(item.id == id for item in items):
            raise ValidationFailed('Filtrene er ugyldige.', [FieldError(field, 'Værdien findes ikke.')])

    def hotel(self, year=None, season=None, country_id=None, room_type_id=None):
        today = self._clock.business_date()
        year = today.year if year is None else year
        with self._uow_factory() as uow:
            uow.begin_snapshot()
            generated_at = self._clock.now_utc()
            catalogs = uow.catalogs.get_all()
            self._reference(catalogs.countries, country_id, 'countryId')
            self._reference(catalogs.room_types, room_type_id, 'roomTypeId')
            bookings = uow.bookings.for_year(year)
        selected = hotel_nights(bookings, year, season, country_id, room_type_id)
        return {
            'filters': {'year': year, 'season': season, 'countryId': country_id, 'roomTypeId': room_type_id},
            'generatedAt': generated_at, 'businessDate': today,
            'demoData': any(booking.demo_data for booking, _ in selected) or any(
                room.demo_data for room in catalogs.room_types if room_type_id is None or room.id == room_type_id),
            'revenues': revenue_periods(selected, today),
        }
