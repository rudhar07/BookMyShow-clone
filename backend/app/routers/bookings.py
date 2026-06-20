"""
routers/bookings.py — the booking flow over HTTP.
==================================================

Three endpoints map onto the two-phase design from booking_service.py:

  POST /api/bookings/lock     → PHASE 1: hold seats, get a cart_token + timer
  POST /api/bookings/confirm  → PHASE 2: pay + finalise into a booking
  GET  /api/bookings/{id}     → fetch a confirmed booking (the ticket page)

The router's only jobs: call the service, and translate a BookingError into the
RIGHT HTTP status. 409 Conflict is the correct code for "seat taken" — it means
"your request is valid but conflicts with current state."
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services import booking_service
from ..services.booking_service import BookingError

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


@router.post("/lock", response_model=schemas.LockResponse)
def lock(req: schemas.LockRequest, db: Session = Depends(get_db)):
    """PHASE 1 — temporarily reserve the chosen seats."""
    try:
        token, ids, expires = booking_service.lock_seats(
            db, req.show_seat_ids, req.cart_token
        )
    except BookingError as e:
        # 409 Conflict: the seat exists but isn't claimable right now.
        raise HTTPException(status_code=409, detail=str(e))
    return schemas.LockResponse(
        cart_token=token, locked_seat_ids=ids, lock_expires_at=expires
    )


@router.post("/confirm", response_model=schemas.BookingOut)
def confirm(req: schemas.ConfirmRequest, db: Session = Depends(get_db)):
    """PHASE 2 — pay and finalise. Returns the ticket."""
    try:
        booking = booking_service.confirm_booking(
            db,
            cart_token=req.cart_token,
            show_seat_ids=req.show_seat_ids,
            user_name=req.user_name,
            user_email=req.user_email,
            payment_method=req.payment_method,
        )
    except BookingError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return _booking_to_out(booking)


@router.get("/{booking_id}", response_model=schemas.BookingOut)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).get(booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return _booking_to_out(booking)


def _booking_to_out(booking: models.Booking) -> schemas.BookingOut:
    """Flatten the booking + its relations into the public response shape."""
    show = booking.show
    return schemas.BookingOut(
        id=booking.id,
        status=booking.status.value,
        total_amount=booking.total_amount,
        movie_title=show.movie.title,
        venue_name=show.screen.venue.name,
        screen_name=show.screen.name,
        start_time=show.start_time,
        seats=[
            schemas.BookingSeatOut(
                row_label=bs.show_seat.seat.row_label,
                seat_number=bs.show_seat.seat.seat_number,
                category=bs.show_seat.seat.category.value,
                price=bs.show_seat.price,
            )
            for bs in booking.seats
        ],
        payment_status=booking.payment.status.value if booking.payment else "NONE",
    )
