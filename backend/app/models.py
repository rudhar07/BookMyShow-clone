"""
models.py — THE DATABASE SCHEMA (the heart of this assignment)
==============================================================

Each Python class below = one SQL table. SQLAlchemy (our ORM) translates
classes ↔ tables and objects ↔ rows, so we think in Python, not raw SQL.

HOW TO READ THIS FILE (top-down = catalogue → inventory → transactions)
-----------------------------------------------------------------------
  CATALOGUE (rarely changes):  City → Venue → Screen → Seat
                               Movie
  SCHEDULING:                  Show  (a Movie on a Screen at a time)
  PER-SHOW INVENTORY:          ShowSeat  ◀── the table that prevents double-booking
  TRANSACTIONS (per user):     User → Booking → BookingSeat → Payment

WHY this shape? The single most important modelling decision:
  A `Seat` is PHYSICAL (chair A1 in Audi-2 — exists forever).
  A `ShowSeat` is that seat *for one specific show* (A1 at the 9PM show on Friday).
  We must separate them, because A1 can be free at 9PM but sold at 6PM. Booking
  status lives on ShowSeat (per show), never on the physical Seat. Get this wrong
  and you literally cannot model a cinema.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey,
    Enum, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship

from .database import Base


# ===========================================================================
# ENUMS — fixed sets of allowed values. Using an Enum (not a free string) means
# the DB/ORM rejects typos like "BOKED" and documents the state machine.
# ===========================================================================

class SeatCategory(str, enum.Enum):
    """Price tiers. A seat's category decides how much it costs."""
    CLASSIC = "CLASSIC"      # cheapest, front/middle
    PRIME = "PRIME"          # better location
    RECLINER = "RECLINER"    # premium


class ShowSeatStatus(str, enum.Enum):
    """
    The state machine of a single seat for a single show. THIS is the crux.

        AVAILABLE ──user selects──▶ LOCKED ──user pays──▶ BOOKED
            ▲                          │
            └──── lock expires ────────┘   (10-min timer abandoned)

    Only AVAILABLE → LOCKED → BOOKED moves forward. A LOCKED seat whose timer
    expired is treated as AVAILABLE again. BOOKED is terminal.
    """
    AVAILABLE = "AVAILABLE"
    LOCKED = "LOCKED"
    BOOKED = "BOOKED"


class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"      # seats locked, awaiting payment
    CONFIRMED = "CONFIRMED"  # paid; seats are BOOKED
    CANCELLED = "CANCELLED"  # user/system released it
    EXPIRED = "EXPIRED"      # lock window passed before payment


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


# ===========================================================================
# CATALOGUE TABLES
# ===========================================================================

class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)   # "Bengaluru"

    venues = relationship("Venue", back_populates="city")


class Movie(Base):
    """A film. Independent of where/when it plays."""
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False, index=True)
    language = Column(String, nullable=False)        # "Hindi", "English"...
    genre = Column(String, nullable=False)           # "Action/Drama"
    certificate = Column(String, default="UA")       # "U", "UA", "A"
    duration_mins = Column(Integer, nullable=False)
    rating = Column(Float, default=0.0)              # 0–10, like BMS "8.5/10"
    votes = Column(String, default="0")              # display string e.g. "12.4K"
    poster_url = Column(String)                      # image shown on the card
    is_promoted = Column(Boolean, default=False)     # the "PROMOTED" tag
    release_date = Column(DateTime)

    shows = relationship("Show", back_populates="movie")


class Venue(Base):
    """A cinema (e.g. 'PVR: Orion Mall'). Lives in one city."""
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String)
    # Brand slug for the cinema-chain icon (pvr / inox / cinepolis_1 / amb / default).
    brand = Column(String, default="default")
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)

    city = relationship("City", back_populates="venues")
    screens = relationship("Screen", back_populates="venue")


class Screen(Base):
    """One auditorium inside a venue. 'Audi 1', 'Audi 2'. Holds physical seats."""
    __tablename__ = "screens"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)            # "Audi 1"
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)

    venue = relationship("Venue", back_populates="screens")
    seats = relationship("Seat", back_populates="screen")
    shows = relationship("Show", back_populates="screen")


class Seat(Base):
    """
    A PHYSICAL chair in a screen — e.g. row 'A', number 5. Exists permanently,
    independent of any show. Its category sets the base price tier.

    UNIQUE(screen_id, row_label, seat_number): you can't have two 'A5' chairs in
    the same auditorium. This is a data-integrity rule the DB enforces for us.
    """
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True)
    screen_id = Column(Integer, ForeignKey("screens.id"), nullable=False)
    row_label = Column(String, nullable=False)       # "A", "B", ...
    seat_number = Column(Integer, nullable=False)     # 1..N within the row
    category = Column(Enum(SeatCategory), nullable=False, default=SeatCategory.CLASSIC)

    screen = relationship("Screen", back_populates="seats")

    __table_args__ = (
        UniqueConstraint("screen_id", "row_label", "seat_number", name="uq_seat_in_screen"),
    )


# ===========================================================================
# SCHEDULING
# ===========================================================================

