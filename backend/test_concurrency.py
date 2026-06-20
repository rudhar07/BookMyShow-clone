"""
test_concurrency.py — PROOF that we never double-book.
======================================================

Run:  python test_concurrency.py   (from backend/, after seeding)

The experiment: fire N threads that ALL try to lock the SAME seat at the same
time. A correct system lets exactly ONE win. We assert that.

This is the demo to run in an interview when asked "how do you know it works?"
"""

import threading
from app.database import SessionLocal
from app import models
from app.services import booking_service
from app.services.booking_service import BookingError

N_THREADS = 50


def main():
    db = SessionLocal()
    # Pick any AVAILABLE seat from show 1 to fight over.
    seat = (
        db.query(models.ShowSeat)
        .filter(models.ShowSeat.show_id == 1,
                models.ShowSeat.status == models.ShowSeatStatus.AVAILABLE)
        .first()
    )
    if seat is None:
        print("No available seat — re-run `python -m app.seed` first.")
        return
    target_id = seat.id
    db.close()

    winners = []
    losers = []
    lock = threading.Lock()

    def attempt(i):
        # Each thread = an independent user with its OWN db session and cart.
        s = SessionLocal()
        try:
            token, ids, exp = booking_service.lock_seats(s, [target_id], cart_token=f"cart-{i}")
            with lock:
                winners.append(i)
        except BookingError:
            with lock:
                losers.append(i)
        except Exception as e:
            with lock:
                losers.append(("err", str(e)))
        finally:
            s.close()

    threads = [threading.Thread(target=attempt, args=(i,)) for i in range(N_THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"Seat under contention : show_seat id={target_id}")
    print(f"Threads competing     : {N_THREADS}")
    print(f"WINNERS (got the lock): {len(winners)}  -> {winners}")
    print(f"LOSERS  (rejected)    : {len(losers)}")

    assert len(winners) == 1, f"DOUBLE-BOOK BUG: {len(winners)} winners!"
    print("\nPASS: exactly one winner. No double-booking.")


if __name__ == "__main__":
    main()
