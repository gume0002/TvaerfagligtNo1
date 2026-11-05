// Booking page. The backend decides what is valid; this page shows the answer.

import {
  ApiError,
  NetworkError,
  cancelBooking,
  createBooking,
  getCatalogs,
  searchBookings,
  updateBooking,
} from "./api.js";

const PAGE_SIZE = 25;

const form = document.querySelector("#booking-form");
const formTitle = document.querySelector("#form-title");
const saveButton = document.querySelector("#save-button");
const cancelEditButton = document.querySelector("#cancel-edit-button");
const roomTypeSelect = document.querySelector("#roomTypeId");
const countrySelect = document.querySelector("#countryId");
const roomTypeHint = document.querySelector("#room-type-hint");
const globalMessage = document.querySelector("#global-message");
const searchForm = document.querySelector("#search-form");
const searchMessage = document.querySelector("#search-message");
const rows = document.querySelector("#booking-rows");
const table = document.querySelector("#booking-table");
const emptyState = document.querySelector("#empty-state");
const resultCount = document.querySelector("#result-count");
const previousPage = document.querySelector("#previous-page");
const nextPage = document.querySelector("#next-page");

let roomTypes = [];
let editingId = null;
let offset = 0;
let filters = { status: "active" };
// Reused when the same booking is sent again after a network error, so the
// backend cannot create it twice.
let pendingCreate = null;

function showMessage(text, isError = false) {
  globalMessage.textContent = text;
  globalMessage.classList.toggle("error", isError);
  globalMessage.hidden = false;
}

function clearMessage() {
  globalMessage.hidden = true;
  globalMessage.textContent = "";
}

function clearFieldErrors() {
  for (const element of form.querySelectorAll("[data-error-for]")) {
    element.textContent = "";
  }
  for (const element of form.querySelectorAll("[aria-invalid]")) {
    element.removeAttribute("aria-invalid");
    element.removeAttribute("aria-describedby");
  }
}

function showFieldErrors(fieldErrors) {
  for (const { field, message } of fieldErrors) {
    const target = form.querySelector(`[data-error-for="${CSS.escape(field)}"]`);
    if (target) {
      target.textContent = message;
      target.id = `error-${field}`;
      form.elements[field]?.setAttribute("aria-describedby", target.id);
    }
    form.elements[field]?.setAttribute("aria-invalid", "true");
  }
}

function showError(error, showIn = (text) => showMessage(text, true)) {
  if (error instanceof ApiError || error instanceof NetworkError) {
    showIn(error.message);
  } else {
    showIn("Der opstod en uventet fejl.");
    console.error(error);
  }
}

function addOptions(select, items, placeholder) {
  const empty = new Option(placeholder, "");
  select.replaceChildren(empty, ...items.map((item) => new Option(item.name, item.id)));
}

function updateRoomTypeHint() {
  const roomType = roomTypes.find((item) => String(item.id) === roomTypeSelect.value);
  if (!roomType) {
    roomTypeHint.textContent = "";
    return;
  }
  const rates = roomType.suggestedNightlyRates;
  roomTypeHint.textContent =
    `Højst ${roomType.maxGuests} gæster. Vejledende pris: lav ${rates.low}, mellem ${rates.mid}, høj ${rates.high} DKK.`;
}

function readForm() {
  const values = new FormData(form);
  // Empty or malformed numbers are sent as they are, so the backend rejects them.
  const asNumber = (name) => {
    const value = values.get(name);
    return value === "" || !Number.isFinite(Number(value)) ? value : Number(value);
  };
  return {
    guestName: values.get("guestName"),
    countryId: asNumber("countryId"),
    roomTypeId: asNumber("roomTypeId"),
    arrival: values.get("arrival"),
    departure: values.get("departure"),
    guestCount: asNumber("guestCount"),
    nightlyRate: values.get("nightlyRate").trim().replace(",", "."),
  };
}

function resetForm() {
  form.reset();
  editingId = null;
  pendingCreate = null;
  formTitle.textContent = "Opret booking";
  saveButton.textContent = "Opret booking";
  cancelEditButton.hidden = true;
  clearFieldErrors();
  updateRoomTypeHint();
}

function startEdit(booking) {
  clearMessage();
  clearFieldErrors();
  editingId = booking.id;
  form.elements.guestName.value = booking.guestName;
  countrySelect.value = booking.countryId;
  roomTypeSelect.value = booking.roomTypeId;
  form.elements.arrival.value = booking.arrival;
  form.elements.departure.value = booking.departure;
  form.elements.guestCount.value = booking.guestCount;
  form.elements.nightlyRate.value = booking.nightlyRate;
  formTitle.textContent = `Ret booking nr. ${booking.id}`;
  saveButton.textContent = "Gem ændringer";
  cancelEditButton.hidden = false;
  updateRoomTypeHint();
  form.scrollIntoView({ block: "start" });
  form.elements.guestName.focus();
}

