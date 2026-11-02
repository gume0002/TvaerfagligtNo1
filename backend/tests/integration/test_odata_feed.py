"""T052/T053: Tableau's feed through all layers, with hand-calculated expectations."""

import json
import xml.etree.ElementTree as ET
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from testsupport.contract import assert_matches_contract, load_contract

ROOT = '/api/odata'
SETS = ('HotelTotals', 'HotelRoomTypeSeason', 'HotelCountries', 'HotelRoomTypeRanks', 'BarTotals', 'BarDrinks', 'BarCategories')
EDM = '{http://docs.oasis-open.org/odata/ns/edm}'
# The test catalog has 8 rooms. The frozen date is 2026-10-29, day 302 of the year.
ALL_YEAR = dict(year=2026, seasonFilter='all', countryFilter='all', roomTypeFilter='all')


@pytest.fixture()
def client(settings, frozen_clock, catalog):
    with TestClient(create_app(settings, frozen_clock), raise_server_exceptions=False) as client:
        yield client


def book(client, catalog, **changes):
    payload = dict(guestName='Gæst', countryId=catalog.sweden, roomTypeId=catalog.large, arrival='2026-06-10',
                   departure='2026-06-13', guestCount=2, nightlyRate='1000.00') | changes
    response = client.post('/api/bookings', json=payload, headers={'Idempotency-Key': str(uuid4())})
    assert response.status_code == 201, response.text
    return response.json()


def feed(client, name):
    response = client.get(f'{ROOT}/{name}')
    assert_matches_contract(response, 'GET', f'{ROOT}/{name}')
    assert response.status_code == 200, response.text
    assert response.headers['OData-Version'] == '4.0'
    return response.json()['value']


def matching(rows, **filters):
    return [row for row in rows if all(row[key] == value for key, value in filters.items())]


def one(rows, **filters):
    found = matching(rows, **filters)
    assert len(found) == 1, f'{filters}: {found}'
    return found[0]


class TestProtocol:
    def test_service_document_lists_every_set(self, client):
        response = client.get(f'{ROOT}/')
        assert_matches_contract(response, 'GET', f'{ROOT}/')
        assert {item['name'] for item in response.json()['value']} == set(SETS)

    def test_metadata_matches_the_contract_field_by_field(self, client):
        response = client.get(f'{ROOT}/$metadata')
        assert response.status_code == 200
        assert response.headers['content-type'].startswith('application/xml')
        root = ET.fromstring(response.text)
        types = {node.get('Name'): node for node in root.iter(f'{EDM}EntityType')}
        schemas = load_contract()['components']['schemas']
        assert len(types) == len(SETS)
        for name in SETS:
            described = {prop.get('Name') for prop in types[f'{name}Row'].iter(f'{EDM}Property')}
            assert described == set(schemas[f'ODataRow{name}']['properties']), name

    def test_nullable_fields_in_metadata_match_the_contract(self, client):
        root = ET.fromstring(client.get(f'{ROOT}/$metadata').text)
        types = {node.get('Name'): node for node in root.iter(f'{EDM}EntityType')}
        schemas = load_contract()['components']['schemas']
        for name in SETS:
            properties = schemas[f'ODataRow{name}']['properties']
            for prop in types[f'{name}Row'].iter(f'{EDM}Property'):
                assert (prop.get('Nullable') == 'true') == properties[prop.get('Name')].get('nullable', False), prop.get('Name')

    def test_amounts_are_exact_json_numbers(self, client, catalog):
        book(client, catalog, nightlyRate='1234.50')
        response = client.get(f'{ROOT}/HotelRoomTypeRanks')
        assert '"revenue":3703.50' in response.text

    def test_null_ratio_is_a_real_json_null(self, client):
        assert '"adr":null' in client.get(f'{ROOT}/HotelTotals').text

    def test_danish_characters_are_kept(self, client, catalog):
        # Names are sent as UTF-8 and not as escape sequences.
        assert json.loads(client.get(f'{ROOT}/BarTotals').text)['value'][0]['employee'] == 'Helene Christine'

    @pytest.mark.parametrize('name', SETS)
    def test_row_ids_are_unique(self, client, catalog, name):
        book(client, catalog)
        ids = [row['id'] for row in feed(client, name)]
        assert ids and len(ids) == len(set(ids))

    def test_feed_is_read_only(self, client):
        assert client.post(f'{ROOT}/HotelTotals', json={}).status_code == 405

    def test_lost_database_gives_503(self, settings, frozen_clock):
        from dataclasses import replace

        with TestClient(create_app(replace(settings, database_host='host-that-does-not-exist'), frozen_clock), raise_server_exceptions=False) as client:
            response = client.get(f'{ROOT}/HotelTotals')
        assert_matches_contract(response, 'GET', f'{ROOT}/HotelTotals')
        assert response.status_code == 503


