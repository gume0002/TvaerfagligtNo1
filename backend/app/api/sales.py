"""HTTP transport for bar sales."""
from typing import Annotated

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from app.api.schemas import SaleBody, sale_json
from app.business.models import IdempotencyContext

COLLECTION_PATH = '/api/bar-sales'
router = APIRouter()


@router.post(COLLECTION_PATH, status_code=201)
def create_sale(request: Request, body: SaleBody,
                idempotency_key: Annotated[str, Header(alias='Idempotency-Key', min_length=1, max_length=128)]):
    sale = request.app.state.sale_service.create(
        body.to_domain(), IdempotencyContext('POST', COLLECTION_PATH, idempotency_key))
    return JSONResponse(status_code=201, content=sale_json(sale), headers={'Location': f'{COLLECTION_PATH}/{sale.id}'})
