"""
booking_service.py — THE CONCURRENCY STORY (most important code to defend)
==========================================================================

The whole assignment hinges on one question:

    "Two users click the same seat at the same millisecond. How do you ensure
     exactly one of them gets it?"

This file is the answer. It implements a 2-phase flow used by every real ticketing
system (cinemas, airlines, Ticketmaster):

    PHASE 1  LOCK     : temporarily hold the seats (status AVAILABLE → LOCKED)
                        with a 10-minute expiry, so the user has time to pay.
    PHASE 2  CONFIRM  : on payment, convert the holder's locks to a real booking
                        (status LOCKED → BOOKED). Anyone else is rejected.

THE ATOMIC PRIMITIVE (the trick to memorise)
--------------------------------------------
We never do "SELECT then decide then UPDATE" in two steps — that has a race window
where two requests both read AVAILABLE. Instead we use ONE conditional UPDATE:

    UPDATE show_seats
       SET status='LOCKED', held_by=:token, lock_expires_at=:exp
     WHERE id=:seat_id
       AND (status='AVAILABLE'
            OR (status='LOCKED' AND lock_expires_at < :now))   -- expired lock = free

The database guarantees this UPDATE is atomic. We then check `rowcount`:
  - rowcount == 1  → WE won the seat.
  - rowcount == 0  → someone else holds it; we lost. No race possible, because the
                     DB applied the writes one at a time (SQLite serialises writers).

If ANY seat in the batch can't be claimed, we roll back the whole transaction so a
user never ends up holding a partial, useless set of seats (all-or-nothing).

WHY this beats a naive Python lock: a Python `threading.Lock` only protects ONE
server process. Two servers (or two workers) would each have their own lock and
still double-sell. The DB is the single shared arbiter — it's the only correct
place to settle the race.
"""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import update, and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .. import models
from ..models import ShowSeatStatus, BookingStatus, PaymentStatus


LOCK_DURATION = timedelta(minutes=10)   # how long a held seat stays reserved


class BookingError(Exception):
    """Raised for any business-rule failure (seat taken, lock expired, ...).

    The router turns this into a clean HTTP 409/400 instead of a 500 crash.
    """


# ---------------------------------------------------------------------------
# PHASE 1 — LOCK
# ---------------------------------------------------------------------------
def lock_seats(db: Session, show_seat_ids: list[int], cart_token: str | None):
    """
    Try to lock all requested seats for one cart. All-or-nothing.

    Returns (cart_token, locked_ids, expires_at) on success.
    Raises BookingError naming the first seat we couldn't get.
    """
    if not show_seat_ids:
        raise BookingError("No seats selected.")

    # Mint a cart token if the client didn't bring one. This token is the user's
    # claim ticket — they must present it at confirm time.
    token = cart_token or uuid.uuid4().hex
    now = datetime.utcnow()
    expires = now + LOCK_DURATION

    try:
        for seat_id in show_seat_ids:
            # The atomic conditional UPDATE described in the header.
            # A seat is claimable if it's AVAILABLE, OR it's LOCKED but expired,
            # OR it's already LOCKED *by this same cart* (re-selecting is idempotent).
            stmt = (
                update(models.ShowSeat)
                .where(
                    models.ShowSeat.id == seat_id,
                    or_(
                        models.ShowSeat.status == ShowSeatStatus.AVAILABLE,
                        and_(
                            models.ShowSeat.status == ShowSeatStatus.LOCKED,
                            models.ShowSeat.lock_expires_at < now,
                        ),
                        and_(
                            models.ShowSeat.status == ShowSeatStatus.LOCKED,
                            models.ShowSeat.held_by == token,
                        ),
                    ),
                )
                .values(
                    status=ShowSeatStatus.LOCKED,
                    held_by=token,
                    lock_expires_at=expires,
                )
            )
            result = db.execute(stmt)

            # rowcount == 0 means the WHERE matched nothing → seat not claimable.
            if result.rowcount != 1:
                db.rollback()   # release any seats we locked earlier in this loop
                raise BookingError(f"Seat {seat_id} is no longer available.")

        # All seats claimed → make the locks permanent (until they expire).
        db.commit()
        return token, show_seat_ids, expires

    except BookingError:
        raise
    except Exception:
        db.rollback()
        raise


