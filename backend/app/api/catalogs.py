"""HTTP route for the catalogs."""

from fastapi import APIRouter, Request

from app.api.schemas import catalogs_json

router = APIRouter()


@router.get("/api/catalogs")
def get_catalogs(request: Request):
    return catalogs_json(request.app.state.catalog_service.get_catalogs())