class TestCombinations:
    def test_every_combination_has_exactly_one_row_per_period(self, client):
        # 4 seasons x (2 countries + all) x (3 room types + all) = 48 combinations, times 3 periods.
        rows = feed(client, 'HotelTotals')
        assert len(rows) == 144
        keys = {(row['year'], row['seasonFilter'], row['countryFilter'], row['roomTypeFilter'], row['period']) for row in rows}
        assert len(keys) == 144

    def test_empty_database_still_has_the_current_year(self, client):
        assert {row['year'] for row in feed(client, 'HotelTotals')} == {2026}
        assert {row['year'] for row in feed(client, 'BarTotals')} == {2026}

    def test_a_stay_over_new_year_adds_both_years(self, client, catalog):
        book(client, catalog, arrival='2026-12-30', departure='2027-01-02')
        assert {row['year'] for row in feed(client, 'HotelTotals')} == {2026, 2027}

    def test_departure_on_new_years_day_does_not_add_the_next_year(self, client, catalog):
        book(client, catalog, arrival='2026-12-30', departure='2027-01-01')
        assert {row['year'] for row in feed(client, 'HotelTotals')} == {2026}

    def test_cancelled_booking_does_not_add_a_year(self, client, catalog):
        created = book(client, catalog, arrival='2020-01-01', departure='2020-01-03')
        assert client.delete(f'/api/bookings/{created["id"]}').status_code == 204
        assert 2020 not in {row['year'] for row in feed(client, 'HotelTotals')}

    def test_booking_outside_the_supported_years_gives_no_rows(self, client, catalog):
        book(client, catalog, arrival='1990-01-01', departure='1990-01-03')
        assert {row['year'] for row in feed(client, 'HotelTotals')} == {2026}


