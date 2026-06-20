"""
routers/cities.py — list the cities that actually have shows to book.
=====================================================================
  GET /api/cities → [{id, name}]  (used to populate the city-picker modal)

Only seeded cities appear here, so the frontend can mark which cities are
"available" (bookable) vs. "coming soon".
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

router = APIRouter(prefix="/api/cities", tags=["cities"])


@router.get("")
def list_cities(db: Session = Depends(get_db)):
    cities = db.query(models.City).order_by(models.City.name).all()
    return [{"id": c.id, "name": c.name} for c in cities]
