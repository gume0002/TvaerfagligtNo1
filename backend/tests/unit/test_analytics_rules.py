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