function randomKey() {
  // crypto.randomUUID only exists on https and localhost.
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function createKey(payload) {
  const serialized = JSON.stringify(payload);
  if (pendingCreate?.serialized !== serialized) {
    pendingCreate = { serialized, key: randomKey() };
  }
  return pendingCreate.key;
}

async function submitBooking(event) {
  event.preventDefault();
  clearMessage();
  clearFieldErrors();
  saveButton.disabled = true;
  const payload = readForm();
  try {
    if (editingId === null) {
      const booking = await createBooking(payload, createKey(payload));
      resetForm();
      showMessage(`Booking nr. ${booking.id} er oprettet for ${booking.guestName}.`);
    } else {
      const booking = await updateBooking(editingId, payload);
      resetForm();
      showMessage(`Booking nr. ${booking.id} er gemt.`);
    }
    await loadBookings();
  } catch (error) {
    if (error instanceof ApiError) {
      // The backend has answered, so a new attempt is a new request.
      pendingCreate = null;
      showFieldErrors(error.fieldErrors);
      form.querySelector('[aria-invalid="true"]')?.focus();
    }
    showError(error);
  } finally {
    saveButton.disabled = false;
  }
}

async function cancelRow(booking) {
  const confirmed = window.confirm(
    `Vil du slette booking nr. ${booking.id} for ${booking.guestName}? Bookingen aflyses og bevares i historikken.`,
  );
  if (!confirmed) {
    return;
  }
  clearMessage();
  try {
    await cancelBooking(booking.id);
    if (editingId === booking.id) {
      resetForm();
    }
    showMessage(`Booking nr. ${booking.id} er aflyst.`);
    await loadBookings();
  } catch (error) {
    showError(error);
  }
}

function cell(text, className) {
  const element = document.createElement("td");
  element.textContent = text;
  if (className) {
    element.className = className;
  }
  return element;
}

function badge(text, className = "") {
  const element = document.createElement("span");
  element.className = `badge ${className}`.trim();
  element.textContent = text;
  return element;
}

function renderRow(booking) {
  const row = document.createElement("tr");
  row.dataset.bookingId = booking.id;
  const isCancelled = booking.status === "cancelled";
  row.classList.toggle("cancelled", isCancelled);
  row.append(
    cell(booking.id),
    cell(booking.guestName),
    cell(booking.countryName),
    cell(booking.roomTypeName),
    cell(booking.arrival),
    cell(booking.departure),
    cell(booking.guestCount, "number"),
    cell(`${booking.nightlyRate} DKK`, "number"),
  );

  const status = document.createElement("td");
  status.append(isCancelled ? badge("Aflyst", "cancelled") : badge("Aktiv"));
  if (booking.demoData) {
    status.append(badge("Demodata"));
  }
  row.append(status);

  const actions = document.createElement("td");
  if (!isCancelled) {
    const wrapper = document.createElement("div");
    wrapper.className = "row-actions";
    const edit = document.createElement("button");
    edit.type = "button";
    edit.textContent = "Ret";
    edit.setAttribute("aria-label", `Ret booking nr. ${booking.id}`);
    edit.addEventListener("click", () => startEdit(booking));
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "danger";
    remove.textContent = "Slet";
    remove.setAttribute("aria-label", `Slet booking nr. ${booking.id}`);
    remove.addEventListener("click", () => cancelRow(booking));
    wrapper.append(edit, remove);
    actions.append(wrapper);
  }
  row.append(actions);
  return row;
}

async function loadBookings() {
  searchMessage.hidden = true;
  try {
    const page = await searchBookings({ ...filters, offset, limit: PAGE_SIZE });
    if (page.items.length === 0 && offset > 0) {
      // The last row on the last page has just been removed.
      offset = Math.max(0, offset - PAGE_SIZE);
      await loadBookings();
      return;
    }
    rows.replaceChildren(...page.items.map(renderRow));
    table.hidden = page.total === 0;
    emptyState.hidden = page.total !== 0;
    const first = page.total === 0 ? 0 : offset + 1;
    const last = offset + page.items.length;
    resultCount.textContent = page.total === 0 ? "" : `Viser ${first}–${last} af ${page.total} bookinger`;
    previousPage.disabled = offset === 0;
    nextPage.disabled = last >= page.total;
  } catch (error) {
    showError(error, (text) => {
      searchMessage.textContent = text;
      searchMessage.hidden = false;
    });
  }
}

function applySearch(event) {
  event.preventDefault();
  filters = {
    name: document.querySelector("#search-name").value.trim(),
    arrivalFrom: document.querySelector("#search-from").value,
    departureTo: document.querySelector("#search-to").value,
    status: document.querySelector("#search-status").value,
  };
  offset = 0;
  loadBookings();
}

function clearSearch() {
  searchForm.reset();
  filters = { status: "active" };
  offset = 0;
  loadBookings();
}

async function start() {
  form.addEventListener("submit", submitBooking);
  cancelEditButton.addEventListener("click", () => {
    resetForm();
    clearMessage();
  });
  roomTypeSelect.addEventListener("change", updateRoomTypeHint);
  searchForm.addEventListener("submit", applySearch);
  document.querySelector("#clear-search").addEventListener("click", clearSearch);
  previousPage.addEventListener("click", () => {
    offset = Math.max(0, offset - PAGE_SIZE);
    loadBookings();
  });
  nextPage.addEventListener("click", () => {
    offset += PAGE_SIZE;
    loadBookings();
  });

  try {
    const catalogs = await getCatalogs();
    roomTypes = catalogs.roomTypes;
    addOptions(countrySelect, catalogs.countries, "Vælg land");
    addOptions(roomTypeSelect, catalogs.roomTypes, "Vælg værelsestype");
  } catch (error) {
    showError(error);
  }
  await loadBookings();
  document.body.dataset.ready = "true";
}

start();