class TestHotelFigures:
    def test_us7_1_new_year_split(self, client, catalog):
        book(client, catalog, arrival='2026-12-30', departure='2027-01-02')
        totals = feed(client, 'HotelTotals')
        assert one(totals, year=2026, seasonFilter='all', countryFilter='all', roomTypeFilter='all', period='all')['revenue'] == 2000
        assert one(totals, year=2027, seasonFilter='all', countryFilter='all', roomTypeFilter='all', period='all')['revenue'] == 1000

    def test_us7_3_guests_nights_and_revenue(self, client, catalog):
        book(client, catalog, guestCount=2)
        country = one(feed(client, 'HotelCountries'), **ALL_YEAR, country='Sweden')
        assert country['guestStays'] == 2
        assert country['revenue'] == 3000
        assert one(feed(client, 'HotelTotals'), **ALL_YEAR, period='all')['bookedRoomNights'] == 3

    def test_us7_5_room_type_split_on_season(self, client, catalog):
        book(client, catalog, arrival='2026-02-28', departure='2026-03-02')
        rows = feed(client, 'HotelRoomTypeSeason')
        assert one(rows, **ALL_YEAR, roomType='Large Suite', season='low')['revenue'] == 1000
        assert one(rows, **ALL_YEAR, roomType='Large Suite', season='mid')['revenue'] == 1000
        only_low = matching(rows, year=2026, seasonFilter='low', countryFilter='all', roomTypeFilter='all')
        assert [(row['roomType'], row['season'], row['revenue']) for row in only_low] == [('Large Suite', 'low', 1000)]

    def test_us7_2_tied_first_places(self, client, catalog):
        book(client, catalog, roomTypeId=catalog.large, nightlyRate='1000.00')
        book(client, catalog, roomTypeId=catalog.double, nightlyRate='1000.00')
        book(client, catalog, roomTypeId=catalog.tiny, nightlyRate='500.00')
        rows = matching(feed(client, 'HotelRoomTypeRanks'), **ALL_YEAR)
        assert sorted(row['revenueRank'] for row in rows) == [1, 1, 3]
        assert one(rows, roomType='Tiny Room')['revenueRank'] == 3

    def test_denominators_follow_the_selected_filters(self, client, catalog):
        book(client, catalog, arrival='2026-06-10', departure='2026-06-12')
        rows = feed(client, 'HotelTotals')
        # 365 days x 8 rooms.
        assert one(rows, **ALL_YEAR, period='all')['availableRoomNights'] == 2920
        # 301 days before 29 October and 64 from then on, x 8 rooms.
        assert one(rows, **ALL_YEAR, period='past')['availableRoomNights'] == 2408
        assert one(rows, **ALL_YEAR, period='upcoming')['availableRoomNights'] == 512
        # January and February are 59 days, x 8 rooms.
        low = one(rows, year=2026, seasonFilter='low', countryFilter='all', roomTypeFilter='all', period='all')
        assert low['availableRoomNights'] == 472
        # Tiny Room has one room.
        tiny = one(rows, year=2026, seasonFilter='all', countryFilter='all', roomTypeFilter='Tiny Room', period='all')
        assert tiny['availableRoomNights'] == 365

    def test_country_filter_keeps_hotel_capacity_and_is_marked(self, client, catalog):
        book(client, catalog, countryId=catalog.sweden)
        rows = feed(client, 'HotelTotals')
        sweden = one(rows, year=2026, seasonFilter='all', countryFilter='Sweden', roomTypeFilter='all', period='all')
        assert sweden['availableRoomNights'] == 2920
        assert sweden['occupancyScope'] == 'country_contribution'
        assert one(rows, **ALL_YEAR, period='all')['occupancyScope'] == 'hotel'
        germany = one(rows, year=2026, seasonFilter='all', countryFilter='Germany', roomTypeFilter='all', period='all')
        assert germany['revenue'] == 0
        assert germany['adr'] is None
        assert germany['adrStatus'] == 'no_data'

    def test_adr_and_occupancy(self, client, catalog):
        # Two nights in Tiny Room at 1000.00, in a year with 365 available room nights.
        book(client, catalog, roomTypeId=catalog.tiny, arrival='2026-06-10', departure='2026-06-12')
        tiny = one(feed(client, 'HotelTotals'), year=2026, seasonFilter='all', countryFilter='all', roomTypeFilter='Tiny Room', period='all')
        assert tiny['adr'] == 1000
        assert tiny['occupancyRatePercent'] == 0.55

    def test_past_and_upcoming_are_separate(self, client, catalog):
        book(client, catalog, arrival='2026-10-28', departure='2026-10-31')
        rows = feed(client, 'HotelTotals')
        assert one(rows, **ALL_YEAR, period='past')['revenue'] == 1000
        assert one(rows, **ALL_YEAR, period='upcoming')['revenue'] == 2000
        assert one(rows, **ALL_YEAR, period='all')['revenue'] == 3000

    def test_us8_3_no_bookings(self, client):
        row = one(feed(client, 'HotelTotals'), **ALL_YEAR, period='all')
        assert row['revenue'] == 0
        assert row['occupancyRatePercent'] == 0
        assert row['adr'] is None
        assert row['satisfactionStatus'] == 'no_data'

    def test_satisfaction_never_has_a_score(self, client):
        fields = load_contract()['components']['schemas']['ODataRowHotelTotals']['properties']
        assert not [name for name in fields if 'satisfaction' in name.lower() and name != 'satisfactionStatus']
        assert {row['satisfactionStatus'] for row in feed(client, 'HotelTotals')} == {'no_data'}

    def test_cancelled_booking_contributes_nothing(self, client, catalog):
        created = book(client, catalog)
        assert client.delete(f'/api/bookings/{created["id"]}').status_code == 204
        assert one(feed(client, 'HotelTotals'), **ALL_YEAR, period='all')['revenue'] == 0
        assert matching(feed(client, 'HotelCountries'), **ALL_YEAR) == []


class TestBarFigures:
    def sell(self, client, drink_id, employee_id, quantity, price, day='2026-05-01'):
        response = client.post('/api/bar-sales', headers={'Idempotency-Key': str(uuid4())}, json=dict(
            drinkId=drink_id, employeeId=employee_id, quantity=quantity, unitPrice=price, saleDate=day))
        assert response.status_code == 201, response.text
        return response.json()

    def catalogs(self, client):
        return client.get('/api/catalogs').json()

    def test_us9_1_totals_and_shares(self, client, engine):
        from sqlalchemy import text
        from decimal import Decimal  # noqa: F401

        with engine.begin() as connection:
            connection.execute(text("INSERT INTO drinks (name, category, suggested_unit_price) VALUES ('Latte', 'coffee', 50)"))
        catalogs = self.catalogs(client)
        employee = catalogs['employees'][0]['id']
        drinks = {item['category']: item['id'] for item in catalogs['drinks']}
        self.sell(client, drinks['cocktail'], employee, 3, '100.00')
        self.sell(client, drinks['coffee'], employee, 2, '50.00')

        totals = one(feed(client, 'BarTotals'), year=2026, employee='Helene Christine')
        assert totals['quantity'] == 5
        assert totals['revenue'] == 400
        categories = feed(client, 'BarCategories')
        cocktail = one(categories, year=2026, category='cocktail')
        assert (cocktail['quantitySharePercent'], cocktail['revenueSharePercent'], cocktail['revenue']) == (60, 75, 300)
        coffee = one(categories, year=2026, category='coffee')
        assert (coffee['quantitySharePercent'], coffee['revenueSharePercent'], coffee['revenue']) == (40, 25, 100)

    def test_drinks_without_sales_are_included(self, client):
        drinks = feed(client, 'BarDrinks')
        assert one(drinks, year=2026, drink='Negroni')['quantity'] == 0
        assert one(drinks, year=2026, drink='Negroni')['revenue'] == 0

    def test_us9_3_no_sales(self, client):
        row = matching(feed(client, 'BarCategories'), year=2026)[0]
        assert row['quantitySharePercent'] is None
        assert row['shareStatus'] == 'no_data'

    def test_a_sale_adds_its_year_but_a_cancelled_one_does_not(self, client):
        catalogs = self.catalogs(client)
        sale = self.sell(client, catalogs['drinks'][0]['id'], catalogs['employees'][0]['id'], 1, '100.00', day='2024-05-01')
        assert 2024 in {row['year'] for row in feed(client, 'BarTotals')}
        assert client.delete(f'/api/bar-sales/{sale["id"]}').status_code == 204
        assert 2024 not in {row['year'] for row in feed(client, 'BarTotals')}


