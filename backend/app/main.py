"""
main.py — the FastAPI application entry point.
===============================================

This is the file uvicorn runs. It:
  1. Creates the FastAPI app (which auto-generates Swagger docs at /docs).
  2. Adds CORS so the Next.js frontend (http://localhost:3000) is allowed to call us.
  3. Registers the routers (movies, shows, bookings).

WHY CORS matters (common interview gotcha): browsers block a page on origin A from
calling an API on origin B unless the API explicitly allows it. Frontend (:3000)
and backend (:8000) are different origins, so without this middleware every fetch
from the UI would fail with a CORS error — even though curl would work fine.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import movies, shows, bookings, cities, search, auth

app = FastAPI(
    title="BookMyShow Clone API",
    version="1.0.0",
    description="Movie ticket booking backend. Core feature: race-free seat booking.",
)

app.add_middleware(
    CORSMiddleware,
    # The Next.js dev server. We list a couple of ports because 3000 may already
    # be taken on a dev machine, in which case Next falls back to 3001.
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movies.router)
app.include_router(shows.router)
app.include_router(bookings.router)
app.include_router(cities.router)
app.include_router(search.router)
app.include_router(auth.router)


@app.get("/api/health", tags=["meta"])
def health():
    """A trivial endpoint to confirm the server is up (used by smoke tests)."""
    return {"status": "ok"}
