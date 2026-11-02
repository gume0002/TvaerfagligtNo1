"""OData V4 transport for Tableau: a read-only view of the business layer's results.

This module only knows the protocol. It holds no SQL, no business rules and no
calculations, and it renders decimals as exact JSON numbers.
"""

import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from fastapi import APIRouter, Request, Response

from app.api.schemas import timestamp

ROOT = '/api/odata'
NAMESPACE = 'HotelKongArthur.Feed'
JSON_MEDIA_TYPE = 'application/json;odata.metadata=minimal;charset=utf-8'
ODATA_HEADERS = {'OData-Version': '4.0'}

INT, TEXT, BOOL, DECIMAL, DATE, TIMESTAMP = (
    'Edm.Int32', 'Edm.String', 'Edm.Boolean', 'Edm.Decimal', 'Edm.Date', 'Edm.DateTimeOffset',
)
HOTEL_FILTERS = [('year', INT), ('seasonFilter', TEXT), ('countryFilter', TEXT), ('roomTypeFilter', TEXT)]
BAR_FILTERS = [('year', INT), ('employee', TEXT)]
METADATA = [('demoData', BOOL), ('generatedAt', TIMESTAMP)]
NULLABLE = {'occupancyRatePercent', 'adr', 'quantitySharePercent', 'revenueSharePercent'}

ENTITY_SETS = {
    'HotelTotals': ('hotel_totals', HOTEL_FILTERS + [
        ('period', TEXT), ('revenue', DECIMAL), ('bookedRoomNights', INT), ('availableRoomNights', INT),
        ('occupancyRatePercent', DECIMAL), ('occupancyStatus', TEXT), ('adr', DECIMAL), ('adrStatus', TEXT),
        ('occupancyScope', TEXT), ('satisfactionStatus', TEXT), ('businessDate', DATE),
    ] + METADATA),
    'HotelRoomTypeSeason': ('hotel_room_type_season', HOTEL_FILTERS + [
        ('roomType', TEXT), ('season', TEXT), ('revenue', DECIMAL),
    ] + METADATA),
    'HotelCountries': ('hotel_countries', HOTEL_FILTERS + [
        ('country', TEXT), ('revenue', DECIMAL), ('revenueRank', INT), ('guestStays', INT),
    ] + METADATA),
    'HotelRoomTypeRanks': ('hotel_room_type_ranks', HOTEL_FILTERS + [
        ('roomType', TEXT), ('revenue', DECIMAL), ('revenueRank', INT),
    ] + METADATA),
    'BarTotals': ('bar_totals', BAR_FILTERS + [('quantity', INT), ('revenue', DECIMAL)] + METADATA),
    'BarDrinks': ('bar_drinks', BAR_FILTERS + [
        ('drink', TEXT), ('category', TEXT), ('quantity', INT), ('revenue', DECIMAL),
    ] + METADATA),
    'BarCategories': ('bar_categories', BAR_FILTERS + [
        ('category', TEXT), ('quantity', INT), ('revenue', DECIMAL), ('quantitySharePercent', DECIMAL),
        ('revenueSharePercent', DECIMAL), ('shareStatus', TEXT),
    ] + METADATA),
}

router = APIRouter()


def _base_url(request: Request) -> str:
    return f'{request.url.scheme}://{request.headers.get("host", request.url.netloc)}{ROOT}'


def _render(value) -> str:
    if isinstance(value, Decimal):
        return format(value, '.2f')
    if isinstance(value, datetime):
        return json.dumps(timestamp(value))
    if isinstance(value, date):
        return json.dumps(value.isoformat())
    if isinstance(value, Enum):
        return json.dumps(value.value)
    return json.dumps(value, ensure_ascii=False)


def _render_row(row_id: int, row: dict, fields) -> str:
    values = [f'"id":{row_id}']
    values.extend(f'{json.dumps(name)}:{_render(row[name])}' for name, _ in fields)
    return '{' + ','.join(values) + '}'


def _metadata_xml() -> str:
    types = []
    sets = []
    for name, (_, fields) in ENTITY_SETS.items():
        properties = ['<Property Name="id" Type="Edm.Int32" Nullable="false"/>']
        for field, edm_type in fields:
            precision = ' Precision="12" Scale="2"' if edm_type == DECIMAL else ''
            nullable = str(field in NULLABLE).lower()
            properties.append(f'<Property Name="{field}" Type="{edm_type}" Nullable="{nullable}"{precision}/>')
        types.append(f'<EntityType Name="{name}Row"><Key><PropertyRef Name="id"/></Key>{"".join(properties)}</EntityType>')
        sets.append(f'<EntitySet Name="{name}" EntityType="{NAMESPACE}.{name}Row"/>')
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<edmx:Edmx Version="4.0" xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx"><edmx:DataServices>'
        f'<Schema Namespace="{NAMESPACE}" xmlns="http://docs.oasis-open.org/odata/ns/edm">{"".join(types)}'
        f'<EntityContainer Name="Container">{"".join(sets)}</EntityContainer></Schema>'
        '</edmx:DataServices></edmx:Edmx>'
    )


@router.get(f'{ROOT}/')
def service_document(request: Request):
    body = {
        '@odata.context': f'{_base_url(request)}/$metadata',
        'value': [{'name': name, 'kind': 'EntitySet', 'url': name} for name in ENTITY_SETS],
    }
    return Response(json.dumps(body), media_type=JSON_MEDIA_TYPE, headers=ODATA_HEADERS)


@router.get(f'{ROOT}/$metadata')
def metadata():
    return Response(_metadata_xml(), media_type='application/xml;charset=utf-8', headers=ODATA_HEADERS)


def _add_entity_set_route(name: str, method: str, fields) -> None:
    def entity_set(request: Request):
        rows = getattr(request.app.state.analytics_feed_service, method)()
        items = ','.join(_render_row(row_id, row, fields) for row_id, row in enumerate(rows, start=1))
        context = json.dumps(f'{_base_url(request)}/$metadata#{name}')
        return Response(f'{{"@odata.context":{context},"value":[{items}]}}', media_type=JSON_MEDIA_TYPE, headers=ODATA_HEADERS)

    router.add_api_route(f'{ROOT}/{name}', entity_set, methods=['GET'], name=f'odata_{name}')


for _name, (_method, _fields) in ENTITY_SETS.items():
    _add_entity_set_route(_name, _method, _fields)
