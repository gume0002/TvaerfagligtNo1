"""T043/T045/T047/T048: hand-calculated hotel analytics through all three layers."""
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from testsupport.contract import assert_matches_contract

HOTEL = '/api/analytics/hotel'
BAR = '/api/analytics/bar'


@pytest.fixture()
def client(settings, frozen_clock, catalog):
    with TestClient(create_app(settings, frozen_clock), raise_server_exceptions=False) as client:
        yield client


def hotel(client, **params):
    response = client.get(HOTEL, params=params)
    assert_matches_contract(response, 'GET', HOTEL)
    assert response.status_code == 200, response.text
    return response.json()


def create_booking(client, catalog, **changes):
    payload = dict(guestName='Test', countryId=catalog.sweden, roomTypeId=catalog.large,
        arrival='2026-06-10', departure='2026-06-13', guestCount=2, nightlyRate='1000.00') | changes
    response = client.post('/api/bookings', json=payload, headers={'Idempotency-Key': str(uuid4())})
    assert_matches_contract(response, 'POST', '/api/bookings')
    assert response.status_code == 201, response.text
    return response.json()


def cancel_booking(client, id):
    response = client.delete(f'/api/bookings/{id}')
    assert_matches_contract(response, 'DELETE', '/api/bookings/{id}')
    assert response.status_code == 204


def test_us7_1_year_boundary(client, catalog):
    create_booking(client, catalog, arrival='2025-12-30', departure='2026-01-02')
    assert hotel(client, year=2025)['totals']['all']['revenue'] == '2000.00'
    assert hotel(client, year=2026)['totals']['all']['revenue'] == '1000.00'


def test_us7_3_guests_and_revenue(client, catalog):
    create_booking(client, catalog)
    data = hotel(client, year=2026)
    assert data['totals']['all']['revenue'] == '3000.00'
    assert data['totals']['all']['bookedRoomNights'] == 3
    assert data['guestStaysByCountry'] == [{'countryId': catalog.sweden, 'countryName': 'Sweden', 'guestStays': 2}]
    assert data['byCountry'][0]['revenue'] == '3000.00'
    assert data['generatedAt'] == '2026-10-29T10:00:00Z'
    assert data['businessDate'] == '2026-10-29'


def test_us7_5_season_type_breakdown_and_combined_filters(client, catalog):
    create_booking(client, catalog, arrival='2026-02-28', departure='2026-03-02')
    create_booking(client, catalog, countryId=catalog.germany, roomTypeId=catalog.double)
    data = hotel(client, year=2026, roomTypeId=catalog.large, countryId=catalog.sweden)
    assert data['byRoomTypeAndSeason'] == [
        {'roomTypeId': catalog.large, 'roomTypeName': 'Large Suite', 'season': 'low', 'revenue': '1000.00'},
        {'roomTypeId': catalog.large, 'roomTypeName': 'Large Suite', 'season': 'mid', 'revenue': '1000.00'}]
    low = hotel(client, year=2026, season='low', roomTypeId=catalog.large, countryId=catalog.sweden)
    assert low['totals']['all']['revenue'] == '1000.00'
    assert low['totals']['all']['availableRoomNights'] == 295
    assert low['occupancyScope'] == 'country_contribution'
    assert low['filters'] == {'year': 2026, 'season': 'low', 'countryId': catalog.sweden, 'roomTypeId': catalog.large}


def test_us7_2_tied_firsts_and_next_is_third(client, catalog, engine):
    from sqlalchemy.orm import Session
    from app.data_access.orm_models import CountryRow
    with Session(engine, expire_on_commit=False) as session:
        third = CountryRow(code='DK', name='Denmark'); session.add(third); session.commit(); third_id = third.id
    create_booking(client, catalog, roomTypeId=catalog.tiny)
    create_booking(client, catalog, roomTypeId=catalog.double, countryId=catalog.germany)
    create_booking(client, catalog, roomTypeId=catalog.large, countryId=third_id, departure='2026-06-12')
    data = hotel(client, year=2026)
    assert [r['rank'] for r in data['topRoomTypes']] == [1, 1, 3]
    assert [r['rank'] for r in data['topCountries']] == [1, 1, 3]
    assert [r['revenue'] for r in data['topCountries']] == ['3000.00', '3000.00', '2000.00']


def test_us4_2_cancelled_booking_contributes_nothing(client, catalog):
    sale = create_booking(client, catalog)
    assert hotel(client)['totals']['all']['revenue'] == '3000.00'
    cancel_booking(client, sale['id'])
    data = hotel(client)
    assert data['totals']['all']['revenue'] == '0.00'
    assert data['totals']['all']['bookedRoomNights'] == 0
    for key in ['guestStaysByCountry', 'byCountry', 'byRoomTypeAndSeason', 'topCountries', 'topRoomTypes']:
        assert data[key] == []


