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


def test_both_analyses_read_rows_from_their_catalog_snapshot(settings, frozen_clock, catalog, uow_factory, engine):
    from datetime import date, datetime
    from app.business.analytics_service import AnalyticsService
    from app.data_access.orm_models import BarSaleRow, BookingRow

    def factory_with_concurrent_write():
        uow = uow_factory()
        class InterleavedRead:
            def __enter__(self):
                uow.__enter__()
                original = uow.catalogs.get_all
                def read_then_commit():
                    catalogs = original()
                    now = datetime(2026, 10, 29, 10)
                    with Session(engine) as writer:
                        writer.add(BookingRow(guest_name='Concurrent', country_id=catalog.sweden,
                            room_type_id=catalog.large, arrival=date(2026, 10, 28), departure=date(2026, 10, 30),
                            guest_count=2, nightly_rate=Decimal('1000.00'), status='active', demo_data=False,
                            created_at=now, updated_at=now))
                        writer.add(BarSaleRow(drink_id=1, employee_id=1, quantity=3, unit_price=Decimal('100.00'),
                            sale_date=date(2026, 10, 29), status='active', demo_data=False, created_at=now, updated_at=now))
                        writer.commit()
                    return catalogs
                uow.catalogs.get_all = read_then_commit
                return uow
            def __exit__(self, *args):
                return uow.__exit__(*args)
        return InterleavedRead()

    service = AnalyticsService(factory_with_concurrent_write, frozen_clock)
    assert service.hotel()['totals']['all']['revenue'] == Decimal('0.00')
    # The second snapshot sees the first committed sale but not the new one
    # written between its catalog and sales reads.
    assert service.bar()['totals'] == {'quantity': 3, 'revenue': Decimal('300.00')}
    current = AnalyticsService(uow_factory, frozen_clock)
    assert current.hotel()['totals']['all']['revenue'] == Decimal('4000.00')
    assert current.bar()['totals'] == {'quantity': 6, 'revenue': Decimal('600.00')}
