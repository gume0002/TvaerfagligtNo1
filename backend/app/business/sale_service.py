"""Bar sale rules and atomic, idempotent creation."""

import hashlib
import json
from dataclasses import asdict
from datetime import date, datetime
from decimal import Decimal

from app.business.models import (
    Clock, DrinkCategory, DuplicateIdempotencyKey, FieldError, IdempotencyConflict,
    IdempotencyContext, NewBarSale, ResourceStatus, RetryableTransactionError,
    Sale, SaleInput, StoredIdempotentResult, TemporarilyUnavailable, ValidationFailed,
)
from app.business.ports import UnitOfWorkFactory
from app.business.rules import EARLIEST_DATE, amount_errors


def _snapshot(sale: Sale) -> dict:
    values = asdict(sale)
    for name in ('sale_date', 'created_at', 'updated_at', 'cancelled_at'):
        values[name] = values[name].isoformat() if values[name] else None
    values['unit_price'] = str(sale.unit_price)
    return values


def _restore(values: dict) -> Sale:
    values = dict(values)
    values['sale_date'] = date.fromisoformat(values['sale_date'])
    for name in ('created_at', 'updated_at', 'cancelled_at'):
        values[name] = datetime.fromisoformat(values[name]) if values[name] else None
    values['unit_price'] = Decimal(values['unit_price'])
    values['category'] = DrinkCategory(values['category'])
    values['status'] = ResourceStatus(values['status'])
    return Sale(**values)


class SaleService:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock):
        self._uow_factory = uow_factory
        self._clock = clock

    def _validate(self, data: SaleInput) -> None:
        errors = amount_errors('unitPrice', data.unit_price)
        if type(data.quantity) is not int or data.quantity < 1:
            errors.append(FieldError('quantity', 'Antal skal være et positivt heltal.'))
        if data.sale_date < EARLIEST_DATE or data.sale_date > self._clock.business_date():
            errors.append(FieldError('saleDate', 'Salgsdatoen skal være gyldig og må højst være dags dato.'))
        if errors:
            raise ValidationFailed('Salget kunne ikke gemmes.', errors)

    @staticmethod
    def _references(uow, data):
        catalogs = uow.catalogs.get_all()
        errors = []
        if not any(item.id == data.drink_id for item in catalogs.drinks):
            errors.append(FieldError('drinkId', 'Drikken findes ikke.'))
        if not any(item.id == data.employee_id for item in catalogs.employees):
            errors.append(FieldError('employeeId', 'Medarbejderen findes ikke.'))
        if errors:
            raise ValidationFailed('Salget kunne ikke gemmes.', errors)

    @staticmethod
    def _with_retry(operation):
        for _attempt in range(3):
            try:
                return operation()
            except (RetryableTransactionError, DuplicateIdempotencyKey):
                continue
        raise TemporarilyUnavailable('Salget kunne ikke gemmes lige nu. Prøv igen.')

    def create(self, data: SaleInput, context: IdempotencyContext) -> Sale:
        self._validate(data)
        payload = asdict(data) | {'unit_price': format(data.unit_price, '.2f'), 'sale_date': data.sale_date.isoformat()}
        payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

        def save():
            with self._uow_factory() as uow:
                stored = uow.idempotency.find(context)
                if stored:
                    if stored.payload_hash != payload_hash:
                        raise IdempotencyConflict('Idempotency-Key er allerede brugt til et andet salg.')
                    return _restore(stored.response_body)
                self._references(uow, data)
                now = self._clock.now_utc()
                sale = uow.sales.add(NewBarSale(**asdict(data), status=ResourceStatus.ACTIVE, demo_data=False, created_at=now))
                uow.idempotency.save(context, StoredIdempotentResult(payload_hash, 201, _snapshot(sale)), now)
                uow.commit()
                return sale

        return self._with_retry(save)
