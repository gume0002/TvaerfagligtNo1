"""Explicit demo smoke check; creates and cancels its own marked records only."""
import json
import os
from decimal import Decimal
from uuid import uuid4

import httpx
from playwright.sync_api import expect, sync_playwright

from testsupport.contract import assert_matches_contract

BASE = os.environ.get('DEMO_URL', 'http://host.docker.internal:8080')
SWAGGER = os.environ.get('SWAGGER_URL', 'http://host.docker.internal:8081')


def main():
    booking_id = None
    sale_id = None
    with httpx.Client(base_url=BASE, timeout=20) as client:
        def analysis(path, **params):
            response = client.get(path, params=params)
            assert_matches_contract(response, 'GET', path)
            assert response.status_code == 200, response.text
            return response.json()

        hotel_before = analysis('/api/analytics/hotel')
        bar_before = analysis('/api/analytics/bar')
        today = hotel_before['businessDate']
        year = hotel_before['filters']['year']
        catalogs_response = client.get('/api/catalogs')
        assert_matches_contract(catalogs_response, 'GET', '/api/catalogs')
        catalogs = catalogs_response.json()
        helene = next(e for e in catalogs['employees'] if e['code'] == 'helene-christine')
        drink = catalogs['drinks'][0]
        room = next(r for r in catalogs['roomTypes'] if r['roomCount'] > 10)
        marker = 'Milepæl 3 kontrol ' + str(uuid4())[:8]
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                page = browser.new_page()
                page.goto(BASE)
                expect(page.locator('body')).to_have_attribute('data-ready', 'true')
                page.get_by_label('Gæstens navn').fill(marker)
                page.get_by_label('Land', exact=True).select_option(str(catalogs['countries'][0]['id']))
                page.get_by_label('Værelsestype').select_option(str(room['id']))
                page.get_by_label('Ankomst').fill(f'{year}-01-03')
                page.get_by_label('Afrejse').fill(f'{year}-01-05')
                page.get_by_label('Antal gæster').fill('1')
                page.get_by_label('Aftalt pris pr. nat (DKK)').fill('1000.00')
                with page.expect_response(lambda r: r.request.method == 'POST' and r.url.endswith('/api/bookings')) as saved:
                    page.get_by_role('button', name='Opret booking').click()
                assert saved.value.status == 201, saved.value.text()
                booking_id = saved.value.json()['id']
                expect(page.locator('#global-message')).to_contain_text('er oprettet')
                after_booking = analysis('/api/analytics/hotel')
                assert Decimal(after_booking['totals']['all']['revenue']) == Decimal(hotel_before['totals']['all']['revenue']) + Decimal('2000.00')
                page.get_by_label('Navn', exact=True).fill(marker)
                page.get_by_role('button', name='Søg', exact=True).click()
                row = page.locator('#booking-rows tr').filter(has_text=marker)
                expect(row).to_have_count(1)
                page.once('dialog', lambda dialog: dialog.accept())
                row.get_by_role('button', name='Slet').click()
                expect(page.locator('#global-message')).to_contain_text('er aflyst')
                after_cancel = analysis('/api/analytics/hotel')
                assert after_cancel['totals']['all']['revenue'] == hotel_before['totals']['all']['revenue']

                page.goto(BASE + '/sales.html')
                expect(page.locator('body')).to_have_attribute('data-ready', 'true')
                page.get_by_label('Drik', exact=True).select_option(str(drink['id']))
                page.get_by_label('Medarbejder', exact=True).select_option(str(helene['id']))
                page.get_by_label('Antal', exact=True).fill('3')
                page.get_by_label('Enhedspris (DKK)').fill('100.00')
                page.get_by_label('Salgsdato').fill(today)
                with page.expect_response(lambda r: r.request.method == 'POST' and r.url.endswith('/api/bar-sales')) as saved_sale:
                    page.get_by_role('button', name='Registrér salg').click()
                assert saved_sale.value.status == 201, saved_sale.value.text()
                sale_id = saved_sale.value.json()['id']
                expect(page.locator('#sale-message')).to_contain_text('er oprettet')
                after_sale = analysis('/api/analytics/bar')
                assert Decimal(after_sale['totals']['revenue']) == Decimal(bar_before['totals']['revenue']) + Decimal('300.00')
                assert after_sale['totals']['quantity'] == bar_before['totals']['quantity'] + 3
                page.set_viewport_size({'width': 390, 'height': 844})
                assert page.evaluate('document.documentElement.scrollWidth <= document.documentElement.clientWidth')
                evidence = os.environ.get('EVIDENCE_DIR')
                if evidence:
                    page.screenshot(path=evidence + '/sales-mobile.png', full_page=True)
                for path in ['/api/analytics/hotel', '/api/analytics/bar']:
                    page.goto(BASE + path)
                    data = json.loads(page.locator('body').inner_text())
                    assert 'totals' in data and 'generatedAt' in data
                page.goto(SWAGGER)
                expect(page.locator('.swagger-ui .info .title')).to_contain_text('Hotel Kong Arthur')
                expect(page.locator('#operations-Analytics-getHotelAnalytics')).to_be_visible()
                expect(page.locator('#operations-Analytics-getBarAnalytics')).to_be_visible()
                if evidence:
                    page.screenshot(path=evidence + '/swagger.png', full_page=True)
                browser.close()
                print(json.dumps({'hotelRevenueBefore': hotel_before['totals']['all']['revenue'],
                    'hotelRevenueAfterBooking': after_booking['totals']['all']['revenue'],
                    'hotelRevenueAfterCancellation': after_cancel['totals']['all']['revenue'],
                    'barRevenueBefore': bar_before['totals']['revenue'], 'barRevenueAfterSale': after_sale['totals']['revenue'],
                    'bookingId': booking_id, 'saleId': sale_id, 'swagger': 'visible', 'mobile': 'no overflow'}, ensure_ascii=False))
        finally:
            for resource, id in [('bookings', booking_id), ('bar-sales', sale_id)]:
                if id is not None:
                    response = client.delete(f'/api/{resource}/{id}')
                    assert_matches_contract(response, 'DELETE', f'/api/{resource}/{{id}}')
                    assert response.status_code == 204
            assert analysis('/api/analytics/hotel')['totals']['all']['revenue'] == hotel_before['totals']['all']['revenue']
            assert analysis('/api/analytics/bar')['totals']['revenue'] == bar_before['totals']['revenue']


if __name__ == '__main__':
    main()
