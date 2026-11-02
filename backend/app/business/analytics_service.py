"""Official analytics: one read snapshot, Decimal amounts and dated room nights."""
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from app.business.models import Clock, DrinkCategory, FieldError, ResourceStatus, TemporarilyUnavailable, ValidationFailed
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


def ratio(numerator, denominator, percent=False):
    if denominator == 0:
        return None
    return (Decimal(numerator) / Decimal(denominator) * (100 if percent else 1)).quantize(Decimal('0.01'))


def period_totals(selected, available_dates, room_count, today):
    revenues = revenue_periods(selected, today)
    result = {}
    for period in ('past', 'upcoming', 'all'):
        def included(night):
            return period == 'all' or (night < today if period == 'past' else night >= today)
        booked = sum(1 for _, nights in selected for night in nights if included(night))
        available = room_count * sum(1 for night in available_dates if included(night))
        result[period] = {
            'revenue': revenues[period], 'bookedRoomNights': booked, 'availableRoomNights': available,
            'occupancyRatePercent': ratio(booked, available, percent=True),
            'occupancyStatus': 'ok' if available else 'no_data',
            'adr': ratio(revenues[period], booked), 'adrStatus': 'ok' if booked else 'no_data',
        }
    return result


def ranked_revenues(groups, id_field, name_field):
    ordered = sorted(groups.items(), key=lambda item: (-item[1]['revenue'], item[0]))
    result = []
    previous = None
    rank = 0
    for position, (id, values) in enumerate(ordered, 1):
        if values['revenue'] != previous:
            rank = position
        result.append({'rank': rank, id_field: id, name_field: values['name'], 'revenue': values['revenue']})
        previous = values['revenue']
    return result


def hotel_groups(selected):
    types = {}
    countries = {}
    seasons = {}
    guests = defaultdict(int)
    for booking, nights in selected:
        guests[booking.country_id] += booking.guest_count
        for target, id, name in [(types, booking.room_type_id, booking.room_type_name),
                                 (countries, booking.country_id, booking.country_name)]:
            group = target.setdefault(id, {'name': name, 'revenue': ZERO})
            group['revenue'] += booking.nightly_rate * len(nights)
        for night in nights:
            key = (booking.room_type_id, season_for_date(night))
            group = seasons.setdefault(key, {'roomTypeId': booking.room_type_id,
                'roomTypeName': booking.room_type_name, 'season': key[1], 'revenue': ZERO})
            group['revenue'] += booking.nightly_rate
    return {
        'byRoomTypeAndSeason': [seasons[key] for key in sorted(seasons)],
        'byCountry': [{'countryId': id, 'countryName': item['name'], 'revenue': item['revenue']} for id, item in sorted(countries.items())],
        'guestStaysByCountry': [{'countryId': id, 'countryName': countries[id]['name'], 'guestStays': count} for id, count in sorted(guests.items())],
        'topRoomTypes': ranked_revenues(types, 'roomTypeId', 'roomTypeName'),
        'topCountries': ranked_revenues(countries, 'countryId', 'countryName'),
    }


def hotel_result(catalogs, bookings, year, season, country_id, room_type_id, today, generated_at):
    """The official hotel figures. REST and the Tableau feed both get them from here."""
    selected = hotel_nights(bookings, year, season, country_id, room_type_id)
    available_dates = [night for night in dates_between(date(year, 1, 1), date(year + 1, 1, 1))
                       if season is None or season_for_date(night) == season]
    room_count = sum(room.room_count for room in catalogs.room_types if room_type_id is None or room.id == room_type_id)
    return {
        'filters': {'year': year, 'season': season, 'countryId': country_id, 'roomTypeId': room_type_id},
        'generatedAt': generated_at, 'businessDate': today,
        'demoData': any(booking.demo_data for booking, _ in selected) or any(
            room.demo_data for room in catalogs.room_types if room_type_id is None or room.id == room_type_id),
        'totals': period_totals(selected, available_dates, room_count, today),
        'occupancyScope': 'country_contribution' if country_id is not None else 'hotel',
        **hotel_groups(selected),
        'satisfaction': {'status': 'no_data'},
    }


def bar_result(catalogs, sales, year, employee, today, generated_at):
    """The official bar figures. REST and the Tableau feed both get them from here."""
    selected = [sale for sale in sales if sale.status is ResourceStatus.ACTIVE and sale.employee_id == employee.id]
    return {
        'filters': {'year': year, 'employeeId': employee.id, 'employeeName': employee.name},
        'generatedAt': generated_at, 'businessDate': today,
        'demoData': any(sale.demo_data for sale in selected),
        **bar_totals(selected, catalogs.drinks),
    }


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
        return hotel_result(catalogs, bookings, year, season, country_id, room_type_id, today, generated_at)

    def bar(self, year=None, employee_id=None):
        today = self._clock.business_date()
        year = today.year if year is None else year
        with self._uow_factory() as uow:
            uow.begin_snapshot()
            generated_at = self._clock.now_utc()
            catalogs = uow.catalogs.get_all()
            if employee_id is None:
                employee_id = next((item.id for item in catalogs.employees if item.code == 'helene-christine'), None)
                if employee_id is None:
                    raise TemporarilyUnavailable('Standardmedarbejderen mangler i kataloget.')
            self._reference(catalogs.employees, employee_id, 'employeeId')
            employee = next(item for item in catalogs.employees if item.id == employee_id)
            sales = uow.sales.for_year(year)
        return bar_result(catalogs, sales, year, employee, today, generated_at)


def bar_totals(sales, drinks):
    by_drink = []
    for drink in drinks:
        selected = [sale for sale in sales if sale.drink_id == drink.id]
        by_drink.append({'drinkId': drink.id, 'drinkName': drink.name, 'category': drink.category,
            'quantity': sum(sale.quantity for sale in selected),
            'revenue': sum((sale.total_amount for sale in selected), ZERO)})
    quantity = sum(item['quantity'] for item in by_drink)
    revenue = sum((item['revenue'] for item in by_drink), ZERO)
    categories = []
    for category in DrinkCategory:
        items = [item for item in by_drink if item['category'] == category]
        count = sum(item['quantity'] for item in items)
        amount = sum((item['revenue'] for item in items), ZERO)
        categories.append({'category': category, 'quantity': count, 'revenue': amount,
            'quantitySharePercent': ratio(count, quantity, percent=True),
            'revenueSharePercent': ratio(amount, revenue, percent=True),
            'shareStatus': 'ok' if quantity and revenue else 'no_data'})
    return {'totals': {'quantity': quantity, 'revenue': revenue}, 'byDrink': by_drink, 'byCategory': categories}
