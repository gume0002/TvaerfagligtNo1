"""HTTP transport for bar sales."""
from typing import Annotated

from fastapi import APIRouter, Header, Request, Query, Path, Response
from fastapi.responses import JSONResponse

from app.api.schemas import SaleBody, sale_json, IsoDate
from app.business.models import IdempotencyContext, SaleSearch, StatusFilter

COLLECTION_PATH = '/api/bar-sales'
router = APIRouter()


@router.post(COLLECTION_PATH, status_code=201)
def create_sale(request: Request, body: SaleBody,
                idempotency_key: Annotated[str, Header(alias='Idempotency-Key', min_length=1, max_length=128)]):
    sale = request.app.state.sale_service.create(
        body.to_domain(), IdempotencyContext('POST', COLLECTION_PATH, idempotency_key))
    return JSONResponse(status_code=201, content=sale_json(sale), headers={'Location': f'{COLLECTION_PATH}/{sale.id}'})


@router.get(COLLECTION_PATH)
def list_sales(
    request: Request,
    sale_date_from: Annotated[IsoDate | None, Query(alias='saleDateFrom')] = None,
    sale_date_to: Annotated[IsoDate | None, Query(alias='saleDateTo')] = None,
    employee_id: Annotated[int | None, Query(alias='employeeId', ge=1)] = None,
    status: StatusFilter = StatusFilter.ACTIVE,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
):
    items, total = request.app.state.sale_service.search(SaleSearch(sale_date_from, sale_date_to, employee_id, status, offset, limit))
    return {'items': [sale_json(item) for item in items], 'total': total}


@router.get(f'{COLLECTION_PATH}/{{id}}')
def get_sale(request: Request, id: Annotated[int, Path(ge=1)],
             include_cancelled: Annotated[bool, Query(alias='includeCancelled')] = False):
    return sale_json(request.app.state.sale_service.get(id, include_cancelled))


@router.put(f'{COLLECTION_PATH}/{{id}}')
def update_sale(request: Request, id: Annotated[int, Path(ge=1)], body: SaleBody):
    return sale_json(request.app.state.sale_service.update(id, body.to_domain()))


@router.delete(f'{COLLECTION_PATH}/{{id}}', status_code=204)
def cancel_sale(request: Request, id: Annotated[int, Path(ge=1)]):
    request.app.state.sale_service.cancel(id)
    return Response(status_code=204)
