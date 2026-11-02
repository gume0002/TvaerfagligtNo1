"""Booking rules: create, find, change and cancel."""

import hashlib
import json
from collections.abc import Callable
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from typing import TypeVar

from app.business.models import (
    Booking,
    BookingInput,
    BookingPage,
    BookingSearch,
    CapacityConflict,
    Clock,
    DuplicateIdempotencyKey,
    FieldError,
    IdempotencyConflict,
    IdempotencyContext,
    NewBooking,
    ResourceCancelled,
    ResourceNotFound,
    ResourceStatus,
    RetryableTransactionError,
    RoomType,
    StoredIdempotentResult,
    TemporarilyUnavailable,
    ValidationFailed,
)
from app.business.ports import UnitOfWork, UnitOfWorkFactory
from app.business.rules import EARLIEST_DATE, amount_errors, first_overbooked_night

MAX_TRANSACTION_ATTEMPTS = 3
GUEST_NAME_MAX_LENGTH = 200
INVALID_BOOKING_MESSAGE = "Bookingen kunne ikke gemmes."
NOT_FOUND_MESSAGE = "Bookingen blev ikke fundet."

T = TypeVar("T")


def _booking_to_snapshot(booking: Booking) -> dict:
    return {
        "id": booking.id,
        "guest_name": booking.guest_name,
        "country_id": booking.country_id,
        "country_name": booking.country_name,
        "room_type_id": booking.room_type_id,
        "room_type_name": booking.room_type_name,
        "arrival": booking.arrival.isoformat(),
        "departure": booking.departure.isoformat(),
        "guest_count": booking.guest_count,
        "nightly_rate": str(booking.nightly_rate),
        "status": booking.status.value,
        "demo_data": booking.demo_data,
        "created_at": booking.created_at.isoformat(),
        "updated_at": booking.updated_at.isoformat(),
        "cancelled_at": booking.cancelled_at.isoformat() if booking.cancelled_at else None,
    }


def _booking_from_snapshot(snapshot: dict) -> Booking:
    return Booking(
        id=snapshot["id"],
        guest_name=snapshot["guest_name"],
        country_id=snapshot["country_id"],
        country_name=snapshot["country_name"],
        room_type_id=snapshot["room_type_id"],
        room_type_name=snapshot["room_type_name"],
        arrival=date.fromisoformat(snapshot["arrival"]),
        departure=date.fromisoformat(snapshot["departure"]),
        guest_count=snapshot["guest_count"],
        nightly_rate=Decimal(snapshot["nightly_rate"]),
        status=ResourceStatus(snapshot["status"]),
        demo_data=snapshot["demo_data"],
        created_at=datetime.fromisoformat(snapshot["created_at"]),
        updated_at=datetime.fromisoformat(snapshot["updated_at"]),
        cancelled_at=datetime.fromisoformat(snapshot["cancelled_at"]) if snapshot["cancelled_at"] else None,
    )


