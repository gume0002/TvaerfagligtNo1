"""Prepares and runs the reduced SC-003 test against an isolated system.

load       Adds bookings and bar sales through the API until there are 1,000 of each.
round N    Makes the change for round N through the API and prints the API's figures,
           which the dashboard must show after a refresh.
status     Prints the current figures.

Everything goes through the REST API, so the normal rules and capacity checks apply.
Requests are repeatable: the same round uses the same idempotency key.
Only the Python standard library is used.
"""

from __future__ import annotations

import json
import random
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta

API = 'http://127.0.0.1:8080'
TARGET = 1000
SEED = 3
YEAR = date.today().year
ROUNDS = {
    1: ('booking', 'oprettelse', 1),
    2: ('booking', 'oprettelse', 2),
    3: ('booking', 'rettelse', 1),
    4: ('booking', 'rettelse', 2),
    5: ('booking', 'aflysning', 1),
    6: ('booking', 'aflysning', 2),
    7: ('salg', 'oprettelse', 1),
    8: ('salg', 'oprettelse', 2),
    9: ('salg', 'rettelse', 1),
    10: ('salg', 'rettelse', 2),
    11: ('salg', 'aflysning', 1),
    12: ('salg', 'aflysning', 2),
}


def call(method: str, path: str, body=None, key: str | None = None):
    headers = {'Content-Type': 'application/json'}
    if key:
        headers['Idempotency-Key'] = key
    data = json.dumps(body).encode('utf-8') if body is not None else None
    request = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        raw = error.read()
        return error.code, json.loads(raw) if raw else None


def get(path: str):
    status, body = call('GET', path)
    if status != 200:
        raise SystemExit(f'GET {path} gav {status}: {body}')
    return body


def load() -> None:
    catalogs = get('/api/catalogs')
    rng = random.Random(SEED)
    bookings = get('/api/bookings?status=all&limit=1')['total']
    number = 0
    while bookings < TARGET:
        number += 1
        room_type = rng.choice(catalogs['roomTypes'])
        arrival = date(YEAR - 1, 1, 1) + timedelta(days=rng.randrange(900))
        payload = {
            'guestName': f'SC003 Gæst {number}',
            'countryId': rng.choice(catalogs['countries'])['id'],
            'roomTypeId': room_type['id'],
            'arrival': arrival.isoformat(),
            'departure': (arrival + timedelta(days=rng.randint(1, 5))).isoformat(),
            'guestCount': rng.randint(1, room_type['maxGuests']),
            'nightlyRate': rng.choice(list(room_type['suggestedNightlyRates'].values())),
        }
        status, _ = call('POST', '/api/bookings', payload, f'sc003-load-booking-{number}')
        if status == 201:
            bookings = get('/api/bookings?status=all&limit=1')['total']
        elif status != 409:
            raise SystemExit(f'Booking {number} gav {status}')
    sales = get('/api/bar-sales?status=all&limit=1')['total']
    number = 0
    today = date.today()
    while sales < TARGET:
        number += 1
        drink = rng.choice(catalogs['drinks'])
        payload = {
            'drinkId': drink['id'],
            'employeeId': rng.choice(catalogs['employees'])['id'],
            'quantity': rng.randint(1, 3),
            'unitPrice': drink['suggestedUnitPrice'],
            'saleDate': (today - timedelta(days=rng.randrange(600))).isoformat(),
        }
        status, body = call('POST', '/api/bar-sales', payload, f'sc003-load-sale-{number}')
        if status != 201:
            raise SystemExit(f'Salg {number} gav {status}: {body}')
        sales += 1
    print(f'Klar: {bookings} bookinger og {sales} barsalg.')


def booking_payload(catalogs: dict, number: int, changed: bool) -> dict:
    room_type = catalogs['roomTypes'][0]
    day = 10 + number
    return {
        'guestName': f'SC003 Runde {number}',
        'countryId': next(item['id'] for item in catalogs['countries'] if item['name'] == 'Denmark'),
        'roomTypeId': room_type['id'],
        'arrival': f'{YEAR}-12-{day}',
        'departure': f'{YEAR}-12-{day + 2}',
        'guestCount': 1,
        'nightlyRate': '1500.00' if changed else '1000.00',
    }


def sale_payload(catalogs: dict, number: int, changed: bool) -> dict:
    return {
        'drinkId': next(item['id'] for item in catalogs['drinks'] if item['name'] == 'Mojito'),
        'employeeId': next(item['id'] for item in catalogs['employees'] if item['name'] == 'Helene Christine'),
        'quantity': 1 if changed else 2,
        'unitPrice': '100.00',
        'saleDate': date.today().isoformat(),
    }


def run_round(number: int) -> None:
    kind, action, item = ROUNDS[number]
    catalogs = get('/api/catalogs')
    if kind == 'booking':
        path, build = '/api/bookings', booking_payload
    else:
        path, build = '/api/bar-sales', sale_payload
    key = f'sc003-{kind}-{item}'
    # Repeating the create with the same key returns the same resource and its id.
    status, created = call('POST', path, build(catalogs, item, False), key)
    if status != 201:
        raise SystemExit(f'Oprettelse gav {status}: {created}')
    if action == 'rettelse':
        status, body = call('PUT', f'{path}/{created["id"]}', build(catalogs, item, True))
        if status != 200:
            raise SystemExit(f'Rettelse gav {status}: {body}')
    elif action == 'aflysning':
        status, body = call('DELETE', f'{path}/{created["id"]}')
        if status != 204:
            raise SystemExit(f'Aflysning gav {status}: {body}')
    print(f'Runde {number}: {action} af {kind} {item} (nr. {created["id"]}).')
    show(kind)


def show(kind: str) -> None:
    if kind == 'booking':
        for title, query in (('Alle sæsoner', ''), ('Højsæson', '&season=high')):
            data = get(f'/api/analytics/hotel?year={YEAR}{query}')
            print(f'  {title}:')
            for period, label in (('all', 'Samlet'), ('past', 'Passeret'), ('upcoming', 'Kommende')):
                row = data['totals'][period]
                print(f"    {label}: omsætning {row['revenue']}, nætter {row['bookedRoomNights']}, ADR {row['adr']}, belægning {row['occupancyRatePercent']}")
            single = [item for item in data['byRoomTypeAndSeason'] if item['roomTypeName'] == 'Standard Single' and item['season'] == 'high']
            print(f"    Standard Single i højsæson: {single[0]['revenue'] if single else '0.00'}")
    else:
        data = get(f'/api/analytics/bar?year={YEAR}')
        print(f"  Helene Christine: {data['totals']['quantity']} drikke, {data['totals']['revenue']} DKK")
        for row in data['byCategory']:
            print(f"  {row['category']}: {row['quantity']} stk., {row['revenue']} DKK, {row['quantitySharePercent']} / {row['revenueSharePercent']} %")
        mojito = next(row for row in data['byDrink'] if row['drinkName'] == 'Mojito')
        print(f"  Mojito: {mojito['quantity']} stk., {mojito['revenue']} DKK")


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else ''
    if command == 'load':
        load()
    elif command == 'round' and len(sys.argv) == 3 and int(sys.argv[2]) in ROUNDS:
        run_round(int(sys.argv[2]))
    elif command == 'status':
        show('booking')
        show('salg')
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    main()
