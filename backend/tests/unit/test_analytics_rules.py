"""T041/T045: independent hand-calculated room-night expectations."""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.business.models import ResourceStatus, Season
from app.business.analytics_service import hotel_nights, revenue_periods


def booking(arrival, departure, **changes):
    return SimpleNamespace(arrival=date.fromisoformat(arrival), departure=date.fromisoformat(departure),
        **(dict(nightly_rate=Decimal('1000.00'), guest_count=2, country_id=1, room_type_id=1,
        status=ResourceStatus.ACTIVE, country_name='Sweden', room_type_name='Single') | changes))


def test_us7_1_year_boundary():
    stay = booking('2025-12-30', '2026-01-02')
    old = hotel_nights([stay], 2025)
    new = hotel_nights([stay], 2026)
    assert revenue_periods(old, date(2026, 10, 29))['all'] == Decimal('2000.00')
    assert revenue_periods(new, date(2026, 10, 29))['all'] == Decimal('1000.00')


def test_us7_5_season_boundary():
    stay = booking('2026-02-28', '2026-03-02')
    assert revenue_periods(hotel_nights([stay], 2026, Season.LOW), date(2026, 10, 29))['all'] == Decimal('1000.00')
    assert revenue_periods(hotel_nights([stay], 2026, Season.MID), date(2026, 10, 29))['all'] == Decimal('1000.00')


def test_us7_3_guests_are_counted_once():
    from app.business.analytics_service import hotel_groups
    selected = hotel_nights([booking('2026-06-10', '2026-06-13')], 2026)
    result = hotel_groups(selected)
    assert result['guestStaysByCountry'] == [{'countryId': 1, 'countryName': 'Sweden', 'guestStays': 2}]
    assert len(selected[0][1]) == 3
    assert result['byCountry'][0]['revenue'] == Decimal('3000.00')


def test_us7_2_competition_rank_for_countries_and_types():
    from app.business.analytics_service import hotel_groups
    stays = [booking('2026-06-10', '2026-06-13', country_id=1, room_type_id=1),
        booking('2026-06-10', '2026-06-13', country_id=2, room_type_id=2),
        booking('2026-06-10', '2026-06-12', country_id=3, room_type_id=3)]
    result = hotel_groups(hotel_nights(stays, 2026))
    assert [item['rank'] for item in result['topCountries']] == [1, 1, 3]
    assert [item['revenue'] for item in result['topRoomTypes']] == [Decimal('3000.00'), Decimal('3000.00'), Decimal('2000.00')]
    assert [item['rank'] for item in result['topRoomTypes']] == [1, 1, 3]


def test_filters_combine_and_cancelled_bookings_are_excluded():
    cancelled = booking('2026-02-28', '2026-03-02', status=ResourceStatus.CANCELLED)
    other = booking('2026-02-28', '2026-03-02', country_id=2)
    active = booking('2026-02-28', '2026-03-02')
    selected = hotel_nights([cancelled, other, active], 2026, Season.MID, 1, 1)
    assert len(selected) == 1
    assert selected[0][1] == [date(2026, 3, 1)]
    assert revenue_periods(selected, date(2026, 10, 29))['all'] == Decimal('1000.00')
    assert hotel_nights([active], 2026, Season.MID, 1, 2) == []


def test_leap_day_is_low_season_and_today_is_upcoming(frozen_clock):
    selected = hotel_nights([booking('2024-02-28', '2024-03-01')], 2024, Season.LOW)
    assert selected[0][1] == [date(2024, 2, 28), date(2024, 2, 29)]
    assert revenue_periods(selected, frozen_clock.business_date())['all'] == Decimal('2000.00')
    selected = hotel_nights([booking('2026-10-28', '2026-10-31')], 2026)
    assert revenue_periods(selected, frozen_clock.business_date()) == {
        'past': Decimal('1000.00'), 'upcoming': Decimal('2000.00'), 'all': Decimal('3000.00')}


def test_us8_1_two_rooms_two_nights(frozen_clock):
    from app.business.analytics_service import period_totals
    selected = hotel_nights([booking('2026-06-10', '2026-06-12')], 2026)
    result = period_totals(selected, [date(2026, 6, 10), date(2026, 6, 11)], 2, frozen_clock.business_date())
    assert result['all'] == {'revenue': Decimal('2000.00'), 'bookedRoomNights': 2,
        'availableRoomNights': 4, 'occupancyRatePercent': Decimal('50.00'), 'occupancyStatus': 'ok',
        'adr': Decimal('1000.00'), 'adrStatus': 'ok'}


def test_us8_3_zero_bookings_and_zero_capacity(frozen_clock):
    from app.business.analytics_service import period_totals
    positive = period_totals([], [date(2026, 6, 10)], 2, frozen_clock.business_date())['all']
    assert positive['revenue'] == Decimal('0.00')
    assert positive['adr'] is None and positive['adrStatus'] == 'no_data'
    assert positive['occupancyRatePercent'] == Decimal('0.00')
    assert positive['occupancyStatus'] == 'ok'
    empty = period_totals([], [], 0, frozen_clock.business_date())['all']
    assert empty['occupancyRatePercent'] is None and empty['occupancyStatus'] == 'no_data'


def test_us9_1_bar_mix():
    from app.business.analytics_service import bar_totals
    from app.business.models import Drink, DrinkCategory
    drinks = [Drink(1, 'Cocktail', DrinkCategory.COCKTAIL, Decimal('100.00')),
              Drink(2, 'Coffee', DrinkCategory.COFFEE, Decimal('50.00'))]
    sales = [SimpleNamespace(drink_id=1, quantity=3, total_amount=Decimal('300.00')),
             SimpleNamespace(drink_id=2, quantity=2, total_amount=Decimal('100.00'))]
    result = bar_totals(sales, drinks)
    assert result['totals'] == {'quantity': 5, 'revenue': Decimal('400.00')}
    assert result['byCategory'] == [
        {'category': DrinkCategory.COCKTAIL, 'quantity': 3, 'revenue': Decimal('300.00'),
         'quantitySharePercent': Decimal('60.00'), 'revenueSharePercent': Decimal('75.00'), 'shareStatus': 'ok'},
        {'category': DrinkCategory.COFFEE, 'quantity': 2, 'revenue': Decimal('100.00'),
         'quantitySharePercent': Decimal('40.00'), 'revenueSharePercent': Decimal('25.00'), 'shareStatus': 'ok'}]


def test_us9_3_no_sales_keeps_catalog_and_both_categories():
    from app.business.analytics_service import bar_totals
    from app.business.models import Drink, DrinkCategory
    result = bar_totals([], [Drink(1, 'Unused', DrinkCategory.COFFEE, Decimal('50.00'))])
    assert result['totals'] == {'quantity': 0, 'revenue': Decimal('0.00')}
    assert result['byDrink'][0]['quantity'] == 0
    assert result['byDrink'][0]['revenue'] == Decimal('0.00')
    assert len(result['byCategory']) == 2
    assert all(item['quantitySharePercent'] is None and item['revenueSharePercent'] is None and item['shareStatus'] == 'no_data' for item in result['byCategory'])
