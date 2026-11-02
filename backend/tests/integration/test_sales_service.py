"""T033: sale creation through business and MySQL."""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.business.models import SaleInput, IdempotencyContext, ValidationFailed
from app.business.sale_service import SaleService
from app.data_access.orm_models import DrinkRow


def test_creation_freezes_price_and_checks_references(catalog, uow_factory, frozen_clock, engine):
    service = SaleService(uow_factory, frozen_clock)
    data = SaleInput(1, 1, 3, Decimal('100.00'), date(2026, 10, 29))
    result = service.create(data, IdempotencyContext('POST', '/api/bar-sales', 'test'))
    assert result.total_amount == Decimal('300.00')
    with Session(engine) as session:
        session.get_one(DrinkRow, 1).suggested_unit_price = Decimal('200.00')
        session.commit()
    replay = service.create(data, IdempotencyContext('POST', '/api/bar-sales', 'test'))
    assert replay.unit_price == Decimal('100.00')
    assert replay == result
    for drink, employee, field in [(9999, 1, 'drinkId'), (1, 9999, 'employeeId')]:
        with pytest.raises(ValidationFailed) as error:
            service.create(SaleInput(drink, employee, 1, Decimal('10'), date(2026, 10, 29)), IdempotencyContext('POST', '/api/bar-sales', field))
        assert field in {item.field for item in error.value.field_errors}


def test_update_cancel_and_atomic_errors(catalog, uow_factory, frozen_clock):
    from dataclasses import replace
    from app.business.models import ResourceCancelled
    service = SaleService(uow_factory, frozen_clock)
    data = SaleInput(1, 1, 3, Decimal('100.00'), date(2026, 10, 29))
    created = service.create(data, IdempotencyContext('POST', '/api/bar-sales', 'one'))
    updated = service.update(created.id, replace(data, quantity=2))
    assert updated.total_amount == Decimal('200.00')
    with pytest.raises(ValidationFailed):
        service.update(created.id, replace(data, drink_id=9999))
    with uow_factory() as uow:
        assert uow.sales.get(created.id) == updated
    service.cancel(created.id)
    with uow_factory() as uow:
        cancelled = uow.sales.get(created.id)
    frozen_clock.today = date(2027, 1, 1)
    service.cancel(created.id)
    with uow_factory() as uow:
        assert uow.sales.get(created.id) == cancelled
    with pytest.raises(ResourceCancelled):
        service.update(created.id, data)
