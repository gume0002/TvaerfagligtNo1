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
