"""T034/T036/T040: HTTP sale behaviour and contract against MySQL."""
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from testsupport.contract import assert_matches_contract

COLLECTION = '/api/bar-sales'
ITEM = '/api/bar-sales/{id}'


@pytest.fixture()
def client(settings, frozen_clock, catalog):
    with TestClient(create_app(settings, frozen_clock), raise_server_exceptions=False) as client:
        yield client


def payload(**changes):
    return dict(drinkId=1, employeeId=1, quantity=3, unitPrice='100.00', saleDate='2026-10-29') | changes


def post(client, data=None, key=None):
    response = client.post(COLLECTION, json=data or payload(), headers={'Idempotency-Key': key or str(uuid4())})
    assert_matches_contract(response, 'POST', COLLECTION)
    return response


def test_us5_creation_and_replay(client):
    response = post(client, key='same')
    assert response.status_code == 201, response.text
    assert response.json()['totalAmount'] == '300.00'
    assert response.json()['quantity'] == 3
    assert response.headers['Location'] == f"{COLLECTION}/{response.json()['id']}"
    assert post(client, key='same').json() == response.json()
    assert post(client, payload(quantity=2), key='same').status_code == 409


@pytest.mark.parametrize('changes', [
    {'quantity': 0}, {'quantity': -1}, {'quantity': 1.5}, {'quantity': True},
    {'drinkId': 999}, {'employeeId': 999}, {'employeeId': None},
    {'unitPrice': '0'}, {'unitPrice': '-1'}, {'unitPrice': '1.001'},
    {'unitPrice': 100}, {'saleDate': '2026-10-30'}, {'saleDate': 'invalid'},
])
def test_us5_invalid_input(client, changes):
    assert post(client, payload(**changes)).status_code == 400


def call(client, method, sale_id=None, **kwargs):
    response = getattr(client, method)(f'{COLLECTION}/{sale_id}' if sale_id is not None else COLLECTION, **kwargs)
    assert_matches_contract(response, method, ITEM if sale_id is not None else COLLECTION)
    return response


def test_read_update_cancel_and_history(client, frozen_clock):
    from datetime import date
    sale = post(client).json()
    id = sale['id']
    assert call(client, 'get', id).json() == sale
    updated = call(client, 'put', id, json=payload(quantity=2))
    assert updated.status_code == 200
    assert updated.json()['totalAmount'] == '200.00'
    assert call(client, 'put', id, json=payload(drinkId=999)).status_code == 400
    assert call(client, 'get', id).json() == updated.json()
    assert call(client, 'delete', id).status_code == 204
    assert call(client, 'get', id).status_code == 404
    history = call(client, 'get', id, params={'includeCancelled': True}).json()
    assert history['status'] == 'cancelled'
    frozen_clock.today = date(2027, 1, 1)
    assert call(client, 'delete', id).status_code == 204
    assert call(client, 'get', id, params={'includeCancelled': True}).json() == history
    assert call(client, 'put', id, json=payload()).status_code == 409
    assert call(client, 'get').json() == {'items': [], 'total': 0}
    assert call(client, 'get', params={'status': 'cancelled'}).json()['items'] == [history]


@pytest.mark.parametrize('method', ['get', 'put', 'delete'])
def test_unknown_and_invalid_id(client, method):
    kwargs = {'json': payload()} if method == 'put' else {}
    assert call(client, method, 999999, **kwargs).status_code == 404
    assert call(client, method, 'abc', **kwargs).status_code == 400


def test_inclusive_dates_employee_and_pagination(client):
    first = post(client, payload(saleDate='2026-10-01')).json()
    second = post(client, payload(saleDate='2026-10-02')).json()
    post(client, payload(saleDate='2026-10-03'))
    result = call(client, 'get', params={'saleDateFrom': '2026-10-01', 'saleDateTo': '2026-10-02', 'employeeId': 1, 'limit': 1, 'offset': 1}).json()
    assert result == {'items': [second], 'total': 2}
    assert call(client, 'get', params={'employeeId': 999}).json()['total'] == 0
    assert call(client, 'get', params={'offset': 99}).json()['items'] == []


@pytest.mark.parametrize('params', [{'limit': 0}, {'limit': 201}, {'offset': -1}, {'status': 'wrong'},
    {'saleDateFrom': 'wrong'}, {'saleDateFrom': '2026-10-02', 'saleDateTo': '2026-10-01'}])
def test_invalid_search(client, params):
    assert call(client, 'get', params=params).status_code == 400
