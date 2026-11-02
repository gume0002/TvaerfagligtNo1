// All communication with the backend. No business rules belong here.

export class ApiError extends Error {
  constructor(status, body) {
    super(body?.message ?? "Der opstod en fejl.");
    this.status = status;
    this.code = body?.code;
    this.fieldErrors = body?.fieldErrors ?? [];
  }
}

export class NetworkError extends Error {
  constructor() {
    super("Kunne ikke få kontakt til systemet. Prøv igen.");
  }
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(path, options);
  } catch {
    throw new NetworkError();
  }
  if (response.status === 204) {
    return null;
  }
  let body = null;
  try {
    body = await response.json();
  } catch {
    // A proxy error page is not JSON. It is handled as an error below.
  }
  if (!response.ok) {
    throw new ApiError(response.status, body);
  }
  return body;
}

function jsonOptions(method, payload, headers = {}) {
  return {
    method,
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify(payload),
  };
}

export function getCatalogs() {
  return request("/api/catalogs");
}

export function searchBookings(filters) {
  const query = new URLSearchParams();
  for (const [name, value] of Object.entries(filters)) {
    if (value !== "" && value !== null && value !== undefined) {
      query.set(name, value);
    }
  }
  return request(`/api/bookings?${query}`);
}

export function createBooking(payload, idempotencyKey) {
  return request("/api/bookings", jsonOptions("POST", payload, { "Idempotency-Key": idempotencyKey }));
}

export function updateBooking(id, payload) {
  return request(`/api/bookings/${id}`, jsonOptions("PUT", payload));
}

export function cancelBooking(id) {
  return request(`/api/bookings/${id}`, { method: "DELETE" });
}
