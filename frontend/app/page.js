/**
 * page.js (/) — the HOME page.
 * ============================
 * "use client" because it fetches data in the browser and holds state. (Next.js
 * components are server-rendered by default; this directive opts into the client
 * so we can use hooks like useState/useEffect.)
 *
 * Flow: on mount → GET /api/movies → render the carousel + the movie grid.
 */
"use client";

import { useEffect, useState } from "react";
import { getMovies } from "./lib/api";
import MovieCard from "./components/MovieCard";
import { useCity } from "./components/CityContext";

// The promotional banners from the screenshot's carousel (BMS CDN images).
const BANNERS = [
  "https://assets-in-gm.bmscdn.com/promotions/cms/creatives/1779713109197_jsblrweb.jpg",
  "https://assets-in-gm.bmscdn.com/promotions/cms/creatives/1781266722008_dndweb.jpeg",
  "https://assets-in-gm.bmscdn.com/promotions/cms/creatives/1781329300147_blrweb.jpg",
];

export default function Home() {
  const { city } = useCity();
  const [movies, setMovies] = useState([]);
  const [error, setError] = useState(null);
  const [banner, setBanner] = useState(0);

  // Re-fetch whenever the city changes — movies are scoped to the chosen city.
  useEffect(() => {
    setError(null);
    getMovies(city).then(setMovies).catch((e) => setError(e.message));
  }, [city]);

  // Auto-rotate the banner every 4s, like the real carousel.
  useEffect(() => {
    const t = setInterval(() => setBanner((b) => (b + 1) % BANNERS.length), 4000);
    return () => clearInterval(t);
  }, []);

  // Carousel controls. We wrap with modulo so prev from slide 0 → last slide.
  const prev = () => setBanner((b) => (b - 1 + BANNERS.length) % BANNERS.length);
  const next = () => setBanner((b) => (b + 1) % BANNERS.length);

  return (
    <div>
      <div className="container">
        <div className="banner-wrap">
          <div className="banner">
            <img src={BANNERS[banner]} alt="promotion" />
          </div>
          {/* Left/right arrows — TOON s47 / s49 */}
          <button className="banner-arrow left" onClick={prev} aria-label="Previous">‹</button>
          <button className="banner-arrow right" onClick={next} aria-label="Next">›</button>
          {/* Dot indicators — TOON s53 / s54 */}
          <div className="banner-dots">
            {BANNERS.map((_, i) => (
              <span
                key={i}
                className={`dot ${i === banner ? "active" : ""}`}
                onClick={() => setBanner(i)}
              />
            ))}
          </div>
        </div>
      </div>

      <section className="container section">
        <div className="section-head">
          <h2>Recommended Movies</h2>
          <span className="see-all">See All ›</span>
        </div>

        {error && <div className="msg-error">Couldn’t load movies: {error}</div>}

        <div className="movie-grid">
          {movies.map((m) => (
            <MovieCard key={m.id} movie={m} />
          ))}
        </div>
      </section>

      {/* Stream promo strip — TOON s83 (a single wide banner linking to Stream) */}
      <div className="container">
        <div className="stream-strip">
          <img
            src="https://assets-in.bmscdn.com/discovery-catalog/collections/tr:w-1440,h-120/stream-leadin-web-collection-202210241242.png"
            alt="Stream"
          />
        </div>
      </div>
    </div>
  );
}
