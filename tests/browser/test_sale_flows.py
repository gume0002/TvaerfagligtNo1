"""T035/T036: sale form through the browser; list fixture until T038."""
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
