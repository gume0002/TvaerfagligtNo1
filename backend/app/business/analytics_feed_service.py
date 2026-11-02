"""Tableau's read feed: the official results for every filter combination.

Tableau filters only work on its stored extract and do not call the API, so a
filter that changes a denominator or a ranking needs a calculated row for each
choice. No figure is calculated here. Every number comes from hotel_result and
bar_result, the same functions the REST analytics use.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from app.business.analytics_service import bar_result, hotel_result
from app.business.models import Clock, Season
from app.business.ports import UnitOfWorkFactory

ALL = 'all'
EARLIEST_YEAR = 2000
LATEST_YEAR = 2100
PERIODS = ('past', 'upcoming', 'all')
SEASONS = (None, *Season)


@dataclass(frozen=True)
class _Snapshot:
    catalogs: object
    today: date
    generated_at: object
    records_by_year: dict


def _stay_years(stays):
    years = set()
    for arrival, departure in stays:
        last_night = departure - timedelta(days=1)
        years.update(range(max(arrival.year, EARLIEST_YEAR), min(last_night.year, LATEST_YEAR) + 1))
    return years


def _bookings_by_selection(bookings):
    """Group the bookings once, so each combination only looks at its own."""
    selections = defaultdict(list)
    for booking in bookings:
        for country_id in (None, booking.country_id):
            for room_type_id in (None, booking.room_type_id):
                selections[(country_id, room_type_id)].append(booking)
    return selections


class AnalyticsFeedService:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock):
        self._uow_factory = uow_factory
        self._clock = clock

    def hotel_totals(self):
        return [
            {
                **filters,
                'period': period,
                **result['totals'][period],
                'occupancyScope': result['occupancyScope'],
                'satisfactionStatus': result['satisfaction']['status'],
                'businessDate': result['businessDate'],
                **_metadata(result),
            }
            for filters, result in self._hotel_results()
            for period in PERIODS
        ]

    def hotel_room_type_season(self):
        return [
            {
                **filters,
                'roomType': item['roomTypeName'],
                'season': item['season'],
                'revenue': item['revenue'],
                **_metadata(result),
            }
            for filters, result in self._hotel_results()
            for item in result['byRoomTypeAndSeason']
        ]

    def hotel_countries(self):
        rows = []
        for filters, result in self._hotel_results():
            guests = {item['countryId']: item['guestStays'] for item in result['guestStaysByCountry']}
            rows.extend(
                {
                    **filters,
                    'country': item['countryName'],
                    'revenue': item['revenue'],
                    'revenueRank': item['rank'],
                    'guestStays': guests[item['countryId']],
                    **_metadata(result),
                }
                for item in result['topCountries']
            )
        return rows

    def hotel_room_type_ranks(self):
        return [
            {
                **filters,
                'roomType': item['roomTypeName'],
                'revenue': item['revenue'],
                'revenueRank': item['rank'],
                **_metadata(result),
            }
            for filters, result in self._hotel_results()
            for item in result['topRoomTypes']
        ]

    def bar_totals(self):
        return [
            {**filters, **result['totals'], **_metadata(result)}
            for filters, result in self._bar_results()
        ]

    def bar_drinks(self):
        return [
            {
                **filters,
                'drink': item['drinkName'],
                'category': item['category'],
                'quantity': item['quantity'],
                'revenue': item['revenue'],
                **_metadata(result),
            }
            for filters, result in self._bar_results()
            for item in result['byDrink']
        ]

    def bar_categories(self):
        return [
            {**filters, **item, **_metadata(result)}
            for filters, result in self._bar_results()
            for item in result['byCategory']
        ]

    def _hotel_results(self):
        snapshot = self._read_hotel()
        catalogs = snapshot.catalogs
        countries = [(None, ALL)] + [(item.id, item.name) for item in catalogs.countries]
        room_types = [(None, ALL)] + [(item.id, item.name) for item in catalogs.room_types]
        for year, bookings in snapshot.records_by_year.items():
            selections = _bookings_by_selection(bookings)
            for season in SEASONS:
                for country_id, country in countries:
                    for room_type_id, room_type in room_types:
                        filters = {
                            'year': year,
                            'seasonFilter': season or ALL,
                            'countryFilter': country,
                            'roomTypeFilter': room_type,
                        }
                        selected = selections.get((country_id, room_type_id), [])
                        yield filters, hotel_result(
                            catalogs, selected, year, season, country_id, room_type_id,
                            snapshot.today, snapshot.generated_at,
                        )

    def _bar_results(self):
        snapshot = self._read_bar()
        for year, sales in snapshot.records_by_year.items():
            for employee in snapshot.catalogs.employees:
                filters = {'year': year, 'employee': employee.name}
                yield filters, bar_result(snapshot.catalogs, sales, year, employee, snapshot.today, snapshot.generated_at)

    def _read_hotel(self) -> _Snapshot:
        today = self._clock.business_date()
        with self._uow_factory() as uow:
            uow.begin_snapshot()
            generated_at = self._clock.now_utc()
            catalogs = uow.catalogs.get_all()
            years = sorted(_stay_years(uow.bookings.active_stays()) | {today.year})
            return _Snapshot(catalogs, today, generated_at, {year: uow.bookings.for_year(year) for year in years})

    def _read_bar(self) -> _Snapshot:
        today = self._clock.business_date()
        with self._uow_factory() as uow:
            uow.begin_snapshot()
            generated_at = self._clock.now_utc()
            catalogs = uow.catalogs.get_all()
            sale_years = {
                sale_date.year for sale_date in uow.sales.active_sale_dates()
                if EARLIEST_YEAR <= sale_date.year <= LATEST_YEAR
            }
            years = sorted(sale_years | {today.year})
            return _Snapshot(catalogs, today, generated_at, {year: uow.sales.for_year(year) for year in years})


def _metadata(result):
    return {'demoData': result['demoData'], 'generatedAt': result['generatedAt']}