def test_us8_2_leap_year(client, catalog):
    data = hotel(client, year=2024, roomTypeId=catalog.tiny)
    assert data['totals']['all']['availableRoomNights'] == 366
    create_booking(client, catalog, arrival='2024-02-28', departure='2024-03-01')
    assert hotel(client, year=2024, season='low')['totals']['all']['revenue'] == '2000.00'


def test_us8_3_no_data_and_country_denominator(client, catalog):
    data = hotel(client, year=2026, countryId=catalog.sweden, roomTypeId=catalog.double)
    assert data['totals']['all']['availableRoomNights'] == 730
    assert data['totals']['all']['adr'] is None
    assert data['totals']['all']['adrStatus'] == 'no_data'
    assert data['totals']['all']['occupancyRatePercent'] == '0.00'
    assert data['satisfaction'] == {'status': 'no_data'}
    assert data['occupancyScope'] == 'country_contribution'
    create_booking(client, catalog, arrival='2026-01-01', departure='2026-01-03', roomTypeId=catalog.double)
    assert hotel(client, year=2026, countryId=catalog.sweden, roomTypeId=catalog.double)['totals']['all']['availableRoomNights'] == 730
    other = hotel(client, year=2026, countryId=catalog.germany, roomTypeId=catalog.double)
    assert other['totals']['all']['availableRoomNights'] == 730
    assert other['totals']['all']['bookedRoomNights'] == 0


def test_us8_2_past_and_upcoming_use_frozen_business_date(client, catalog):
    create_booking(client, catalog, arrival='2026-10-28', departure='2026-10-31')
    data = hotel(client, year=2026, roomTypeId=catalog.large)
    assert data['totals']['past']['revenue'] == '1000.00'
    assert data['totals']['upcoming']['revenue'] == '2000.00'
    assert data['totals']['all']['revenue'] == '3000.00'
    assert data['totals']['past']['availableRoomNights'] == 1505
    assert data['totals']['upcoming']['availableRoomNights'] == 320
    assert data['totals']['all']['availableRoomNights'] == 1825
    assert data['totals']['upcoming']['adr'] == '1000.00'


@pytest.mark.parametrize('params', [{'year': 1999}, {'year': 2101}, {'year': 'wrong'}, {'season': 'wrong'},
    {'countryId': 0}, {'roomTypeId': 0}, {'countryId': 9999}, {'roomTypeId': 9999}])
def test_invalid_hotel_filters(client, params):
    response = client.get(HOTEL, params=params)
    assert_matches_contract(response, 'GET', HOTEL)
    assert response.status_code == 400


def bar(client, **params):
    response = client.get(BAR, params=params)
    assert_matches_contract(response, 'GET', BAR)
    assert response.status_code == 200, response.text
    return response.json()


def create_sale(client, **changes):
    values = dict(drinkId=1, employeeId=1, quantity=3, unitPrice='100.00', saleDate='2026-10-29') | changes
    response = client.post('/api/bar-sales', json=values, headers={'Idempotency-Key': str(uuid4())})
    assert_matches_contract(response, 'POST', '/api/bar-sales')
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture()
def extra_bar_catalog(engine, catalog):
    from decimal import Decimal
    from sqlalchemy.orm import Session
    from app.data_access.orm_models import DrinkRow, EmployeeRow
    with Session(engine, expire_on_commit=False) as session:
        coffee = DrinkRow(name='Coffee', category='coffee', suggested_unit_price=Decimal('50.00'))
        other = EmployeeRow(code='other', name='Demo employee')
        session.add_all([coffee, other]); session.commit()
        return coffee.id, other.id


def test_us9_1_bar_amounts_categories_and_drinks(client, extra_bar_catalog):
    coffee, _ = extra_bar_catalog
    create_sale(client)
    create_sale(client, drinkId=coffee, quantity=2, unitPrice='50.00')
    data = bar(client)
    assert data['filters'] == {'year': 2026, 'employeeId': 1, 'employeeName': 'Helene Christine'}
    assert data['totals'] == {'quantity': 5, 'revenue': '400.00'}
    assert data['byDrink'] == [
        {'drinkId': 1, 'drinkName': 'Negroni', 'category': 'cocktail', 'quantity': 3, 'revenue': '300.00'},
        {'drinkId': coffee, 'drinkName': 'Coffee', 'category': 'coffee', 'quantity': 2, 'revenue': '100.00'}]
    assert data['byCategory'] == [
        {'category': 'cocktail', 'quantity': 3, 'revenue': '300.00', 'quantitySharePercent': '60.00', 'revenueSharePercent': '75.00', 'shareStatus': 'ok'},
        {'category': 'coffee', 'quantity': 2, 'revenue': '100.00', 'quantitySharePercent': '40.00', 'revenueSharePercent': '25.00', 'shareStatus': 'ok'}]


