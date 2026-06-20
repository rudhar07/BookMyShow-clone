/**
 * /movies/[id] — cinema & showtime listing (matched to the showtimes-page TOON).
 * ============================================================================
 * Faithful to BookMyShow's "buy tickets" page:
 *   • WHITE header: "Title - (Language)" + outlined meta pills      [TOON s34–s39]
 *   • horizontal DATE SELECTOR (selected = pink pill)               [TOON s43–s51]
 *   • subtitle note + AVAILABLE / FAST FILLING legend               [TOON s67–s82]
 *   • cinema rows: brand icon, F&B / M-Ticket badges, cancellation  [TOON s90]
 *   • showtime pills: TIME + format (LASER/ATMOS), colour by avail.  [TOON s102/s122/s105]
 *
 * Availability colour comes from the backend's GROUP BY count, so it's real.
 */
"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { getMovie, getMovieShows } from "../../lib/api";
import { useCity } from "../../components/CityContext";

function timeLabel(iso) {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
function dateKey(iso) {
  return iso.slice(0, 10);
}
function dateParts(key) {
  const d = new Date(key + "T00:00:00");
  return {
    weekday: d.toLocaleDateString([], { weekday: "short" }).toUpperCase(),
    day: d.getDate(),
    month: d.toLocaleDateString([], { month: "short" }).toUpperCase(),
  };
}
// 145 -> "2h 25m"  (BMS shows runtime this way, not "145 min")
function runtime(mins) {
  return `${Math.floor(mins / 60)}h ${mins % 60}m`;
}

export default function MoviePage({ params }) {
  const router = useRouter();
  const { city } = useCity();
  const [movie, setMovie] = useState(null);
  const [venues, setVenues] = useState([]);
  const [error, setError] = useState(null);
  const [selectedDate, setSelectedDate] = useState(null);

  useEffect(() => {
    getMovie(params.id).then(setMovie).catch((e) => setError(e.message));
    // Only show cinemas in the chosen city; refetch when city changes.
    getMovieShows(params.id, city).then(setVenues).catch((e) => setError(e.message));
  }, [params.id, city]);

  const dates = useMemo(() => {
    const set = new Set();
    venues.forEach((v) => v.shows.forEach((s) => set.add(dateKey(s.start_time))));
    return [...set].sort();
  }, [venues]);

  useEffect(() => {
    if (!selectedDate && dates.length) setSelectedDate(dates[0]);
  }, [dates, selectedDate]);

  if (error) return <div className="msg-error">{error}</div>;
  if (!movie) return <div className="loading">Loading…</div>;

  const pillClass = (a) =>
    a === "AVAILABLE" ? "pill green" : a === "FAST_FILLING" ? "pill amber" : "pill grey";
  const genres = movie.genre.split("/");

  return (
    <div>
      {/* Breadcrumb */}
      <div className="container crumbs">
        <a href="/">Home</a><span className="sep">›</span>
        <a href="/">Movies in {city}</a><span className="sep">›</span>
        <span>{movie.language} Movies</span><span className="sep">›</span>
        <span>{movie.title}</span>
      </div>

      {/* White showtimes header */}
      <div className="mv-header">
        <div className="container mv-header-inner">
          <div className="mv-title">{movie.title} - ({movie.language})</div>
          <div className="mv-meta">
            <span className="meta-pill">Movie runtime: {runtime(movie.duration_mins)}</span>
            <span className="meta-pill">{movie.certificate}</span>
            {genres.map((g) => (
              <span className="meta-genre" key={g}>{g}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Date selector strip */}
      <div className="datebar">
        <div className="container datebar-inner">
          {dates.map((d) => {
            const p = dateParts(d);
            return (
              <button
                key={d}
                className={`datepill ${d === selectedDate ? "active" : ""}`}
                onClick={() => setSelectedDate(d)}
              >
                <span className="dp-wd">{p.weekday}</span>
                <span className="dp-day">{p.day}</span>
                <span className="dp-mo">{p.month}</span>
              </button>
            );
          })}
        </div>
      </div>

      <section className="container section">
        {/* Subtitle note + legend (only 2 states on the real page) */}
        <div className="leg">
          <span style={{ color: "#999" }}>ⓘ indicates subtitle language, if available</span>
          <span><i className="dot green" /> AVAILABLE</span>
          <span><i className="dot amber" /> FAST FILLING</span>
        </div>

        {venues
          .map((v) => ({
            ...v,
            shows: v.shows.filter((s) => dateKey(s.start_time) === selectedDate),
          }))
          .filter((v) => v.shows.length > 0)
          .map((v) => {
            // Brand icon comes straight from the BMS CDN by brand slug.
            const iconUrl = `https://assets-in.bmscdn.com/moviesmaster/movies-showtimes/v4/cinema-icon/${v.brand}.png`;
            // Row-level cancellation line: only "available" if every shown show allows it.
            const allCancellable = v.shows.every((s) => s.is_cancellable);
            return (
              <div className="venue-card" key={v.venue_id}>
                <div style={{ flex: "0 0 320px" }}>
                  <div className="cine-left">
                    <div className="cine-icon">
                      <img src={iconUrl} alt={v.brand}
                           onError={(e) => (e.currentTarget.style.display = "none")} />
                    </div>
                    <div>
                      <div className="venue-name">{v.venue_name} ⓘ</div>
                      <div className="venue-addr">{v.address}</div>
                      <div className="cine-badges">
                        <span className="cine-badge">🍿 F&amp;B</span>
                        <span className="cine-badge">📱 M-Ticket</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div style={{ flex: 1 }}>
                  <div className="showtimes">
                    {v.shows.map((s) => {
                      const soldOut = s.availability === "SOLD_OUT";
                      return (
                        <button
                          key={s.id}
                          className={pillClass(s.availability)}
                          disabled={soldOut}
                          onClick={() => !soldOut && router.push(`/shows/${s.id}`)}
                          title={`${s.available_seats}/${s.total_seats} seats · ₹${s.price_classic} onwards · ${s.is_cancellable ? "Cancellable" : "Non-cancellable"}`}
                        >
                          <span className="pill-time">
                            {timeLabel(s.start_time)}
                            <sup className="pill-lang">{s.subtitle_lang}</sup>
                          </span>
                          <span className="pill-sub">{soldOut ? "Sold out" : s.audio_format}</span>
                        </button>
                      );
                    })}
                  </div>
                  <div className={`cancellation ${allCancellable ? "" : "no"}`}>
                    {allCancellable ? "✓ Cancellation available" : "✕ Non-cancellable"}
                  </div>
                </div>
              </div>
            );
          })}

        {/* Empty-state prompt at the bottom of the cinema list — TOON s131 */}
        <div className="change-loc">
          <div className="q">Unable to find what you are looking for?</div>
          <button>Change Location</button>
        </div>
      </section>
    </div>
  );
}