def _payload_hash(data: BookingInput) -> str:
    """Hash the meaning of the input, so "1000" and "1000.00" count as the same."""
    payload = {
        "guest_name": data.guest_name,
        "country_id": data.country_id,
        "room_type_id": data.room_type_id,
        "arrival": data.arrival.isoformat(),
        "departure": data.departure.isoformat(),
        "guest_count": data.guest_count,
        "nightly_rate": format(data.nightly_rate, ".2f"),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


class BookingService:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock):
        self._uow_factory = uow_factory
        self._clock = clock

    def create(self, data: BookingInput, idempotency: IdempotencyContext) -> Booking:
        data = self._validated_fields(data)
        payload_hash = _payload_hash(data)
        return self._with_retry(lambda: self._create_once(data, idempotency, payload_hash))

    def search(self, search: BookingSearch) -> BookingPage:
        errors = []
        if (search.arrival_from is None) != (search.departure_to is None):
            field = "departureTo" if search.departure_to is None else "arrivalFrom"
            errors.append(FieldError(field, "Angiv både start og slut på opholdsintervallet."))
        elif search.arrival_from is not None and search.departure_to <= search.arrival_from:
            errors.append(FieldError("departureTo", "Slutdatoen skal ligge efter startdatoen."))
        if errors:
            raise ValidationFailed("Filtrene er ugyldige.", errors)

        name = search.name.strip() if search.name else None
        with self._uow_factory() as uow:
            items, total = uow.bookings.search(replace(search, name=name or None))
        return BookingPage(items=items, total=total)

    def get(self, booking_id: int, include_cancelled: bool = False) -> Booking:
        with self._uow_factory() as uow:
            booking = uow.bookings.get(booking_id)
        if booking is None or (booking.status is ResourceStatus.CANCELLED and not include_cancelled):
            raise ResourceNotFound(NOT_FOUND_MESSAGE)
        return booking

    def update(self, booking_id: int, data: BookingInput) -> Booking:
        data = self._validated_fields(data)
        return self._with_retry(lambda: self._update_once(booking_id, data))

    def cancel(self, booking_id: int) -> None:
        self._with_retry(lambda: self._cancel_once(booking_id))

    def _create_once(self, data: BookingInput, idempotency: IdempotencyContext, payload_hash: str) -> Booking:
        with self._uow_factory() as uow:
            replayed = self._replayed_booking(uow, idempotency, payload_hash)
            if replayed is not None:
                return replayed

            room_type = uow.catalogs.lock_room_type(data.room_type_id)

            # A request with the same key may have committed while this one waited.
            replayed = self._replayed_booking(uow, idempotency, payload_hash)
            if replayed is not None:
                return replayed

            self._check_references_and_guests(uow, data, room_type)
            self._check_capacity(uow, data, room_type, exclude_booking_id=None)

            now = self._clock.now_utc()
            booking = uow.bookings.add(
                NewBooking(data=data, status=ResourceStatus.ACTIVE, demo_data=False, created_at=now)
            )
            uow.idempotency.save(
                idempotency,
                StoredIdempotentResult(
                    payload_hash=payload_hash,
                    response_status=201,
                    response_body=_booking_to_snapshot(booking),
                ),
                now,
            )
            uow.commit()
            return booking

    def _update_once(self, booking_id: int, data: BookingInput) -> Booking:
        with self._uow_factory() as uow:
            current = uow.bookings.lock(booking_id)
            if current is None:
                raise ResourceNotFound(NOT_FOUND_MESSAGE)
            if current.status is ResourceStatus.CANCELLED:
                raise ResourceCancelled("En aflyst booking kan ikke rettes.")

            # Same order everywhere: booking first, then types by ascending id.
            locked_types = {
                room_type_id: uow.catalogs.lock_room_type(room_type_id)
                for room_type_id in sorted({current.room_type_id, data.room_type_id})
            }
            room_type = locked_types[data.room_type_id]
            self._check_references_and_guests(uow, data, room_type)
            self._check_capacity(uow, data, room_type, exclude_booking_id=booking_id)

            booking = uow.bookings.update(booking_id, data, self._clock.now_utc())
            uow.commit()
            return booking

    def _cancel_once(self, booking_id: int) -> None:
        with self._uow_factory() as uow:
            current = uow.bookings.lock(booking_id)
            if current is None:
                raise ResourceNotFound(NOT_FOUND_MESSAGE)
            if current.status is ResourceStatus.CANCELLED:
                return
            uow.catalogs.lock_room_type(current.room_type_id)
            uow.bookings.cancel(booking_id, self._clock.now_utc())
            uow.commit()

    @staticmethod
    def _replayed_booking(uow: UnitOfWork, idempotency: IdempotencyContext, payload_hash: str) -> Booking | None:
        stored = uow.idempotency.find(idempotency)
        if stored is None:
            return None
        if stored.payload_hash != payload_hash:
            raise IdempotencyConflict("Idempotency-Key er allerede brugt til en anden booking.")
        return _booking_from_snapshot(stored.response_body)

    @staticmethod
    def _validated_fields(data: BookingInput) -> BookingInput:
        """Check everything that does not need the database, and normalize the name."""
        name = data.guest_name.strip()
        errors = []
        if not name:
            errors.append(FieldError("guestName", "Gæstens navn skal udfyldes."))
        elif len(name) > GUEST_NAME_MAX_LENGTH:
            errors.append(FieldError("guestName", "Gæstens navn er for langt."))
        if data.arrival < EARLIEST_DATE:
            errors.append(FieldError("arrival", "Ankomstdatoen er ugyldig."))
        if data.departure <= data.arrival:
            errors.append(FieldError("departure", "Afrejse skal ligge efter ankomst."))
        if data.guest_count < 1:
            errors.append(FieldError("guestCount", "Antal gæster skal være mindst 1."))
        errors.extend(amount_errors("nightlyRate", data.nightly_rate))
        if errors:
            raise ValidationFailed(INVALID_BOOKING_MESSAGE, errors)
        return replace(data, guest_name=name)

    @staticmethod
    def _check_references_and_guests(uow: UnitOfWork, data: BookingInput, room_type: RoomType | None) -> None:
        errors = []
        if uow.catalogs.get_country(data.country_id) is None:
            errors.append(FieldError("countryId", "Landet findes ikke."))
        if room_type is None:
            errors.append(FieldError("roomTypeId", "Værelsestypen findes ikke."))
        elif data.guest_count > room_type.max_guests:
            errors.append(FieldError("guestCount", f"Værelsestypen har plads til højst {room_type.max_guests} gæster."))
        if errors:
            raise ValidationFailed(INVALID_BOOKING_MESSAGE, errors)

    @staticmethod
    def _check_capacity(uow: UnitOfWork, data: BookingInput, room_type: RoomType, exclude_booking_id: int | None) -> None:
        stays = uow.bookings.active_stays_overlapping(room_type.id, data.arrival, data.departure, exclude_booking_id)
        night = first_overbooked_night(data.arrival, data.departure, stays, room_type.room_count)
        if night is not None:
            raise CapacityConflict(f"{room_type.name} er fuldt booket natten til {night.isoformat()}.")

    @staticmethod
    def _with_retry(operation: Callable[[], T]) -> T:
        for _attempt in range(MAX_TRANSACTION_ATTEMPTS):
            try:
                return operation()
            except (RetryableTransactionError, DuplicateIdempotencyKey):
                continue
        raise TemporarilyUnavailable("Bookingen kunne ikke gemmes lige nu. Prøv igen.")
