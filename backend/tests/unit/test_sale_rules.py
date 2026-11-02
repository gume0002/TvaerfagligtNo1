"""T033: sale rules reject invalid domain inputs before any write."""
from dataclasses import replace
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from app.business.models import SaleInput, ValidationFailed
from app.business.sale_service import SaleService


@pytest.mark.parametrize('changes,field', [
    ({'quantity': 0}, 'quantity'), ({'quantity': -1}, 'quantity'),
    ({'quantity': 1.5}, 'quantity'), ({'quantity': True}, 'quantity'),
    ({'unit_price': Decimal('0')}, 'unitPrice'),
    ({'unit_price': Decimal('-1')}, 'unitPrice'),
    ({'unit_price': Decimal('1.001')}, 'unitPrice'),
    ({'unit_price': Decimal('NaN')}, 'unitPrice'),
    ({'sale_date': date(2026, 10, 30)}, 'saleDate'),
])
def test_invalid_sale_never_opens_transaction(frozen_clock, changes, field):
    factory = Mock()
    service = SaleService(factory, frozen_clock)
    data = SaleInput(1, 1, 3, Decimal('100.00'), date(2026, 10, 29))
    with pytest.raises(ValidationFailed) as error:
        service.create(replace(data, **changes), Mock())
    assert field in {item.field for item in error.value.field_errors}
    factory.assert_not_called()
