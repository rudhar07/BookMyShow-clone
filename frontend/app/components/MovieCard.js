/**
 * MovieCard.js — one poster tile in the "Recommended Movies" grid.
 * Clicking it navigates to that movie's booking page (/movies/[id]).
 *
 * Shows the PROMOTED tag and a rating bar, mirroring the BMS card.
 * We use a plain <img> with an onError fallback because the seeded poster URLs
 * are illustrative and may 404 — graceful degradation beats a broken image.
 */
import Link from "next/link";

export default function MovieCard({ movie }) {
  return (
    <Link href={`/movies/${movie.id}`} className="card">
      <div className="card-poster">
        {movie.is_promoted && <div className="promoted">PROMOTED</div>}
        <img
          src={movie.poster_url}
          alt={movie.title}
          onError={(e) => {
            // Fallback to a coloured block with no broken-image icon.
            e.currentTarget.style.display = "none";
          }}
        />
        {/* BMS shows EITHER a rating (with /10) OR a likes count, never both.
            We mirror that: rating>0 → star line; rating==0 → likes line. */}
        {movie.rating > 0 ? (
          <div className="card-rating">
            ★ {movie.rating.toFixed(1)}/10 · {movie.votes} Votes
          </div>
        ) : (
          <div className="card-rating">👍 {movie.votes} Likes</div>
        )}
      </div>
      <div className="card-title">{movie.title}</div>
      {/* Real BMS home cards show only the genre line under the title. */}
      <div className="card-sub">{movie.genre}</div>
    </Link>
  );
}
