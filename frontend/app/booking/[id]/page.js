/**
 * /booking/[id] — the confirmed TICKET page.
 * ==========================================
 * After a successful confirm we land here. We GET the booking by id and render
 * it like a ticket stub. Re-fetching (instead of passing data through navigation)
 * means a refresh or a shared link still works — the booking lives in the DB.
 */
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getBooking } from "../../lib/api";

function fmt(iso) {
  return new Date(iso).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}

export default function BookingPage({ params }) {
  const [booking, setBooking] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getBooking(params.id).then(setBooking).catch((e) => setError(e.message));
  }, [params.id]);

  if (error) return <div className="msg-error">{error}</div>;
  if (!booking) return <div className="loading">Loading ticket…</div>;

  return (
    <div className="ticket">
      <div className="ticket-head">
        <div style={{ fontSize: 13, opacity: 0.9 }}>Booking #{booking.id} · {booking.status}</div>
        <div style={{ fontSize: 24, fontWeight: 700 }}>{booking.movie_title}</div>
      </div>
      <div className="ticket-body">
        <div className="ticket-row"><span>Cinema</span><span>{booking.venue_name}</span></div>
        <div className="ticket-row"><span>Screen</span><span>{booking.screen_name}</span></div>
        <div className="ticket-row"><span>Showtime</span><span>{fmt(booking.start_time)}</span></div>
        <div className="ticket-row">
          <span>Seats</span>
          <span>{booking.seats.map((s) => `${s.row_label}${s.seat_number}`).join(", ")}</span>
        </div>
        <div className="ticket-row"><span>Payment</span><span>{booking.payment_status}</span></div>
        <div className="ticket-total">Total Paid: ₹{booking.total_amount}</div>
        <p style={{ marginTop: 20 }}>
          <Link href="/" className="see-all">‹ Back to home</Link>
        </p>
      </div>
    </div>
  );
}
