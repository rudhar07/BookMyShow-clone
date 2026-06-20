"""
routers/shows.py — the seat map for a show.
============================================

  GET /api/shows/{id}/seatmap → every seat for the show with its live status.

Before returning, we lazily free expired locks so users always see truthful
availability without waiting on a background job. This is cheap (one UPDATE) and
keeps the demo honest.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services import booking_service

router = APIRouter(prefix="/api/shows", tags=["shows"])


@router.get("/{show_id}/seatmap", response_model=schemas.SeatMapOut)
def get_seatmap(show_id: int, db: Session = Depends(get_db)):
    show = db.query(models.Show).get(show_id)
    if show is None:
        raise HTTPException(status_code=404, detail="Show not found")

    # Free abandoned locks first so AVAILABLE counts are accurate.
    booking_service.release_expired_locks(db)

    show_seats = (
        db.query(models.ShowSeat)
        .filter(models.ShowSeat.show_id == show_id)
        .join(models.Seat, models.ShowSeat.seat_id == models.Seat.id)
        .order_by(models.Seat.row_label, models.Seat.seat_number)
        .all()
    )

    seats = [
        schemas.SeatOut(
            id=ss.id,
            seat_id=ss.seat_id,
            row_label=ss.seat.row_label,
            seat_number=ss.seat.seat_number,
            category=ss.seat.category.value,
            price=ss.price,
            status=ss.status.value,
        )
        for ss in show_seats
    ]

    return schemas.SeatMapOut(
        show_id=show.id,
        movie_title=show.movie.title,
        venue_name=show.screen.venue.name,
        screen_name=show.screen.name,
        start_time=show.start_time,
        seats=seats,
    )
