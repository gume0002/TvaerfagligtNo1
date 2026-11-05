// Shows the official figures from the API. Nothing is calculated here: bar lengths
// are only a drawing of the values, and all numbers and shares come from the backend.

import { getBarAnalytics, getCatalogs, getHotelAnalytics } from "./api.js";

const SEASON_LABELS = { low: "Lavsæson", mid: "Mellemsæson", high: "Højsæson" };
const SEASON_ORDER = ["low", "mid", "high"];
const CATEGORY_LABELS = { cocktail: "Cocktail", coffee: "Kaffe" };
const CATEGORY_ORDER = ["cocktail", "coffee"];
const NO_DATA = "Intet datagrundlag";
const PERIODS = [["all", "Samlet"], ["past", "Passeret"], ["upcoming", "Kommende"]];

const element = (id) => document.querySelector(`#${id}`);
const yearSelect = element("filter-year");
const seasonSelect = element("filter-season");
const countrySelect = element("filter-country");
const roomTypeSelect = element("filter-room-type");
const employeeSelect = element("filter-employee");
const tooltip = element("chart-tooltip");
let latestRequest = 0;

function formatNumber(value, decimals = 0) {
  return Number(value).toLocaleString("da-DK", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function formatMoney(value) {
  return `${formatNumber(value, 2)} DKK`;
}

function formatPercent(value) {
  return value === null ? NO_DATA : `${formatNumber(value, 2)} %`;
}

function formatGeneratedAt(value) {
  const moment = new Date(value).toLocaleString("da-DK", { dateStyle: "short", timeStyle: "medium", timeZone: "Europe/Copenhagen" });
  return `${moment} (dansk tid)`;
}

function make(tag, className, text) {
  const node = document.createElement(tag);
  if (className) {
    node.className = className;
  }
  if (text !== undefined) {
    node.textContent = text;
  }
  return node;
}

function tile(label, value, note, id) {
  const node = make("div", "tile");
  const valueNode = make("div", "tile-value", value);
  if (id) {
    valueNode.id = id;
  }
  node.append(make("div", "tile-label", label), valueNode);
  if (note) {
    node.append(make("div", "tile-note", note));
  }
  return node;
}

function renderTable(table, headers, rows) {
  const head = make("thead");
  const headRow = make("tr");
  headers.forEach((header) => headRow.append(make("th", "", header)));
  head.append(headRow);
  const body = make("tbody");
  rows.forEach((row) => {
    const tr = make("tr");
    row.forEach((value) => tr.append(make("td", "", value)));
    body.append(tr);
  });
  table.replaceChildren(head, body);
}

function legend(target, items) {
  target.replaceChildren(...items.map(([key, label]) => {
    const entry = make("span", "legend-item");
    entry.append(make("span", `legend-key series-${key}`), make("span", "", label));
    return entry;
  }));
}

function showTooltip(event, value, label) {
  tooltip.replaceChildren(make("strong", "", value), make("span", "", label));
  tooltip.hidden = false;
  const box = event.target.getBoundingClientRect();
  const x = event.clientX ?? box.left + box.width / 2;
  const y = event.clientY ?? box.top;
  const left = Math.min(Math.max(8, x + 12), window.innerWidth - tooltip.offsetWidth - 8);
  tooltip.style.left = `${left}px`;
  tooltip.style.top = `${Math.max(8, y - tooltip.offsetHeight - 12)}px`;
}

function hideTooltip() {
  tooltip.hidden = true;
}

function withTooltip(mark, value, label) {
  mark.tabIndex = 0;
  mark.setAttribute("aria-label", `${label}: ${value}`);
  mark.addEventListener("pointermove", (event) => showTooltip(event, value, label));
  mark.addEventListener("pointerleave", hideTooltip);
  mark.addEventListener("focus", (event) => showTooltip(event, value, label));
  mark.addEventListener("blur", hideTooltip);
  return mark;
}

function emptyChart(target) {
  target.replaceChildren(make("p", "empty-state", "Ingen data for dette valg."));
}

// Rows of { label, total, totalText, segments: [{ key, value, valueText, label }] }.
function renderBars(target, rows) {
  if (!rows.length) {
    emptyChart(target);
    return;
  }
  const largest = Math.max(...rows.map((row) => Number(row.total)));
  target.replaceChildren(...rows.map((row) => {
    const line = make("div", "bar-row");
    line.append(make("div", "bar-label", row.label));
    const track = make("div", "bar-track");
    const marks = make("div", "bar-marks");
    marks.style.setProperty("--bar-length", largest > 0 ? Number(row.total) / largest : 0);
    row.segments.filter((segment) => Number(segment.value) > 0).forEach((segment) => {
      const mark = make("span", `bar-segment series-${segment.key}`);
      mark.style.flexGrow = Number(segment.value);
      marks.append(withTooltip(mark, segment.valueText, segment.label));
    });
    track.append(marks, make("span", "bar-value", row.totalText));
    line.append(track);
    return line;
  }));
}

function renderHotel(data) {
  const { all, past, upcoming } = data.totals;
  const countryOnly = data.occupancyScope === "country_contribution";
  element("hotel-tiles").replaceChildren(
    tile("Årets omsætning", formatMoney(all.revenue), `Passeret ${formatMoney(past.revenue)} · Kommende ${formatMoney(upcoming.revenue)}`, "hotel-revenue"),
    tile(countryOnly ? "Landets bidrag til belægningen" : "Belægning", formatPercent(all.occupancyRatePercent), `${formatNumber(all.bookedRoomNights)} af ${formatNumber(all.availableRoomNights)} værelsesnætter`, "hotel-occupancy"),
    tile("Gennemsnitspris pr. nat (ADR)", all.adr === null ? NO_DATA : formatMoney(all.adr), null, "hotel-adr"),
    tile("Gæstetilfredshed", NO_DATA, "Der findes ingen vurderinger", "hotel-satisfaction"),
  );
  renderTable(element("hotel-periods"), ["Periode", "Omsætning", "Bookede nætter", "Tilgængelige nætter", "Belægning", "ADR"], PERIODS.map(([key, label]) => {
    const row = data.totals[key];
    return [label, formatMoney(row.revenue), formatNumber(row.bookedRoomNights), formatNumber(row.availableRoomNights), formatPercent(row.occupancyRatePercent), row.adr === null ? NO_DATA : formatMoney(row.adr)];
  }));

  legend(element("season-legend"), SEASON_ORDER.map((key) => [key, SEASON_LABELS[key]]));
  const seasonRows = (roomTypeName) => data.byRoomTypeAndSeason.filter((item) => item.roomTypeName === roomTypeName);
  renderBars(element("chart-room-types"), data.topRoomTypes.map((type) => ({
    label: `${type.rank}. ${type.roomTypeName}`,
    total: type.revenue,
    totalText: formatMoney(type.revenue),
    segments: SEASON_ORDER.map((season) => {
      const found = seasonRows(type.roomTypeName).find((item) => item.season === season);
      const value = found ? found.revenue : "0";
      return { key: season, value, valueText: formatMoney(value), label: `${type.roomTypeName}, ${SEASON_LABELS[season]}` };
    }),
  })));
  renderTable(element("table-room-types"), ["Placering", "Værelsestype", "Sæson", "Omsætning"], data.topRoomTypes.flatMap((type) => seasonRows(type.roomTypeName).map((item) => [
    type.rank, type.roomTypeName, SEASON_LABELS[item.season], formatMoney(item.revenue),
  ])));

  renderBars(element("chart-countries"), data.topCountries.map((country) => ({
    label: `${country.rank}. ${country.countryName}`,
    total: country.revenue,
    totalText: formatMoney(country.revenue),
    segments: [{ key: "single", value: country.revenue, valueText: formatMoney(country.revenue), label: country.countryName }],
  })));
  renderTable(element("table-countries"), ["Placering", "Land", "Omsætning"], data.topCountries.map((country) => [country.rank, country.countryName, formatMoney(country.revenue)]));

  const guests = [...data.guestStaysByCountry].sort((a, b) => b.guestStays - a.guestStays || a.countryName.localeCompare(b.countryName, "da"));
  renderBars(element("chart-guests"), guests.map((item) => ({
    label: item.countryName,
    total: item.guestStays,
    totalText: formatNumber(item.guestStays),
    segments: [{ key: "single", value: item.guestStays, valueText: `${formatNumber(item.guestStays)} gæsteophold`, label: item.countryName }],
  })));
  renderTable(element("table-guests"), ["Land", "Gæsteophold"], guests.map((item) => [item.countryName, formatNumber(item.guestStays)]));
}

function renderCategoryShares(categories) {
  const target = element("chart-categories");
  const measures = [
    ["Andel af antal", "quantitySharePercent", "quantity", (value) => `${formatNumber(value)} stk.`],
    ["Andel af omsætning", "revenueSharePercent", "revenue", formatMoney],
  ];
  target.replaceChildren(...measures.map(([title, shareField, valueField, formatValue]) => {
    const row = make("div", "share-row");
    row.append(make("div", "bar-label", title));
    if (categories.every((item) => item[shareField] === null)) {
      row.append(make("div", "share-empty", NO_DATA));
      return row;
    }
    const track = make("div", "share-track");
    CATEGORY_ORDER.forEach((key) => {
      const item = categories.find((category) => category.category === key);
      if (Number(item[shareField]) > 0) {
        const mark = make("span", `bar-segment series-${key}`);
        mark.style.flexGrow = Number(item[shareField]);
        track.append(withTooltip(mark, `${formatPercent(item[shareField])} · ${formatValue(item[valueField])}`, `${title}, ${CATEGORY_LABELS[key]}`));
      }
    });
    const values = make("div", "share-values");
    CATEGORY_ORDER.forEach((key) => {
      const item = categories.find((category) => category.category === key);
      values.append(make("span", "", `${CATEGORY_LABELS[key]} ${formatPercent(item[shareField])}`));
    });
    row.append(track, values);
    return row;
  }));
}

function renderBar(data) {
  element("bar-employee").textContent = data.filters.employeeName;
  element("bar-tiles").replaceChildren(
    tile("Årets salg", formatMoney(data.totals.revenue), null, "bar-revenue"),
    tile("Solgte drikke", formatNumber(data.totals.quantity), null, "bar-quantity"),
  );
  legend(element("category-legend"), CATEGORY_ORDER.map((key) => [key, CATEGORY_LABELS[key]]));
  renderCategoryShares(data.byCategory);
  renderTable(element("table-categories"), ["Kategori", "Antal", "Omsætning", "Andel af antal", "Andel af omsætning"], CATEGORY_ORDER.map((key) => {
    const item = data.byCategory.find((category) => category.category === key);
    return [CATEGORY_LABELS[key], formatNumber(item.quantity), formatMoney(item.revenue), formatPercent(item.quantitySharePercent), formatPercent(item.revenueSharePercent)];
  }));

  legend(element("drink-legend"), CATEGORY_ORDER.map((key) => [key, CATEGORY_LABELS[key]]));
  const drinks = [...data.byDrink].sort((a, b) => Number(b.revenue) - Number(a.revenue) || a.drinkName.localeCompare(b.drinkName, "da"));
  renderBars(element("chart-drinks"), drinks.map((drink) => ({
    label: drink.drinkName,
    total: drink.revenue,
    totalText: formatMoney(drink.revenue),
    segments: [{ key: drink.category, value: drink.revenue, valueText: `${formatMoney(drink.revenue)} · ${formatNumber(drink.quantity)} stk.`, label: drink.drinkName }],
  })));
  renderTable(element("table-drinks"), ["Drik", "Kategori", "Antal", "Omsætning"], drinks.map((drink) => [drink.drinkName, CATEGORY_LABELS[drink.category], formatNumber(drink.quantity), formatMoney(drink.revenue)]));
}

function renderStatus(hotel, bar) {
  const status = element("data-status");
  const scope = [`Data fra ${formatGeneratedAt(hotel.generatedAt)}`];
  if (hotel.demoData || bar.demoData) {
    scope.push("Demodata");
  }
  status.textContent = scope.join(" · ");
}

async function load() {
  const request = ++latestRequest;
  const year = yearSelect.value;
  try {
    const [hotel, bar] = await Promise.all([
      getHotelAnalytics({ year, season: seasonSelect.value, countryId: countrySelect.value, roomTypeId: roomTypeSelect.value }),
      getBarAnalytics({ year, employeeId: employeeSelect.value }),
    ]);
    if (request !== latestRequest) {
      return;
    }
    renderHotel(hotel);
    renderBar(bar);
    renderStatus(hotel, bar);
    element("analytics-error").hidden = true;
    element("analytics-content").hidden = false;
  } catch (error) {
    if (request !== latestRequest) {
      return;
    }
    // Old numbers must not look current, so they are removed from view.
    element("analytics-content").hidden = true;
    element("data-status").textContent = "";
    hideTooltip();
    const box = element("analytics-error");
    box.textContent = error.message || "Analyserne kunne ikke hentes.";
    box.hidden = false;
  } finally {
    document.body.dataset.loadedRequest = String(request);
  }
}

function fillSelect(select, items, allLabel) {
  const options = items.map((item) => new Option(item.name, item.id));
  select.replaceChildren(...(allLabel ? [new Option(allLabel, ""), ...options] : options));
}

async function start() {
  const currentYear = new Date().getFullYear();
  yearSelect.replaceChildren(...[currentYear + 1, currentYear, currentYear - 1, currentYear - 2].map((year) => new Option(year, year)));
  yearSelect.value = String(currentYear);
  try {
    const catalogs = await getCatalogs();
    fillSelect(countrySelect, catalogs.countries, "Alle");
    fillSelect(roomTypeSelect, catalogs.roomTypes, "Alle");
    fillSelect(employeeSelect, catalogs.employees);
  } catch (error) {
    const box = element("analytics-error");
    box.textContent = error.message || "Filtrene kunne ikke hentes.";
    box.hidden = false;
    document.body.dataset.ready = "true";
    return;
  }
  [yearSelect, seasonSelect, countrySelect, roomTypeSelect, employeeSelect].forEach((select) => select.addEventListener("change", load));
  element("analytics-filters").addEventListener("submit", (event) => event.preventDefault());
  await load();
  document.body.dataset.ready = "true";
}

start();
