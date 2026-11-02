"""Contract-defined analytics transport. All numbers come from business."""
from typing import Annotated

from fastapi import APIRouter, Query, Request

from app.api.schemas import analytics_json
from app.business.models import Season

router = APIRouter()
Year = Annotated[int | None, Query(ge=2000, le=2100)]


@router.get('/api/analytics/hotel')
def hotel(request: Request, year: Year = None, season: Season | None = None,
          country_id: Annotated[int | None, Query(alias='countryId', ge=1)] = None,
          room_type_id: Annotated[int | None, Query(alias='roomTypeId', ge=1)] = None):
    return analytics_json(request.app.state.analytics_service.hotel(year, season, country_id, room_type_id))
