"""
seed.py — create the tables and fill them with realistic demo data.
===================================================================

Run with:  python -m app.seed     (from the backend/ folder)

WHAT it does, in order:
  1. Drop + recreate every table (clean slate each run — fine for local development).
  2. Insert a city, movies (matching the BookMyShow screenshot), venues, screens.
  3. Generate a physical seat grid for each screen.
  4. Create shows (a movie playing on a screen at a time).
  5. MATERIALISE ShowSeats: for every show, one inventory row per physical seat,
     all starting AVAILABLE. This is the step that makes seats bookable.

WHY a dedicated seed script (interview point)?
  A fresh clone of the repo is useless with an empty DB. Seeding gives a
  reproducible, known starting state — essential for demos and for tests.
"""

from datetime import datetime, timedelta

from .database import Base, engine, SessionLocal
from . import models
from .models import SeatCategory, ShowSeatStatus


def reset_schema():
    """Drop everything then create fresh tables from the models. Clean slate."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# AUDITORIUM LAYOUTS — each is a different physical room shape.
#
# A layout = how many rows, how many seats per row, and how those rows split
# into price tiers (front CLASSIC → middle PRIME → back RECLINER).
# Real cinemas differ: a boutique GOLD screen is small + all-recliner; an IMAX
# is huge. We model that variety so no two audi types look identical.
#
# `tiers` is a list of (number_of_rows, category) and MUST sum to `rows`.
# ---------------------------------------------------------------------------
LAYOUTS = [
    {  # 0: Standard multiplex — 10 rows × 18 = 180 seats
        "name": "Standard", "rows": 10, "cols": 18,
        "tiers": [(4, SeatCategory.CLASSIC), (4, SeatCategory.PRIME), (2, SeatCategory.RECLINER)],
    },
    {  # 1: Large screen — 14 rows × 22 = 308 seats
        "name": "Large", "rows": 14, "cols": 22,
        "tiers": [(6, SeatCategory.CLASSIC), (5, SeatCategory.PRIME), (3, SeatCategory.RECLINER)],
    },
    {  # 2: Boutique / GOLD — 6 rows × 12 = 72 seats, all premium recliners
        "name": "Boutique", "rows": 6, "cols": 12,
        "tiers": [(6, SeatCategory.RECLINER)],
    },
    {  # 3: Compact screen — 8 rows × 14 = 112 seats
        "name": "Compact", "rows": 8, "cols": 14,
        "tiers": [(4, SeatCategory.CLASSIC), (3, SeatCategory.PRIME), (1, SeatCategory.RECLINER)],
    },
    {  # 4: IMAX / grand — 16 rows × 24 = 384 seats
        "name": "IMAX", "rows": 16, "cols": 24,
        "tiers": [(7, SeatCategory.CLASSIC), (6, SeatCategory.PRIME), (3, SeatCategory.RECLINER)],
    },
    {  # 5: Mid-size — 12 rows × 20 = 240 seats
        "name": "Mid", "rows": 12, "cols": 20,
        "tiers": [(5, SeatCategory.CLASSIC), (5, SeatCategory.PRIME), (2, SeatCategory.RECLINER)],
    },
]


def layout_for_screen(venue_name: str, audi_number: int) -> dict:
    """
    Pick a layout DETERMINISTICALLY from the theatre identity so that:
      • a given (venue, audi) ALWAYS gets the same room shape — even across
        reseeds and regardless of which movie plays there, and
      • different theatres/audis get different shapes.

    We use a stable character-sum of the venue name + audi number as the index.
    (We deliberately avoid Python's built-in hash(), which is randomised per
    process via PYTHONHASHSEED and would give a different layout every run.)
    """
    key = sum(ord(c) for c in venue_name) + audi_number
    return LAYOUTS[key % len(LAYOUTS)]


def make_seats_for_screen(db, screen, layout):
    """
    Build a physical seat grid from a layout template. Front rows = CLASSIC
    (cheap), middle = PRIME, back = RECLINER (premium) — the usual cinema tiering.
    """
    # Expand the tier spec into a per-row category list, e.g. [CLASSIC, CLASSIC,
    # PRIME, PRIME, RECLINER] for a 5-row room.
    row_categories = []
    for count, category in layout["tiers"]:
        row_categories.extend([category] * count)

    for r_index in range(layout["rows"]):
        row_label = chr(ord("A") + r_index)        # A, B, C, ...
        category = row_categories[r_index]
        for num in range(1, layout["cols"] + 1):
            db.add(models.Seat(
                screen=screen, row_label=row_label, seat_number=num, category=category,
            ))


def price_for(show, category):
    """Pick the right per-category price stored on the show."""
    return {
        SeatCategory.CLASSIC: show.price_classic,
        SeatCategory.PRIME: show.price_prime,
        SeatCategory.RECLINER: show.price_recliner,
    }[category]


def materialise_show_seats(db, show):
    """
    For ONE show, create an inventory row (ShowSeat) for every physical seat in
    its screen, all AVAILABLE. The frozen `price` comes from the show's tier.
    This is the bridge from 'a chair exists' to 'a chair is for sale tonight'.
    """
    for seat in show.screen.seats:
        db.add(models.ShowSeat(
            show=show,
            seat=seat,
            status=ShowSeatStatus.AVAILABLE,
            price=price_for(show, seat.category),
        ))


def run():
    reset_schema()
    db = SessionLocal()
    try:
        # (Cities are created further below — each gets its own venues/shows.)

        # --- Movies (exact data extracted from the BookMyShow TOON dump) ---
        #
        # Posters: we use the REAL BMS CDN image paths from the TOON, but with a
        # CLEAN transform ("tr:w-400,h-600,bg-CCCCCC") so the poster has no baked-in
        # text. We then draw the rating/likes ourselves in MovieCard — separating
        # data from presentation, which is cleaner than BMS's text-on-image trick.
        #
        # Rating convention (decoded from the base64 in the original URLs):
        #   rating > 0  -> show "★ 9.4/10 · 740 Votes"   (votes = the number string)
        #   rating == 0 -> this title shows LIKES instead -> show "👍 76.8K Likes"
        POSTER = "https://assets-in.bmscdn.com/discovery-catalog/events/tr:w-400,h-600,bg-CCCCCC"
        movies = [
            models.Movie(title="Cocktail 2", language="Hindi",
                         genre="Comedy/Drama/Romantic",
                         certificate="UA", duration_mins=145, rating=0.0, votes="76.8K",
                         poster_url=f"{POSTER}/et00491386-gamhtmercb-portrait.jpg",
                         is_promoted=True, release_date=datetime(2026, 6, 12)),
            models.Movie(title="Maa Inti Bangaaram", language="Telugu",
                         genre="Action/Comedy/Family/Thriller",
                         certificate="UA", duration_mins=152, rating=9.4, votes="740",
                         poster_url=f"{POSTER}/et00489559-vuacrglalf-portrait.jpg",
                         release_date=datetime(2026, 6, 13)),
            models.Movie(title="Toy Story 5", language="English",
                         genre="Adventure/Animation/Comedy/Family",
                         certificate="U", duration_mins=110, rating=0.0, votes="36.2K",
                         poster_url=f"{POSTER}/et00482787-fvfmbdamzj-portrait.jpg",
                         release_date=datetime(2026, 6, 19)),
            models.Movie(title="Obsession", language="English",
                         genre="Horror/Thriller",
                         certificate="A", duration_mins=128, rating=8.6, votes="82.2K",
                         poster_url=f"{POSTER}/et00480914-tybyavqknb-portrait.jpg",
                         release_date=datetime(2026, 6, 6)),
            models.Movie(title="Nooru Sami", language="Tamil",
                         genre="Drama/Family/Social",
                         certificate="UA", duration_mins=139, rating=9.0, votes="40",
                         poster_url=f"{POSTER}/et00494436-umrkcnhfbg-portrait.jpg",
                         release_date=datetime(2026, 6, 14)),
        ]
        db.add_all(movies)

        # --- Cities, each with its OWN cinemas (3 fully "working" cities) ---
        # A Movie is global; it only becomes "showing in <city>" because its Show
        # runs on a Screen in a Venue that belongs to that City. So to make a city
        # bookable we just give it venues + shows. name -> [(venue, address, brand)].
        CITY_VENUES = {
            "Bengaluru": [
                ("PVR: Orion Mall, Dr Rajkumar Road", "Brigade Gateway, Malleshwaram", "pvr"),
                ("INOX: Megaplex Mall of Asia Bangalore", "Mall of Asia, Byatarayanapura", "inox"),
                ("Cinepolis: Nexus Shantiniketan, Bengaluru", "Nexus Shantiniketan, Whitefield", "cinepolis_1"),
                ("PVR: Vega City, Bannerghatta Road", "Vega City Mall, Bannerghatta Road", "pvr"),
                ("Cinepolis: Lulu Mall, Bengaluru", "Lulu Mall, Rajajinagar", "cinepolis_1"),
                ("AMB Cinemas Kapali: Bengaluru", "Kapali, Bengaluru", "amb"),
            ],
            "Hyderabad": [
                ("PVR: Nexus Mall, Kukatpally", "Nexus Mall, Kukatpally", "pvr"),
                ("AMB Cinemas: Gachibowli", "Gachibowli, Hyderabad", "amb"),
                ("INOX: GVK One, Banjara Hills", "GVK One Mall, Banjara Hills", "inox"),
                ("PVR: Inorbit, Madhapur", "Inorbit Mall, Madhapur", "pvr"),
                ("Cinepolis: Sudha Multiplex, Dilsukhnagar", "Dilsukhnagar, Hyderabad", "cinepolis_1"),
                ("Asian: Mukunda Cinemas, Attapur", "Attapur, Hyderabad", "default"),
            ],
            "Mumbai": [
                ("PVR: Phoenix Palladium, Lower Parel", "Phoenix Palladium, Lower Parel", "pvr"),
                ("INOX: R-City, Ghatkopar", "R-City Mall, Ghatkopar", "inox"),
                ("PVR: ICON, Infiniti Mall Andheri", "Infiniti Mall, Andheri", "pvr"),
                ("Cinepolis: Viviana Mall, Thane", "Viviana Mall, Thane", "cinepolis_1"),
                ("INOX: Metro, Marine Lines", "Metro INOX, Marine Lines", "inox"),
                ("PVR: Citimall, Andheri West", "Citi Mall, Andheri West", "pvr"),
            ],
        }

        # Build every city's venues + screens (+ physical seats). Keep each city's
        # screen list so we can spread that city's shows across its OWN cinemas.
        screens_by_city = {}
        for city_name, vlist in CITY_VENUES.items():
            city = models.City(name=city_name)
            db.add(city)
            city_screens = []
            for (n, a, b) in vlist:
                v = models.Venue(name=n, address=a, brand=b, city=city)
                db.add(v)
                for audi in (1, 2):
                    layout = layout_for_screen(v.name, audi)
                    sc = models.Screen(name=f"Audi {audi}", venue=v)
                    db.add(sc)
                    make_seats_for_screen(db, sc, layout)
                    city_screens.append(sc)
            screens_by_city[city_name] = city_screens

        # Flush so seats/screens get IDs before we build shows on top of them.
        db.flush()

        # --- Shows: per city, each movie plays 3 times/day across 3 days ---
        # Spreading across dates makes the date-selector meaningful. Fixed dates
        # keep the demo deterministic (no "today" drift).
        DATES = [datetime(2026, 6, 19), datetime(2026, 6, 20), datetime(2026, 6, 21)]
        TIMES = [(10, 0), (14, 0), (18, 30)]   # morning, afternoon, evening
        # Real BMS screening formats — cycled so pills show variety (LASER/ATMOS…).
        FORMATS = ["2D", "LASER", "ATMOS", "GOLD", "INSIGNIA", "DOLBY 7.1",
                   "LUXE", "4K LASER DOLBY 7.1"]
        # Premium formats are typically non-cancellable on BMS.
        PREMIUM_KEYWORDS = ("LASER", "DOLBY", "BARCO", "4K")
        LANG_ABBR = {"Hindi": "HIN", "Telugu": "TEL", "Tamil": "TAM",
                     "English": "ENG", "Kannada": "KAN"}

        shows = []
        fmt_i = 0
        for city_name, city_screens in screens_by_city.items():
            for i, movie in enumerate(movies):
                for d_idx, day in enumerate(DATES):
                    for j, (hh, mm) in enumerate(TIMES):
                        t = day.replace(hour=hh, minute=mm)
                        # Spread within THIS city's screens (so each city has its
                        # own showings of each movie across its own cinemas).
                        screen = city_screens[(i + d_idx + j) % len(city_screens)]
                        fmt = FORMATS[fmt_i % len(FORMATS)]
                        cancellable = not any(k in fmt for k in PREMIUM_KEYWORDS)
                        surge = 1.0 if hh < 17 else 1.3
                        show = models.Show(
                            movie=movie, screen=screen, start_time=t,
                            price_classic=round(150 * surge),
                            price_prime=round(250 * surge),
                            price_recliner=round(450 * surge),
                            audio_format=fmt,
                            subtitle_lang=LANG_ABBR.get(movie.language, "ENG"),
                            is_cancellable=cancellable,
                        )
                        fmt_i += 1
                        shows.append(show)
                        db.add(show)

        db.flush()

        # --- Materialise per-show seat inventory ---
        for show in shows:
            materialise_show_seats(db, show)
        db.flush()

        # --- Pre-sell some seats so availability VARIES on screen ---
        # This is purely demo dressing: it lets you SEE green (available),
        # amber (fast filling) and grey (sold out) pills without booking by hand.
        # We mark seats BOOKED directly (no Booking row) — that's fine, the status
        # field is what availability reads; a Booking is only needed for real sales.
        for idx, show in enumerate(shows):
            ss_list = show.show_seats
            n = len(ss_list)
            if idx % 7 == 0:
                frac = 1.0     # sold out
            elif idx % 3 == 0:
                frac = 0.85    # fast filling (>80% gone)
            elif idx % 2 == 0:
                frac = 0.45
            else:
                frac = 0.10
            for k in range(int(n * frac)):
                ss_list[k].status = ShowSeatStatus.BOOKED

        db.commit()

        # Quick summary so you SEE what was created.
        counts = {
            "cities": db.query(models.City).count(),
            "movies": db.query(models.Movie).count(),
            "venues": db.query(models.Venue).count(),
            "screens": db.query(models.Screen).count(),
            "seats": db.query(models.Seat).count(),
            "shows": db.query(models.Show).count(),
            "show_seats": db.query(models.ShowSeat).count(),
        }
        print("Seed complete:")
        for k, v in counts.items():
            print(f"  {k:12} {v}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