# ---------------------------------------------------------------------------
# PHASE 2 — CONFIRM (mock payment + create the booking)
# ---------------------------------------------------------------------------
def confirm_booking(
    db: Session,
    cart_token: str,
    show_seat_ids: list[int],
    user_name: str,
    user_email: str,
    payment_method: str = "CARD",
):
    """
    Convert this cart's LOCKED seats into a CONFIRMED booking.

    Guards (each maps to a real failure mode):
      - seat must still be LOCKED, held_by THIS cart, and not expired
        → otherwise the lock lapsed or belongs to someone else.
    Everything happens in ONE transaction so we can't half-book.
    """
    if not show_seat_ids:
        raise BookingError("No seats to confirm.")

    now = datetime.utcnow()

    try:
        # Re-load the seats and validate ownership of the locks.
        seats = (
            db.query(models.ShowSeat)
            .filter(models.ShowSeat.id.in_(show_seat_ids))
            .all()
        )
        if len(seats) != len(show_seat_ids):
            raise BookingError("Some seats no longer exist.")

        show_ids = {s.show_id for s in seats}
        if len(show_ids) != 1:
            # A booking must be for a single show — mixing shows is a client bug.
            raise BookingError("All seats must belong to the same show.")

        for s in seats:
            valid = (
                s.status == ShowSeatStatus.LOCKED
                and s.held_by == cart_token
                and s.lock_expires_at is not None
                and s.lock_expires_at >= now
            )
            if not valid:
                raise BookingError(
                    f"Lock on seat {s.id} is invalid or expired — please reselect."
                )

        # Find or create the user (no auth in the assignment).
        user = db.query(models.User).filter(models.User.email == user_email).first()
        if user is None:
            user = models.User(name=user_name, email=user_email)
            db.add(user)
            db.flush()   # assign user.id

        show_id = show_ids.pop()
        total = sum(s.price for s in seats)

        booking = models.Booking(
            user_id=user.id,
            show_id=show_id,
            status=BookingStatus.CONFIRMED,
            total_amount=total,
        )
        db.add(booking)
        db.flush()   # assign booking.id

        # Mark each seat BOOKED and link it to the booking.
        # The UNIQUE(show_seat_id) on BookingSeat is the final hard stop against
        # the same seat being attached to two bookings.
        for s in seats:
            s.status = ShowSeatStatus.BOOKED
            s.lock_expires_at = None
            db.add(models.BookingSeat(booking_id=booking.id, show_seat_id=s.id))

        # Mock payment — always succeeds here, but modelled as its own row so the
        # design extends to a real gateway (PENDING → SUCCESS/FAILED) later.
        payment = models.Payment(
            booking_id=booking.id,
            amount=total,
            status=PaymentStatus.SUCCESS,
            method=payment_method,
        )
        db.add(payment)

        db.commit()
        db.refresh(booking)
        return booking

    except IntegrityError:
        # The DB's UNIQUE constraint fired — a concurrent confirm beat us to it.
        db.rollback()
        raise BookingError("One of these seats was just booked by someone else.")
    except BookingError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


# ---------------------------------------------------------------------------
# Housekeeping — free abandoned locks (so seats don't stay stuck forever)
# ---------------------------------------------------------------------------
def release_expired_locks(db: Session) -> int:
    """
    Flip any LOCKED-but-expired seats back to AVAILABLE. In production a cron job
    or background task calls this periodically; we also call it lazily before
    serving a seat map so users always see fresh availability.
    """
    now = datetime.utcnow()
    stmt = (
        update(models.ShowSeat)
        .where(
            models.ShowSeat.status == ShowSeatStatus.LOCKED,
            models.ShowSeat.lock_expires_at < now,
        )
        .values(status=ShowSeatStatus.AVAILABLE, held_by=None, lock_expires_at=None)
    )
    result = db.execute(stmt)
    db.commit()
    return result.rowcount
