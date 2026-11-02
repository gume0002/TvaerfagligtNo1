"""T012: MySQL snapshot spans repositories and does not change write isolation."""
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.data_access.orm_models import DrinkRow, RoomTypeRow


def test_consistent_snapshot_across_concurrent_commits(catalog, engine, uow_factory):
    with uow_factory() as reader:
        reader.begin_snapshot()
        before = reader.catalogs.get_all()
        with Session(engine) as writer:
            writer.get_one(DrinkRow, 1).suggested_unit_price = Decimal('999.00')
            writer.get_one(RoomTypeRow, catalog.tiny).room_count = 99
            writer.commit()
        after = reader.catalogs.get_all()
        assert after == before
        assert after.drinks[0].suggested_unit_price == Decimal('100.00')
        assert after.room_types[0].room_count == 1
    with uow_factory() as reader:
        assert reader.catalogs.get_all().drinks[0].suggested_unit_price == Decimal('999.00')
    with engine.connect() as connection:
        assert connection.scalar(text('SELECT @@transaction_isolation')) == 'READ-COMMITTED'
