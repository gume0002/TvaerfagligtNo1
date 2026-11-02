"""T035/T036: sale form, editing, cancellation and history through the browser."""
import os

import pytest
from playwright.sync_api import expect, sync_playwright

FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://test-frontend')


@pytest.fixture(scope='module')
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture()
def page(browser, catalog):
    context = browser.new_context(base_url=FRONTEND_URL)
    page = context.new_page()
    page.goto('/sales.html')
    expect(page.locator('body')).to_have_attribute('data-ready', 'true')
    yield page
    context.close()


def fill_sale(page, quantity='3', price='100.00', sale_date='2026-10-01'):
    page.get_by_label('Drik', exact=True).select_option(label='Negroni')
    page.get_by_label('Medarbejder', exact=True).select_option(label='Helene Christine')
    page.get_by_label('Antal', exact=True).fill(quantity)
    page.get_by_label('Enhedspris (DKK)').fill(price)
    page.get_by_label('Salgsdato').fill(sale_date)


def test_form_uses_catalog_and_saves(page):
    expect(page.locator('#drinkId option')).to_have_text(['Vælg drik', 'Negroni'])
    fill_sale(page)
    page.get_by_role('button', name='Registrér salg').click()
    expect(page.locator('#sale-message')).to_contain_text('er oprettet')


@pytest.mark.parametrize('quantity,price,sale_date,field', [
    ('0', '100.00', '2026-10-01', 'quantity'),
    ('3', 'gratis', '2026-10-01', 'unitPrice'),
    ('3', '100.00', '2099-01-01', 'saleDate'),
])
def test_backend_errors_keep_form(page, quantity, price, sale_date, field):
    fill_sale(page, quantity, price, sale_date)
    page.get_by_role('button', name='Registrér salg').click()
    expect(page.locator(f'[data-error-for="{field}"]')).not_to_be_empty()
    expect(page.get_by_label('Enhedspris (DKK)')).to_have_value(price)


def test_saved_sale_survives_reload_and_can_be_edited_cancelled(page):
    fill_sale(page)
    page.get_by_role('button', name='Registrér salg').click()
    expect(page.locator('#sale-rows tr')).to_contain_text('300.00 DKK')
    page.reload()
    expect(page.locator('#sale-rows tr')).to_contain_text('Negroni')
    page.locator('#sale-rows').get_by_role('button', name='Ret', exact=True).click()
    page.get_by_label('Antal', exact=True).fill('0')
    page.get_by_role('button', name='Gem salg').click()
    expect(page.locator('[data-error-for="quantity"]')).not_to_be_empty()
    expect(page.locator('#sale-rows tr')).to_contain_text('300.00 DKK')
    page.get_by_label('Antal', exact=True).fill('2')
    page.get_by_role('button', name='Gem salg').click()
    expect(page.locator('#sale-rows tr')).to_contain_text('200.00 DKK')
    page.once('dialog', lambda dialog: dialog.dismiss())
    page.locator('#sale-rows').get_by_role('button', name='Aflys').click()
    expect(page.locator('#sale-rows tr')).to_have_count(1)
    page.once('dialog', lambda dialog: dialog.accept())
    page.locator('#sale-rows').get_by_role('button', name='Aflys').click()
    expect(page.locator('#sale-rows tr')).to_have_count(0)
    page.get_by_label('Vis salg').select_option('cancelled')
    page.get_by_role('button', name='Søg salg').click()
    expect(page.locator('#sale-rows tr')).to_contain_text('Aflyst')
    expect(page.locator('#sale-rows button')).to_have_count(0)


def test_lost_response_reuses_key(page):
    lost = []
    def lose(route):
        if route.request.method == 'POST' and not lost:
            lost.append(True)
            route.fetch()
            route.abort()
        else:
            route.continue_()
    page.route('**/api/bar-sales', lose)
    fill_sale(page)
    page.get_by_role('button', name='Registrér salg').click()
    expect(page.locator('#sale-message')).to_contain_text('Kunne ikke få kontakt')
    page.get_by_role('button', name='Registrér salg').click()
    expect(page.locator('#sale-message')).to_contain_text('er oprettet')
    expect(page.locator('#sale-rows tr')).to_have_count(1)


def test_edit_brings_the_form_into_view(page):
    page.set_viewport_size({'width': 1000, 'height': 500})
    for _ in range(8):
        fill_sale(page)
        page.get_by_role('button', name='Registrér salg').click()
        expect(page.locator('#sale-message')).to_contain_text('er oprettet')
    page.locator('#sale-rows tr').last.get_by_role('button', name='Ret').click()
    expect(page.locator('#sale-title')).to_contain_text('Ret salg')
    expect(page.locator('#quantity')).to_be_in_viewport()
    expect(page.locator('#quantity')).to_be_focused()


def test_empty_sale_date_says_the_field_is_empty(page):
    fill_sale(page)
    page.get_by_label('Salgsdato').fill('')
    page.get_by_role('button', name='Registrér salg').click()
    expect(page.locator('[data-error-for="saleDate"]')).to_have_text('Feltet skal udfyldes.')
