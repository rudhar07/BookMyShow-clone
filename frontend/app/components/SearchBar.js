/**
 * SearchBar.js — the header search field + the full search modal.
 * ===============================================================
 * Matches BookMyShow's search overlay: a big search input, category chips, and a
 * results list ("Popular/Trending Results" when empty).
 *
 * Behaviour:
 *   • Clicking the header bar opens the modal.
 *   • Typing hits GET /api/search?q=&city= (debounced) → movies (by title) +
 *     cinemas in the SELECTED city (by name).
 *   • Empty query shows trending movies.
 *   • Clicking a movie → its showtimes page. (No standalone venue page, so a
 *     cinema result just closes the modal.)
 *
 * Debounce: we wait 250 ms after the last keystroke before calling the API, so
 * typing "obsession" fires one request, not nine.
 */
"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useCity } from "./CityContext";
import { search as searchApi } from "../lib/api";

const CHIPS = ["Movies", "Stream", "Events", "Plays", "Sports", "Activities"];

export default function SearchBar() {
  const { city } = useCity();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [results, setResults] = useState({ movies: [], venues: [] });
  const timer = useRef(null);

  // Debounced search whenever the query (or city) changes while open.
  useEffect(() => {
    if (!open) return;
    clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      searchApi(q, city)
        .then(setResults)
        .catch(() => setResults({ movies: [], venues: [] }));
    }, 250);
    return () => clearTimeout(timer.current);
  }, [q, city, open]);

  const close = () => {
    setOpen(false);
    setQ("");
    setResults({ movies: [], venues: [] });
  };

  const openMovie = (id) => {
    close();
    router.push(`/movies/${id}`);
  };

  const isTrending = q.trim() === "";

  return (
    <>
      {/* The bar shown in the header (click to open the modal) */}
      <div className="search" onClick={() => setOpen(true)}>
        <span>🔍</span>
        Search for Movies, Events, Plays, Sports and Activities
      </div>

      {open && (
        <div className="search-overlay" onClick={close}>
          <div className="search-panel" onClick={(e) => e.stopPropagation()}>
            <div className="search-top">
              <div className="search-input">
                <span>🔍</span>
                <input
                  autoFocus
                  placeholder="Search for movies, events, plays, sports..."
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                />
              </div>
              <span className="search-close" onClick={close}>✕</span>
            </div>

            <div className="search-chips">
              {CHIPS.map((c, i) => (
                <span key={c} className={`search-chip ${i === 0 ? "active" : ""}`}>{c}</span>
              ))}
            </div>
          </div>

          {/* Results live below the white panel */}
          <div className="search-results" onClick={(e) => e.stopPropagation()}>
            <p className="search-results-label">
              {isTrending ? "Popular/Trending Results" : `Results for "${q}" in ${city}`}
            </p>

            {results.movies.map((m) => (
              <div key={`m${m.id}`} className="search-row" onClick={() => openMovie(m.id)}>
                <div>
                  <div className="search-row-title">{m.title}</div>
                  <div className="search-row-sub">{m.language} · {m.genre}</div>
                </div>
                <span className="search-row-icon">🎬</span>
              </div>
            ))}

            {results.venues.map((v) => (
              <div key={`v${v.id}`} className="search-row" onClick={close}>
                <div>
                  <div className="search-row-title">{v.name}</div>
                  <div className="search-row-sub">{v.address} · Cinema in {city}</div>
                </div>
                <span className="search-row-icon">📍</span>
              </div>
            ))}

            {!isTrending && results.movies.length === 0 && results.venues.length === 0 && (
              <div className="search-empty">No movies or cinemas match “{q}” in {city}.</div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
