// The service validates sales and computes their amounts.
import { ApiError, getCatalogs, createSale, searchSales } from './api.js';
const form = document.querySelector('#sale-form');
const save = document.querySelector('#sale-save');
const message = document.querySelector('#sale-message');
const rows = document.querySelector('#sale-rows');
let pending = null;
let offset = 0;
let filters = {status: 'active'};
const pageSize = 25;

function showError(error, target = message) {
  target.textContent = error.message;
  target.hidden = false;
  target.classList.add('error');
}
function clearErrors() {
  message.hidden = true;
  message.classList.remove('error');
  form.querySelectorAll('[data-error-for]').forEach(element => element.textContent = '');
  form.querySelectorAll('[aria-invalid]').forEach(element => element.removeAttribute('aria-invalid'));
}
function keyFor(payload) {
  const serialized = JSON.stringify(payload);
  if (pending?.serialized !== serialized) {
    const key = Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, '0')).join('');
    pending = {serialized, key};
  }
  return pending.key;
}
function cell(value) {
  const td = document.createElement('td');
  td.textContent = value;
  return td;
}
function renderRow(sale) {
  const row = document.createElement('tr');
  row.dataset.saleId = sale.id;
  row.append(...[sale.id, sale.drinkName, sale.employeeName, sale.saleDate, sale.quantity,
    `${sale.unitPrice} DKK`, `${sale.totalAmount} DKK`,
    `${sale.status === 'cancelled' ? 'Aflyst' : 'Aktiv'}${sale.demoData ? ' · Demodata' : ''}`].map(cell));
  return row;
}
async function loadSales() {
  const errorBox = document.querySelector('#sale-search-message');
  errorBox.hidden = true;
  try {
    const page = await searchSales({...filters, offset, limit: pageSize});
    if (!page.items.length && offset > 0) {
      offset = Math.max(0, offset - pageSize);
      return loadSales();
    }
    rows.replaceChildren(...page.items.map(renderRow));
    document.querySelector('#sale-count').textContent = `${page.total} salg`;
    document.querySelector('#sale-empty').hidden = page.total !== 0;
    document.querySelector('#sale-previous').disabled = offset === 0;
    document.querySelector('#sale-next').disabled = offset + page.items.length >= page.total;
  } catch (error) { showError(error, errorBox); }
}
form.addEventListener('submit', async event => {
  event.preventDefault();
  clearErrors();
  save.disabled = true;
  const values = new FormData(form);
  const number = name => values.get(name) === '' ? '' : Number(values.get(name));
  const payload = {drinkId: number('drinkId'), employeeId: number('employeeId'), quantity: number('quantity'),
    unitPrice: values.get('unitPrice').trim().replace(',', '.'), saleDate: values.get('saleDate')};
  try {
    const sale = await createSale(payload, keyFor(payload));
    form.reset(); pending = null;
    message.textContent = `Salg nr. ${sale.id} er oprettet.`;
    message.hidden = false;
    await loadSales();
  } catch (error) {
    if (error instanceof ApiError) {
      pending = null;
      for (const {field, message: text} of error.fieldErrors) {
        const target = form.querySelector(`[data-error-for="${CSS.escape(field)}"]`);
        if (target) target.textContent = text;
        form.elements[field]?.setAttribute('aria-invalid', 'true');
      }
    }
    showError(error);
  } finally { save.disabled = false; }
});
document.querySelector('#sale-previous').addEventListener('click', () => { offset = Math.max(0, offset - pageSize); loadSales(); });
document.querySelector('#sale-next').addEventListener('click', () => { offset += pageSize; loadSales(); });
async function start() {
  try {
    const catalogs = await getCatalogs();
    for (const [name, items, label] of [['drinkId', catalogs.drinks, 'Vælg drik'], ['employeeId', catalogs.employees, 'Vælg medarbejder']]) {
      form.elements[name].replaceChildren(new Option(label, ''), ...items.map(item => new Option(item.name, item.id)));
    }
  } catch (error) { showError(error); }
  await loadSales();
  document.body.dataset.ready = 'true';
}
start();
