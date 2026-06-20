# BookMyShow Clone — Full-Stack Project

A clone of BookMyShow: **Next.js** frontend, **FastAPI** backend, **SQLite** database.
The heart of the project is the **booking subsystem** — designing a database and
flow that guarantees *no seat is ever sold twice*, even when many users click at
the same instant.


---

## 1. High-level architecture

```
┌─────────────────┐      HTTP/JSON      ┌──────────────────┐      SQL       ┌────────────┐
│  Next.js (UI)   │  ───────────────▶   │  FastAPI (logic) │ ───────────▶   │  SQLite    │
│  React, pages   │  ◀───────────────   │  routers+services│ ◀───────────   │  (file DB) │
└─────────────────┘                     └──────────────────┘                └────────────┘
     :3000                                    :8000                         bookmyshow.db
```

**Why three layers?**
- The **frontend** can be swapped (web today, mobile tomorrow) without touching rules.
- The **backend** enforces business rules *no client can bypass* (clients lie; servers don't trust them).
- The **database** enforces *hard* invariants (unique seat per show) the backend might forget.

Each layer distrusts the layer above it. That is the single most important idea in the project.

---

## 2. The core problem: double-booking

If 1000 people want the last seat in a hall, exactly **one** must win. This is a
**concurrency** problem. Our defence has three lines (explained fully in
`backend/app/services/booking_service.py`):

1. **Application logic** — we check "is this seat free?" before booking.
2. **A `LOCKED` state with an expiry** — when you pick a seat we *temporarily reserve*
   it for ~10 minutes so you can pay. If you abandon, the lock expires and the seat frees.
3. **A database UNIQUE constraint** — even if logic has a race, the DB physically
   refuses to insert two bookings for the same `(show_id, seat_id)`. This is the
   last line of defence and the one you can never bypass.

> Interview soundbite: *"Optimistic checks for UX, a timed lock for fairness, and a
> DB unique constraint for correctness. Defence in depth."*

---

## 3. Folder layout

```
Clone-2/
├── backend/
│   ├── app/
│   │   ├── database.py        # SQLite connection + session factory
│   │   ├── models.py          # SQLAlchemy ORM tables (THE schema)
│   │   ├── schemas.py         # Pydantic request/response shapes (the API contract)
│   │   ├── seed.py            # Fills the DB with demo movies/venues/shows/seats
│   │   ├── main.py            # FastAPI app + CORS + router registration
│   │   ├── routers/           # HTTP endpoints, grouped by resource
│   │   └── services/          # Business logic (booking_service = seat locking)
│   └── requirements.txt
└── frontend/                  # Next.js app (App Router)
```

**Why split `routers/` and `services/`?** Routers handle *HTTP* (parse request,
return status codes). Services handle *logic* (what it means to book). Keeping them
apart means the booking logic is testable without a web server and reusable from,
say, a CLI or a background job.

---

## 4. How to run

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows;  source .venv/bin/activate on mac/linux
pip install -r requirements.txt
python -m app.seed              # create + populate bookmyshow.db
uvicorn app.main:app --reload   # http://localhost:8000  (docs at /docs)

# Frontend (new terminal)
cd frontend
npm install
npm run dev                     # http://localhost:3000
```

---

## 5. Reading order for the interviewer

1. `backend/app/models.py` — the data model. Start here; everything serves the data.
2. `backend/app/services/booking_service.py` — the concurrency story.
3. `backend/app/routers/bookings.py` — how the flow is exposed over HTTP.
4. `frontend/` — how a user walks through movie → show → seats → confirm.

Each file has a teaching header comment explaining *what, why, and how*.
