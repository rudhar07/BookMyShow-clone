"""
schemas.py — THE API CONTRACT (Pydantic models)
================================================

WHAT is the difference between models.py and schemas.py?
  - models.py  = how data is stored      (SQLAlchemy, talks to the DB)
  - schemas.py = how data crosses the wire (Pydantic, talks to the client)

WHY keep them separate (a classic interview question)?
  1. Security: a DB row may have internal fields (held_by token, raw status)
     we don't want to leak. Schemas expose only what's safe.
  2. Stability: we can refactor the DB without breaking the public JSON shape.
  3. Validation: Pydantic auto-rejects bad input (missing fields, wrong types)
     and returns a clean 422 error — FastAPI does this for free from these classes.

Naming convention: `XCreate` = what the client SENDS; `XOut` = what we RETURN.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, ConfigDict


# `from_attributes=True` lets Pydantic build a response straight from a
# SQLAlchemy object (reading .attributes), so routers can `return db_movie`.
class _ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Movies ----------
class MovieOut(_ORMModel):
    id: int
    title: str
    language: str
    genre: str
    certificate: str
    duration_mins: int
    rating: float
    votes: str
    poster_url: Optional[str] = None
    is_promoted: bool


# ---------- Shows ----------
class ShowOut(_ORMModel):
    id: int
    movie_id: int
    screen_id: int
    start_time: datetime
    price_classic: float
    price_prime: float
    price_recliner: float
    audio_format: str = "2D"
    subtitle_lang: str = "ENG"
    is_cancellable: bool = True
    # Live availability, computed per request (NOT stored). Drives the pill colour
    # on the UI: green=AVAILABLE, amber=FAST_FILLING, grey=SOLD_OUT.
    available_seats: int = 0
    total_seats: int = 0
    availability: str = "AVAILABLE"


class VenueShowsOut(BaseModel):
    """Shows for one movie grouped under their venue — what the booking page needs."""
    venue_id: int
    venue_name: str
    address: Optional[str] = None
    brand: str = "default"
    shows: List[ShowOut]


# ---------- Seat map ----------
class SeatOut(_ORMModel):
    """One seat in the seat-selection grid, with its live status."""
    id: int                       # this is the ShowSeat id (what you lock/book)
    seat_id: int                  # the physical seat id
    row_label: str
    seat_number: int
    category: str
    price: float
    status: str                   # AVAILABLE / LOCKED / BOOKED


class SeatMapOut(BaseModel):
    show_id: int
    movie_title: str
    venue_name: str
    screen_name: str
    start_time: datetime
    seats: List[SeatOut]


# ---------- Locking ----------
class LockRequest(BaseModel):
    """Client asks to temporarily hold some seats while it pays."""
    show_seat_ids: List[int]
    # cart_token identifies this browser session. If omitted on lock, the server
    # mints one and returns it; the client must send it back to confirm.
    cart_token: Optional[str] = None


class LockResponse(BaseModel):
    cart_token: str
    locked_seat_ids: List[int]
    lock_expires_at: datetime


# ---------- Booking confirmation ----------
class ConfirmRequest(BaseModel):
    cart_token: str               # proves you hold the locks
    show_seat_ids: List[int]
    # In a real app the user comes from auth. For the assignment we accept basic
    # contact details and create/find the user.
    user_name: str
    user_email: EmailStr
    payment_method: str = "CARD"


class BookingSeatOut(_ORMModel):
    row_label: str
    seat_number: int
    category: str
    price: float


# ---------- Auth (mock sign-in) ----------
class LoginRequest(BaseModel):
    """Mock sign-in: real BMS uses phone+OTP; we accept name+email (+phone)."""
    name: str
    email: EmailStr
    phone: Optional[str] = None


class UserOut(_ORMModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None


class BookingOut(BaseModel):
    id: int
    status: str
    total_amount: float
    movie_title: str
    venue_name: str
    screen_name: str
    start_time: datetime
    seats: List[BookingSeatOut]
    payment_status: str
