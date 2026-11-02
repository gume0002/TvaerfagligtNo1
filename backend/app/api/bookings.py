"""HTTP routes for bookings. Translates between JSON and the booking service."""

from typing import Annotated

from fastapi import APIRouter, Header, Path, Query, Request, Response
from fastapi.responses import JSONResponse

from app.api.schemas import BookingBody, IsoDate, booking_json
from app.business.booking_service import BookingService
from app.business.models import BookingSearch, IdempotencyContext, StatusFilter

COLLECTION_PATH = "/api/bookings"

router = APIRouter()
ResourceId = Annotated[int, Path(ge=1)]


def _service(request: Request) -> BookingService:
    return request.app.state.booking_service


@router.get(COLLECTION_PATH)
def list_bookings(
    request: Request,
    name: str | None = None,
    arrival_from: Annotated[IsoDate | None, Query(alias="arrivalFrom")] = None,
    departure_to: Annotated[IsoDate | None, Query(alias="departureTo")] = None,
    status: StatusFilter = StatusFilter.ACTIVE,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
):
    page = _service(request).search(
        BookingSearch(
            name=name,
            arrival_from=arrival_from,
            departure_to=departure_to,
            status=status,
            offset=offset,
            limit=limit,
        )
    )
    return {"items": [booking_json(item) for item in page.items], "total": page.total}


@router.post(COLLECTION_PATH, status_code=201)
def create_booking(
    request: Request,
    body: BookingBody,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
):
    booking = _service(request).create(
        body.to_domain(),
        IdempotencyContext(http_method="POST", path=COLLECTION_PATH, key=idempotency_key),
    )
    return JSONResponse(
        status_code=201,
        content=booking_json(booking),
        headers={"Location": f"{COLLECTION_PATH}/{booking.id}"},
    )


@router.get(f"{COLLECTION_PATH}/{{booking_id}}")
def get_booking(
    request: Request,
    booking_id: ResourceId,
    include_cancelled: Annotated[bool, Query(alias="includeCancelled")] = False,
):
    return booking_json(_service(request).get(booking_id, include_cancelled))


@router.put(f"{COLLECTION_PATH}/{{booking_id}}")
def update_booking(request: Request, booking_id: ResourceId, body: BookingBody):
    return booking_json(_service(request).update(booking_id, body.to_domain()))


@router.delete(f"{COLLECTION_PATH}/{{booking_id}}", status_code=204)
def cancel_booking(request: Request, booking_id: ResourceId):
    _service(request).cancel(booking_id)
    return Response(status_code=204)
