"""Constructed demo master data from specs/004-hotelsystem/plan.md, section 8.

Room counts and guest limits are not the hotel's real distribution.
"""

from decimal import Decimal

from app.business.models import NewEmployee, NewRoomType, Season

HELENE_CHRISTINE_CODE = "helene-christine"
DEMO_EMPLOYEE_CODE = "demo-employee"


def _room_type(code: str, name: str, room_count: int, max_guests: int, low: str, mid: str, high: str) -> NewRoomType:
    return NewRoomType(
        code=code,
        name=name,
        room_count=room_count,
        max_guests=max_guests,
        suggested_nightly_rates={Season.LOW: Decimal(low), Season.MID: Decimal(mid), Season.HIGH: Decimal(high)},
    )


ROOM_TYPES = [
    _room_type("standard-single", "Standard Single", 30, 1, "900.00", "1050.00", "1200.00"),
    _room_type("grand-lit", "Grand Lit", 30, 2, "1100.00", "1250.00", "1400.00"),
    _room_type("standard-double", "Standard Double", 60, 2, "1200.00", "1400.00", "1600.00"),
    _room_type("superior-double", "Superior Double", 40, 2, "1400.00", "1700.00", "2000.00"),
    _room_type("junior-suite", "Junior Suite", 20, 3, "1800.00", "2150.00", "2500.00"),
    _room_type("spa-executive", "Spa Executive", 14, 2, "2000.00", "2400.00", "2800.00"),
    _room_type("suite", "Suite", 12, 4, "2500.00", "3000.00", "3500.00"),
    _room_type("loft-suite", "LOFT Suite", 8, 4, "3000.00", "3500.00", "4000.00"),
]

# The 20 countries in the hotel data plus Denmark, mapped to ISO 3166-1 alpha-2.
COUNTRY_CODES = {
    "Australia": "AU",
    "Brazil": "BR",
    "Canada": "CA",
    "China": "CN",
    "Denmark": "DK",
    "Egypt": "EG",
    "France": "FR",
    "Germany": "DE",
    "India": "IN",
    "Italy": "IT",
    "Japan": "JP",
    "Mexico": "MX",
    "Nigeria": "NG",
    "Pakistan": "PK",
    "Russia": "RU",
    "South Korea": "KR",
    "Spain": "ES",
    "Sweden": "SE",
    "United Kingdom": "GB",
    "United States": "US",
    "Vietnam": "VN",
}

EMPLOYEES = [
    NewEmployee(code=HELENE_CHRISTINE_CODE, name="Helene Christine"),
    NewEmployee(code=DEMO_EMPLOYEE_CODE, name="Demomedarbejder"),
]
