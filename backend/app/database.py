"""
database.py — the single place that knows HOW to talk to SQLite.
=================================================================

WHAT this file does
-------------------
It builds three things every other file reuses:
  1. `engine`      — the low-level connection pool to the SQLite file.
  2. `SessionLocal`— a factory that hands out short-lived DB "sessions"
                     (one unit of work = one session).
  3. `Base`        — the parent class every ORM table inherits from.

WHY centralise it
-----------------
If the connection details lived in 10 files, changing the DB (say, to Postgres
in production) would mean 10 edits. Here it's ONE line. This is the standard
SQLAlchemy pattern and what an interviewer expects to see.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

# The DB is just a file next to the code. "sqlite:///./bookmyshow.db" means
# "a SQLite database stored in the file ./bookmyshow.db".
SQLALCHEMY_DATABASE_URL = "sqlite:///./bookmyshow.db"

# create_engine = open the door to the database.
#
# check_same_thread=False : SQLite by default forbids using one connection from
#   multiple threads. FastAPI serves requests on a thread pool, so we relax that.
#   It's safe here because each request uses its OWN session (see get_db below).
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)


# ---------------------------------------------------------------------------
# Turn ON foreign-key enforcement in SQLite.
#
# Surprising fact every interviewer loves: SQLite does NOT enforce foreign keys
# by default — you must switch it on per-connection with `PRAGMA foreign_keys=ON`.
# Without this, you could insert a booking pointing at a show that doesn't exist.
# We hook into every new connection to enable it.
# ---------------------------------------------------------------------------
@event.listens_for(engine, "connect")
def _enable_sqlite_fks(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    # WAL = Write-Ahead Logging. It lets readers keep reading while one writer
    # writes, which improves concurrency — directly relevant to a booking site.
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


# SessionLocal() gives us a new session. A session is a "staging area": you add
# objects, then commit() to flush them to disk (or rollback() to discard).
#  - autoflush=False : we control exactly when SQL is sent (important for locking).
#  - autocommit=False: nothing is permanent until we explicitly commit().
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Every model class (Movie, Show, Seat...) will subclass this.
Base = declarative_base()


def get_db():
    """
    FastAPI dependency: open a session, hand it to the endpoint, ALWAYS close it.

    The `yield` pattern guarantees the `finally` runs even if the endpoint raises,
    so we never leak connections. Endpoints declare `db: Session = Depends(get_db)`
    and FastAPI wires this in automatically.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
