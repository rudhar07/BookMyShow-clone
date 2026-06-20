/**
 * /shows/[id] — SEAT SELECTION + booking (the client side of the hard part).
 * ===========================================================================
 * This page mirrors the backend's two-phase flow:
 *
 *   1. User toggles AVAILABLE seats  → local "selected" state.
 *   2. Click "Pay"  → POST /lock     → backend reserves them, returns a cart_token.
 *                     If a seat was just taken, backend says 409 and we refresh
 *                     the map so the user sees reality.
 *   3. Fill name/email in the modal → POST /confirm with the cart_token →
 *                     booking created → redirect to the ticket page.
 *
 * Key teaching point: the client NEVER decides if a seat is free. It only asks.
 * The server is the single source of truth, which is why concurrency is safe.
 */
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getSeatMap, lockSeats, confirmBooking } from "../../lib/api";
import { useAuth } from "../../components/AuthContext";

function fmt(iso) {
  const d = new Date(iso);
  return d.toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}

export default function SeatPage({ params }) {
  const router = useRouter();
  const { user } = useAuth();
  const [map, setMap] = useState(null);
  const [selected, setSelected] = useState([]); // show_seat ids
  const [error, setError] = useState(null);
  const [cartToken, setCartToken] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);

  const loadMap = () =>
    getSeatMap(params.id).then(setMap).catch((e) => setError(e.message));

  useEffect(() => { loadMap(); }, [params.id]);

  // If the user is signed in, pre-fill the booking form with their details.
  useEffect(() => {
    if (user) { setName(user.name); setEmail(user.email); }
  }, [user]);

  if (error && !map) return <div className="msg-error">{error}</div>;
  if (!map) return <div className="loading">Loading seat map…</div>;

  // Group seats by row so we can render the auditorium grid.
  const rows = {};
  for (const s of map.seats) {
    (rows[s.row_label] ||= []).push(s);
  }

  const toggle = (seat) => {
    if (seat.status !== "AVAILABLE") return; // can't pick BOOKED/LOCKED
    setSelected((prev) =>
      prev.includes(seat.id)
        ? prev.filter((x) => x !== seat.id)
        : [...prev, seat.id]
    );
  };

  const selectedSeats = map.seats.filter((s) => selected.includes(s.id));
  const total = selectedSeats.reduce((sum, s) => sum + s.price, 0);

  // PHASE 1: lock the seats, then open the payment modal.
  const handlePay = async () => {
    setError(null);
    setBusy(true);
    try {
      const res = await lockSeats(selected, cartToken);
      setCartToken(res.cart_token);
      setShowModal(true);
    } catch (e) {
      // Most likely a 409: someone grabbed a seat first. Refresh to show truth.
      setError(e.message);
      setSelected([]);
      await loadMap();
    } finally {
      setBusy(false);
    }
  };

  // PHASE 2: confirm + (mock) pay.
  const handleConfirm = async () => {
    setError(null);
    setBusy(true);
    try {
      const booking = await confirmBooking({
        cart_token: cartToken,
        show_seat_ids: selected,
        user_name: name,
        user_email: email,
        payment_method: "CARD",
      });
      router.push(`/booking/${booking.id}`);
    } catch (e) {
      setError(e.message);
      setBusy(false);
    }
  };

  return (
    <div className="seat-page">
      <h2>{map.movie_title}</h2>
      <div className="card-sub">
        {map.venue_name} · {map.screen_name} · {fmt(map.start_time)}
      </div>

      {error && <div className="msg-error">{error}</div>}

      <div className="screen-banner">
        <div className="screen-bar" />
        <div className="screen-label">SCREEN THIS WAY</div>
      </div>

      {Object.entries(rows).map(([rowLabel, seats]) => (
        <div key={rowLabel}>
          {seats[0] && (
            <div className="seat-row">
              <span className="row-label">{rowLabel}</span>
              {seats.map((seat) => {
                const isSel = selected.includes(seat.id);
                const cls = isSel
                  ? "seat selected"
                  : seat.status === "BOOKED" || seat.status === "LOCKED" 
                  ? "seat booked"
                  // : seat.status === "LOCKED"
                  // ? "seat locked"
                  : "seat";
                return (
                  <div
                    key={seat.id}
                    className={cls}
                    title={`${seat.category} · ₹${seat.price}`}
                    onClick={() => toggle(seat)}
                  >
                    {seat.seat_number}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ))}

      <div className="legend">
        <span><span className="box" style={{ border: "1px solid #1ea83c" }} /> Available</span>
        <span><span className="box" style={{ background: "#1ea83c" }} /> Selected</span>
        {/* <span><span className="box" style={{ background: "#ffe9b3", border: "1px solid #e0b94e" }} /> Locked</span> */}
        <span><span className="box" style={{ background: "#eee" }} /> Sold </span>
      </div>

      <div className="paybar">
        {selected.length > 0 ? (
          <button className="btn-primary" onClick={handlePay} disabled={busy}>
            Pay ₹{total} · {selected.length} seat{selected.length > 1 ? "s" : ""}
          </button>
        ) : (
          <button className="btn-primary" disabled>
            Select seats to continue
          </button>
        )}
      </div>

      {showModal && (
        <div className="overlay">
          <div className="modal">
            <h3>Almost there — ₹{total}</h3>
            <div className="card-sub">
              {selectedSeats.map((s) => `${s.row_label}${s.seat_number}`).join(", ")}
            </div>
            <label>Name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" />
            <label>Email</label>
            <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
            {error && <div className="msg-error">{error}</div>}
            <div className="modal-actions">
              <button className="btn-ghost" onClick={() => setShowModal(false)} disabled={busy}>
                Cancel
              </button>
              <button
                className="btn-primary"
                style={{ flex: 1 }}
                onClick={handleConfirm}
                disabled={busy || !name || !email}
              >
                {busy ? "Processing…" : "Pay now"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