class Show(Base):
    """
    A specific screening: this Movie, on this Screen, starting at this time.
    Price multipliers per category can vary by show (evening shows cost more),
    so we store base prices here per category.
    """
    __tablename__ = "shows"

    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    screen_id = Column(Integer, ForeignKey("screens.id"), nullable=False)
    start_time = Column(DateTime, nullable=False, index=True)
    # Projection/sound format shown on the showtime pill (e.g. "2D", "LASER",
    # "ATMOS", "GOLD"). On BMS this is metadata of the screening, so it lives here.
    audio_format = Column(String, default="2D")
    # Subtitle/audio language tag shown as the small superscript on the pill ("ENG").
    subtitle_lang = Column(String, default="ENG")
    # Cancellation policy is PER SCREENING on BMS — premium formats are often
    # "Non-cancellable", regular shows allow cancellation. So it lives on Show.
    is_cancellable = Column(Boolean, nullable=False, default=True)

    # Price by category, decided at show level (e.g. weekend surge).
    price_classic = Column(Float, nullable=False, default=150)
    price_prime = Column(Float, nullable=False, default=250)
    price_recliner = Column(Float, nullable=False, default=450)

    movie = relationship("Movie", back_populates="shows")
    screen = relationship("Screen", back_populates="shows")
    show_seats = relationship("ShowSeat", back_populates="show")

    __table_args__ = (
        # No two shows can start on the same screen at the same instant.
        UniqueConstraint("screen_id", "start_time", name="uq_show_per_screen_time"),
    )


# ===========================================================================
# PER-SHOW INVENTORY — the table that makes double-booking impossible
# ===========================================================================

class ShowSeat(Base):
    """
    A physical Seat, materialised for ONE Show, with its live booking status.

    There is exactly ONE row per (show, seat) — enforced by the UNIQUE constraint
    below. That constraint is the *hard* guarantee: even with a perfect storm of
    concurrent requests, the database physically cannot create a second row for
    the same seat in the same show, so a seat can never be double-sold.

    Locking fields:
      status         : AVAILABLE / LOCKED / BOOKED (the state machine)
      lock_expires_at: when a LOCKED seat auto-frees (we give users ~10 min to pay)
      held_by        : an opaque token (a "cart" id) identifying who holds the lock,
                       so only that holder may convert the lock into a booking.

    WHY a row per seat per show instead of computing availability on the fly?
      - We need somewhere to store the LOCKED state + expiry per seat per show.
      - A conditional UPDATE on this row is our atomic "claim this seat" operation
        (see booking_service.py). That is the whole concurrency trick.
    """
    __tablename__ = "show_seats"

    id = Column(Integer, primary_key=True)
    show_id = Column(Integer, ForeignKey("shows.id"), nullable=False)
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=False)

    status = Column(Enum(ShowSeatStatus), nullable=False, default=ShowSeatStatus.AVAILABLE)
    price = Column(Float, nullable=False)            # frozen price for this seat+show
    lock_expires_at = Column(DateTime, nullable=True)
    held_by = Column(String, nullable=True)          # cart/session token holding the lock

    show = relationship("Show", back_populates="show_seats")
    seat = relationship("Seat")

    __table_args__ = (
        # THE invariant: one inventory row per seat per show. Last line of defence.
        UniqueConstraint("show_id", "seat_id", name="uq_seat_per_show"),
        # Speeds up the very common query "give me all seats for show X".
        Index("ix_showseat_show", "show_id"),
    )


# ===========================================================================
# TRANSACTIONS
# ===========================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    phone = Column(String)

    bookings = relationship("Booking", back_populates="user")


class Booking(Base):
    """
    One purchase = one Booking, covering one or more seats of one show.
    Money lives here (total_amount) so we never re-sum seats to know what was charged.
    """
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    show_id = Column(Integer, ForeignKey("shows.id"), nullable=False)
    status = Column(Enum(BookingStatus), nullable=False, default=BookingStatus.PENDING)
    total_amount = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="bookings")
    show = relationship("Show")
    seats = relationship("BookingSeat", back_populates="booking")
    payment = relationship("Payment", back_populates="booking", uselist=False)


class BookingSeat(Base):
    """
    Link row: which ShowSeats belong to which Booking (a many-to-many bridge,
    one Booking ↔ many ShowSeats).

    UNIQUE(show_seat_id): a single show-seat can appear in AT MOST ONE booking.
    A second guarantee against double-selling, at the link level.
    """
    __tablename__ = "booking_seats"

    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    show_seat_id = Column(Integer, ForeignKey("show_seats.id"), nullable=False)

    booking = relationship("Booking", back_populates="seats")
    show_seat = relationship("ShowSeat")

    __table_args__ = (
        UniqueConstraint("show_seat_id", name="uq_showseat_one_booking"),
    )


class Payment(Base):
    """A (mock) payment attached to a booking. One booking → one payment."""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False, unique=True)
    amount = Column(Float, nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    method = Column(String, default="CARD")          # CARD / UPI / WALLET (mock)
    created_at = Column(DateTime, default=datetime.utcnow)

    booking = relationship("Booking", back_populates="payment")
