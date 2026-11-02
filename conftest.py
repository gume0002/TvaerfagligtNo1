"""Shared fixtures. Tests only ever use the isolated test-db from the test profile."""

import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.business.models import Clock
from app.config import Settings
from app.data_access.database import create_database_engine, create_session_factory
from app.data_access.orm_models import (
    Base,
    CountryRow,
    DrinkRow,
    EmployeeRow,
    RoomTypePriceRow,
    RoomTypeRow,
    SeedRunRow,
)
from app.data_access.unit_of_work import SqlUnitOfWork

REPO_ROOT = Path(__file__).resolve().parent


class FrozenClock(Clock):
    """The fixed test date from specs/004-hotelsystem/plan.md, section 8."""

    def __init__(self, today: date = date(2026, 10, 29)):
        self.today = today

    def now_utc(self) -> datetime:
        return datetime(self.today.year, self.today.month, self.today.day, 10, 0, 0)

    def business_date(self) -> date:
        return self.today


@pytest.fixture(scope="session")
def settings():
    assert os.environ["DATABASE_HOST"] == "test-db", "Tests may only run against the isolated test database."
    return Settings.from_env()


@pytest.fixture(scope="session")
def engine(settings):
    command.upgrade(Config(str(REPO_ROOT / "backend/alembic.ini")), "head")
    engine = create_database_engine(settings)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def session_factory(engine):
    return create_session_factory(engine)


@pytest.fixture()
def uow_factory(session_factory):
    return lambda: SqlUnitOfWork(session_factory)


def _truncate_all(engine):
    with engine.begin() as connection:
        connection.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for table in Base.metadata.sorted_tables:
            connection.execute(text(f"TRUNCATE TABLE {table.name}"))
        connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))


@pytest.fixture()
def empty_database(engine):
    _truncate_all(engine)
    return engine


@pytest.fixture()
def catalog(empty_database):
    """A small, known catalog. `tiny` has one room, which makes capacity easy to test."""
    with Session(empty_database, expire_on_commit=False) as session:
        sweden = CountryRow(code="SE", name="Sweden")
        germany = CountryRow(code="DE", name="Germany")

        def room_type(code, name, room_count, max_guests):
            return RoomTypeRow(
                code=code,
                name=name,
                room_count=room_count,
                max_guests=max_guests,
                demo_data=True,
                prices=[
                    RoomTypePriceRow(season=season, suggested_nightly_rate=Decimal(rate))
                    for season, rate in (("low", "900.00"), ("mid", "1000.00"), ("high", "1100.00"))
                ],
            )

        tiny = room_type("tiny", "Tiny Room", 1, 2)
        double = room_type("double", "Double Room", 2, 2)
        large = room_type("large", "Large Suite", 5, 4)
        helene = EmployeeRow(code="helene-christine", name="Helene Christine")
        drink = DrinkRow(name="Negroni", category="cocktail", suggested_unit_price=Decimal("100.00"))
        marker = SeedRunRow(
            version="test",
            source_checksums={},
            anchor_date=date(2026, 10, 29),
            anchor_year=2026,
            completed_at=datetime(2026, 10, 29, 10, 0, 0),
        )
        session.add_all([sweden, germany, tiny, double, large, helene, drink, marker])
        session.commit()
        return SimpleNamespace(
            sweden=sweden.id,
            germany=germany.id,
            tiny=tiny.id,
            double=double.id,
            large=large.id,
        )


@pytest.fixture()
def frozen_clock():
    return FrozenClock()
