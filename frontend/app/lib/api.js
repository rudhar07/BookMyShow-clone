/**
 * lib/api.js — the ONE place the frontend knows how to reach the backend.
 * =======================================================================
 *
 * WHY centralise (same reasoning as backend/database.py): if the API URL or
 * error handling changes, we edit it here once, not in every component.
 *
 * The base URL comes from an env var so we never hardcode "localhost" into
 * production builds. It falls back to our dev backend on port 9000.
 */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://localhost:9000";

/** Thin wrapper around fetch that throws a useful Error on non-2xx responses. */
async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store", // booking data is live; never serve a stale cache
    ...options,
  });
  if (!res.ok) {
    // FastAPI puts the human message in {detail: "..."}. Surface it to the UI.
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body.detail) detail = body.detail;
    } catch (_) {}
    throw new Error(detail);
  }
  return res.json();
}

// --- Auth (mock sign-in) ---
export const login = (payload) =>
  request("/api/auth/login", { method: "POST", body: JSON.stringify(payload) });

// --- Cities ---
export const getCities = () => request("/api/cities");

// --- Search (movies by title + cinemas in the city) ---
export const search = (q, city) =>
  request(
    `/api/search?q=${encodeURIComponent(q || "")}` +
      (city ? `&city=${encodeURIComponent(city)}` : "")
  );

// --- Catalogue ---
// `city` (optional) scopes results to one city. encodeURIComponent guards names
// with spaces/hyphens like "Delhi-NCR".
export const getMovies = (city) =>
  request(`/api/movies${city ? `?city=${encodeURIComponent(city)}` : ""}`);
export const getMovie = (id) => request(`/api/movies/${id}`);
export const getMovieShows = (id, city) =>
  request(`/api/movies/${id}/shows${city ? `?city=${encodeURIComponent(city)}` : ""}`);

// --- Seat map ---
export const getSeatMap = (showId) => request(`/api/shows/${showId}/seatmap`);

// --- Booking (two-phase) ---
export const lockSeats = (showSeatIds, cartToken) =>
  request("/api/bookings/lock", {
    method: "POST",
    body: JSON.stringify({ show_seat_ids: showSeatIds, cart_token: cartToken }),
  });

export const confirmBooking = (payload) =>
  request("/api/bookings/confirm", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const getBooking = (id) => request(`/api/bookings/${id}`);