def test_us9_2_year_employee_and_us6_2_cancelled_excluded(client, extra_bar_catalog):
    _, other = extra_bar_catalog
    create_sale(client, saleDate='2025-10-01', quantity=7)
    create_sale(client, employeeId=other, quantity=9)
    sale = create_sale(client)
    assert bar(client)['totals'] == {'quantity': 3, 'revenue': '300.00'}
    assert bar(client, year=2025)['totals'] == {'quantity': 7, 'revenue': '700.00'}
    assert bar(client, employeeId=other)['totals'] == {'quantity': 9, 'revenue': '900.00'}
    response = client.put(f"/api/bar-sales/{sale['id']}", json={'drinkId': 1, 'employeeId': 1, 'quantity': 2, 'unitPrice': '100.00', 'saleDate': '2026-10-29'})
    assert_matches_contract(response, 'PUT', '/api/bar-sales/{id}')
    assert response.status_code == 200
    assert bar(client)['totals'] == {'quantity': 2, 'revenue': '200.00'}
    response = client.delete(f"/api/bar-sales/{sale['id']}")
    assert_matches_contract(response, 'DELETE', '/api/bar-sales/{id}')
    assert response.status_code == 204
    data = bar(client)
    assert data['totals'] == {'quantity': 0, 'revenue': '0.00'}
    assert all(item['revenue'] == '0.00' and item['quantity'] == 0 for item in data['byDrink'])
    assert all(item['quantitySharePercent'] is None and item['revenueSharePercent'] is None and item['shareStatus'] == 'no_data' for item in data['byCategory'])


def test_us9_3_no_sales(client):
    data = bar(client)
    assert data['totals'] == {'quantity': 0, 'revenue': '0.00'}
    assert {item['category'] for item in data['byCategory']} == {'cocktail', 'coffee'}
    assert data['byDrink'][0]['revenue'] == '0.00'
    assert data['byDrink'][0]['quantity'] == 0


@pytest.mark.parametrize('params', [{'year': 1999}, {'year': 2101}, {'year': 'wrong'}, {'employeeId': 0}, {'employeeId': 9999}])
def test_invalid_bar_filters(client, params):
    response = client.get(BAR, params=params)
    assert_matches_contract(response, 'GET', BAR)
    assert response.status_code == 400


def test_us9_4_seed_catalog_includes_twenty_cocktails_ten_coffees(settings, frozen_clock, uow_factory, empty_database):
    import os
    from pathlib import Path
    from app.business.seed_service import SeedService
    from app.data_access.raw_files import read_raw_data
    SeedService(uow_factory, frozen_clock).run(read_raw_data(Path(os.environ['RAW_DATA_DIR'])))
    with TestClient(create_app(settings, frozen_clock)) as seeded_client:
        data = bar(seeded_client, year=2000)
    assert len(data['byDrink']) == 30
    assert sum(item['category'] == 'cocktail' for item in data['byDrink']) == 20
    assert sum(item['category'] == 'coffee' for item in data['byDrink']) == 10
    assert len({item['drinkName'] for item in data['byDrink']}) == 30
    assert all(item['quantity'] == 0 and item['revenue'] == '0.00' for item in data['byDrink'])
    assert data['totals'] == {'quantity': 0, 'revenue': '0.00'}


def test_contract_assertion_rejects_wrong_metric_type(client):
    import httpx
    data = hotel(client)
    data['totals']['all']['revenue'] = 0
    malformed = httpx.Response(200, json=data)
    with pytest.raises(AssertionError, match='revenue'):
        assert_matches_contract(malformed, 'GET', HOTEL)


@pytest.mark.parametrize('path', [HOTEL, BAR])
def test_lost_database_is_503(settings, frozen_clock, path):
    from dataclasses import replace
    broken = replace(settings, database_host='host-that-does-not-exist')
    with TestClient(create_app(broken, frozen_clock), raise_server_exceptions=False) as broken_client:
        response = broken_client.get(path)
    assert_matches_contract(response, 'GET', path)
    assert response.status_code == 503
    assert 'sql' not in response.text.lower()
    assert response.headers['Retry-After']
