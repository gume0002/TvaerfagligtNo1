"""SC-004: simultaneous requests against real MySQL with independent connections."""

from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from threading import Barrier

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.business.booking_service import BookingService
from app.business.models import BookingInput, BookingSearch, CapacityConflict, IdempotencyContext, RetryableTransactionError, StatusFilter, TemporarilyUnavailable
from app.data_access.orm_models import BookingRow

REPETITIONS = 20


def booking_input(room_type_id, country_id, arrival=date(2026, 6, 10), departure=date(2026, 6, 12), name="Gæst"):
    return BookingInput(
        guest_name=name,
        country_id=country_id,
        room_type_id=room_type_id,
        arrival=arrival,
        departure=departure,
        guest_count=1,
        nightly_rate=Decimal("1000.00"),
    )


def run_together(*operations):
    """Start all operations at the same moment and return their result or error."""
    barrier = Barrier(len(operations))

    def run(operation):
        barrier.wait()
        try:
            return operation()
        except Exception as error:  # noqa: BLE001 - the error is the result here
            return error

    with ThreadPoolExecutor(len(operations)) as executor:
        return list(executor.map(run, operations))


def active_count(engine, room_type_id):
    with Session(engine) as session:
        return session.scalar(
            select(func.count())
            .select_from(BookingRow)
            .where(BookingRow.room_type_id == room_type_id, BookingRow.status == "active")
        )


@pytest.fixture()
def service(uow_factory, frozen_clock):
    return BookingService(uow_factory, frozen_clock)


def test_engine_uses_read_committed_as_planned(engine):
    with engine.connect() as connection:
        assert connection.get_isolation_level() == "READ COMMITTED"


def test_two_requests_for_the_last_room_never_overbook(service, catalog, engine):
    for repetition in range(REPETITIONS):
        arrival = date(2026, 1, 1).replace(month=(repetition % 12) + 1, day=1)
        data = booking_input(catalog.tiny, catalog.sweden, arrival, arrival.replace(day=3))
        results = run_together(
            lambda: service.create(data, IdempotencyContext("POST", "/api/bookings", f"a-{repetition}")),
            lambda: service.create(data, IdempotencyContext("POST", "/api/bookings", f"b-{repetition}")),
        )
        conflicts = [result for result in results if isinstance(result, CapacityConflict)]
        created = [result for result in results if not isinstance(result, Exception)]
        assert len(conflicts) == 1 and len(created) == 1, results
        # Clear the months for the next repetition, also when the year wraps.
        service.cancel(created[0].id)
    assert active_count(engine, catalog.tiny) == 0


def test_many_requests_fill_exactly_the_capacity(service, catalog, engine):
    data = booking_input(catalog.large, catalog.sweden)
    operations = [
        (lambda number=number: service.create(data, IdempotencyContext("POST", "/api/bookings", f"k-{number}")))
        for number in range(12)
    ]
    results = run_together(*operations)
    created = [result for result in results if not isinstance(result, Exception)]
    errors = [result for result in results if isinstance(result, Exception)]
    assert len(created) == 5
    assert all(isinstance(error, CapacityConflict) for error in errors), errors
    assert active_count(engine, catalog.large) == 5


def test_same_key_at_the_same_time_creates_one_booking(service, catalog, engine):
    data = booking_input(catalog.large, catalog.sweden)
    context = IdempotencyContext("POST", "/api/bookings", "same-key")
    for _ in range(REPETITIONS):
        results = run_together(lambda: service.create(data, context), lambda: service.create(data, context))
        assert not any(isinstance(result, Exception) for result in results), results
        assert results[0].id == results[1].id
    assert active_count(engine, catalog.large) == 1


def test_two_updates_cannot_take_the_last_room_together(service, catalog, engine):
    context = lambda key: IdempotencyContext("POST", "/api/bookings", key)  # noqa: E731
    for repetition in range(REPETITIONS):
        first = service.create(booking_input(catalog.double, catalog.sweden), context(f"first-{repetition}"))
        second = service.create(booking_input(catalog.double, catalog.sweden), context(f"second-{repetition}"))
        target = booking_input(catalog.tiny, catalog.sweden)
        results = run_together(lambda: service.update(first.id, target), lambda: service.update(second.id, target))
        conflicts = [result for result in results if isinstance(result, CapacityConflict)]
        updated = [result for result in results if not isinstance(result, Exception)]
        assert len(conflicts) == 1 and len(updated) == 1, results
        assert active_count(engine, catalog.tiny) == 1
        service.cancel(first.id)
        service.cancel(second.id)


def test_opposite_type_changes_do_not_deadlock(service, catalog):
    context = lambda key: IdempotencyContext("POST", "/api/bookings", key)  # noqa: E731
    for repetition in range(REPETITIONS):
        arrival = date(2027, (repetition % 12) + 1, 1)
        departure = arrival.replace(day=3)
        in_large = service.create(booking_input(catalog.large, catalog.sweden, arrival, departure), context(f"l-{repetition}"))
        in_double = service.create(booking_input(catalog.double, catalog.sweden, arrival, departure), context(f"d-{repetition}"))
        results = run_together(
            lambda: service.update(in_large.id, booking_input(catalog.double, catalog.sweden, arrival, departure)),
            lambda: service.update(in_double.id, booking_input(catalog.large, catalog.sweden, arrival, departure)),
        )
        assert not any(isinstance(result, Exception) for result in results), results
        service.cancel(in_large.id)
        service.cancel(in_double.id)


def test_simultaneous_delete_and_create_keep_capacity_correct(service, catalog, engine):
    context = lambda key: IdempotencyContext("POST", "/api/bookings", key)  # noqa: E731
    data = booking_input(catalog.tiny, catalog.sweden)
    current = service.create(data, context("start"))
    for repetition in range(REPETITIONS):
        cancel_id = current.id
        results = run_together(
            lambda: service.cancel(cancel_id),
            lambda: service.create(data, context(f"new-{repetition}")),
        )
        assert active_count(engine, catalog.tiny) <= 1, results
        active = service.search(BookingSearch(status=StatusFilter.ACTIVE)).items
        current = active[0] if active else service.create(data, context(f"again-{repetition}"))


def test_lock_conflicts_are_retried_three_times_and_then_reported(frozen_clock):
    attempts = []

    class Conflicting:
        def __enter__(self):
            attempts.append(1)
            raise RetryableTransactionError()

        def __exit__(self, *_):
            return None

    service = BookingService(Conflicting, frozen_clock)
    with pytest.raises(TemporarilyUnavailable):
        service.cancel(1)
    assert len(attempts) == 3
