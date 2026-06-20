"""
routers/movies.py — read endpoints for the catalogue.
======================================================

Endpoints:
  GET /api/movies              → list movies (the home-page rail)
  GET /api/movies/{id}         → one movie's details
  GET /api/movies/{id}/shows   → that movie's shows, grouped by venue (booking page)

These are pure reads, so no locking/transactions — just queries shaped into the
response schemas. Routers stay THIN: parse path/query, call the DB, return.
"""

from collections import OrderedDict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..models import ShowSeatStatus

router = APIRouter(prefix="/api/movies", tags=["movies"])

# If fewer than 20% of seats remain we call it "fast filling" — the amber pill.
FAST_FILLING_THRESHOLD = 0.20


def _availability_label(available: int, total: int) -> str:
    """Turn raw counts into the 3 states the UI colours by."""
    if total == 0 or available == 0:
        return "SOLD_OUT"
    if available / total < FAST_FILLING_THRESHOLD:
        return "FAST_FILLING"
    return "AVAILABLE"


def _in_city(query, city: str):
    """Restrict a Show/Movie query to a city by walking Show→Screen→Venue→City."""
    return (
        query
        .join(models.Screen, models.Show.screen_id == models.Screen.id)
        .join(models.Venue, models.Screen.venue_id == models.Venue.id)
        .join(models.City, models.Venue.city_id == models.City.id)
        .filter(models.City.name == city)
    )


@router.get("", response_model=list[schemas.MovieOut])
def list_movies(city: str | None = None, db: Session = Depends(get_db)):
    """
    Movies, promoted first. If `city` is given, return only movies that actually
    have a show in that city (Movie→Show→Screen→Venue→City). A Movie is global;
    the city scopes it via where its shows run.
    """
    q = db.query(models.Movie)
    if city:
        q = _in_city(q.join(models.Show, models.Show.movie_id == models.Movie.id), city).distinct()
    return q.order_by(models.Movie.is_promoted.desc(), models.Movie.rating.desc()).all()


@router.get("/{movie_id}", response_model=schemas.MovieOut)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(models.Movie).get(movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.get("/{movie_id}/shows", response_model=list[schemas.VenueShowsOut])
def get_movie_shows(movie_id: int, city: str | None = None, db: Session = Depends(get_db)):
    """
    Shows for a movie, grouped by venue — exactly the structure the booking page
    renders ("PVR Orion: 10:00 | 2:00 | 6:00"). We group in Python because it's a
    small result set; for huge data you'd push grouping into SQL.
    """
    movie = db.query(models.Movie).get(movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    shows_q = db.query(models.Show).filter(models.Show.movie_id == movie_id)
    if city:
        shows_q = _in_city(shows_q, city)   # only this city's venues
    shows = shows_q.order_by(models.Show.start_time).all()
    show_ids = [s.id for s in shows]

    # --- AVAILABILITY in ONE aggregate query (the interview-worthy bit) ---
    # Instead of N queries ("for each show, count its free seats" — the N+1 problem),
    # we ask the DB ONCE: "group all these shows' seats by show and status, count
    # each group." GROUP BY does the counting set-based, inside the DB, where it's
    # fast. We then look up the numbers in Python dicts.
    rows = (
        db.query(
            models.ShowSeat.show_id,
            models.ShowSeat.status,
            func.count().label("n"),
        )
        .filter(models.ShowSeat.show_id.in_(show_ids))
        .group_by(models.ShowSeat.show_id, models.ShowSeat.status)
        .all()
    )
    total_by_show: dict[int, int] = {}
    avail_by_show: dict[int, int] = {}
    for show_id, status, n in rows:
        total_by_show[show_id] = total_by_show.get(show_id, 0) + n
        if status == ShowSeatStatus.AVAILABLE:
            avail_by_show[show_id] = avail_by_show.get(show_id, 0) + n

    grouped: "OrderedDict[int, schemas.VenueShowsOut]" = OrderedDict()
    for show in shows:
        venue = show.screen.venue
        if venue.id not in grouped:
            grouped[venue.id] = schemas.VenueShowsOut(
                venue_id=venue.id, venue_name=venue.name,
                address=venue.address, brand=venue.brand, shows=[],
            )
        total = total_by_show.get(show.id, 0)
        avail = avail_by_show.get(show.id, 0)
        grouped[venue.id].shows.append(schemas.ShowOut(
            id=show.id, movie_id=show.movie_id, screen_id=show.screen_id,
            start_time=show.start_time,
            price_classic=show.price_classic, price_prime=show.price_prime,
            price_recliner=show.price_recliner, audio_format=show.audio_format,
            subtitle_lang=show.subtitle_lang, is_cancellable=show.is_cancellable,
            available_seats=avail, total_seats=total,
            availability=_availability_label(avail, total),
        ))

    return list(grouped.values())