class TestParityWithRest:
    """The feed must show the REST result for the same filters."""

    def number(self, value):
        return None if value is None else float(value)

    @pytest.mark.parametrize('season', [None, 'low', 'high'])
    def test_hotel_totals_match_rest(self, client, catalog, season):
        book(client, catalog, arrival='2026-02-20', departure='2026-02-25', roomTypeId=catalog.double, nightlyRate='1111.11')
        book(client, catalog, arrival='2026-06-10', departure='2026-06-13', countryId=catalog.germany, nightlyRate='2222.22')
        rows = feed(client, 'HotelTotals')
        for country_id, country in ((None, 'all'), (catalog.sweden, 'Sweden'), (catalog.germany, 'Germany')):
            for type_id, room_type in ((None, 'all'), (catalog.double, 'Double Room'), (catalog.large, 'Large Suite')):
                params = {'year': 2026} | ({'season': season} if season else {})
                params |= ({'countryId': country_id} if country_id else {}) | ({'roomTypeId': type_id} if type_id else {})
                rest = client.get('/api/analytics/hotel', params=params).json()
                for period in ('past', 'upcoming', 'all'):
                    row = one(rows, year=2026, seasonFilter=season or 'all', countryFilter=country, roomTypeFilter=room_type, period=period)
                    expected = rest['totals'][period]
                    assert row['revenue'] == self.number(expected['revenue'])
                    assert row['bookedRoomNights'] == expected['bookedRoomNights']
                    assert row['availableRoomNights'] == expected['availableRoomNights']
                    assert row['occupancyRatePercent'] == self.number(expected['occupancyRatePercent'])
                    assert row['adr'] == self.number(expected['adr'])

    def test_groupings_match_rest(self, client, catalog):
        book(client, catalog, roomTypeId=catalog.large, nightlyRate='1000.00')
        book(client, catalog, roomTypeId=catalog.double, countryId=catalog.germany, nightlyRate='1000.00')
        rest = client.get('/api/analytics/hotel', params={'year': 2026}).json()
        countries = matching(feed(client, 'HotelCountries'), **ALL_YEAR)
        assert sorted((row['country'], row['revenue'], row['revenueRank']) for row in countries) == sorted(
            (item['countryName'], float(item['revenue']), item['rank']) for item in rest['topCountries'])
        room_types = matching(feed(client, 'HotelRoomTypeRanks'), **ALL_YEAR)
        assert sorted((row['roomType'], row['revenue'], row['revenueRank']) for row in room_types) == sorted(
            (item['roomTypeName'], float(item['revenue']), item['rank']) for item in rest['topRoomTypes'])
        seasons = matching(feed(client, 'HotelRoomTypeSeason'), **ALL_YEAR)
        assert sorted((row['roomType'], row['season'], row['revenue']) for row in seasons) == sorted(
            (item['roomTypeName'], item['season'], float(item['revenue'])) for item in rest['byRoomTypeAndSeason'])

    def test_change_is_visible_on_the_next_read(self, client, catalog):
        created = book(client, catalog)
        assert one(feed(client, 'HotelTotals'), **ALL_YEAR, period='all')['revenue'] == 3000
        payload = dict(guestName='Gæst', countryId=catalog.sweden, roomTypeId=catalog.large, arrival='2026-06-10',
                       departure='2026-06-11', guestCount=2, nightlyRate='1000.00')
        assert client.put(f'/api/bookings/{created["id"]}', json=payload).status_code == 200
        assert one(feed(client, 'HotelTotals'), **ALL_YEAR, period='all')['revenue'] == 1000
        assert client.delete(f'/api/bookings/{created["id"]}').status_code == 204
        assert one(feed(client, 'HotelTotals'), **ALL_YEAR, period='all')['revenue'] == 0
