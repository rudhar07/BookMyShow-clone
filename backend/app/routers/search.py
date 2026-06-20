"""
routers/search.py — the global search box.
===========================================
  GET /api/search?q=<text>&city=<city>
    → { movies: [...], venues: [...] }

Rules (mirrors what the UI needs):
  • movies  — match by title (case-insensitive). A movie is global, so we don't
    scope it to the city.
  • venues  — match cinemas by name, scoped to the SELECTED city (you only want
    cinemas you can actually go to).
  • empty q — return "trending": the top movies (promoted/highest-rated), no venues,
    exactly like BookMyShow's "Popular/Trending Results" panel.

`ilike` gives case-insensitive matching; on SQLite SQLAlchemy renders it as
`lower(col) LIKE lower(:q)`, so "obse" matches "Obsession".
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

router = APIRouter(prefix="/api/search", tags=["search"])

LIMIT = 8


@router.get("")
def search(q: str = "", city: str | None = None, db: Session = Depends(get_db)):
    term = (q or "").strip()

    # --- Movies: trending when empty, else title match ---
    mq = db.query(models.Movie)
    if term:
        mq = mq.filter(models.Movie.title.ilike(f"%{term}%"))
    movies = (
        mq.order_by(models.Movie.is_promoted.desc(), models.Movie.rating.desc())
        .limit(LIMIT)
        .all()
    )

    # --- Venues: only when searching, scoped to the chosen city ---
    venues = []
    if term:
        vq = db.query(models.Venue)
        if city:
            vq = vq.join(models.City, models.Venue.city_id == models.City.id) \
                   .filter(models.City.name == city)
        venues = vq.filter(models.Venue.name.ilike(f"%{term}%")).limit(LIMIT).all()

    return {
        "movies": [
            {"id": m.id, "title": m.title, "genre": m.genre, "language": m.language}
            for m in movies
        ],
        "venues": [
            {"id": v.id, "name": v.name, "address": v.address}
            for v in venues
        ],
    }
