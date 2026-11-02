"""T041/T045: independent hand-calculated room-night expectations."""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.business.models import ResourceStatus, Season
from app.business.analytics_service import hotel_nights, revenue_periods


def booking(arrival, departure, **changes):
    return SimpleNamespace(arrival=date.fromisoformat(arrival), departure=date.fromisoformat(departure),
        **(dict(nightly_rate=Decimal('1000.00'), guest_count=2, country_id=1, room_type_id=1,
        status=ResourceStatus.ACTIVE) | changes))


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
