/**
 * CitySelector.js — the header city button + the BMS-style city-picker modal.
 * ===========================================================================
 * Matches the city-modal TOON: a search box, "Detect my location", a "Popular
 * Cities" grid of region icons, and "View All Cities".
 *
 * Behaviour:
 *   • Reads/sets the global city via useCity() (Context, persisted to localStorage).
 *   • Fetches /api/cities to know which cities are actually BOOKABLE (seeded).
 *     Those are clickable; the rest render dimmed as "Coming soon" — honest about
 *     what has data.
 *   • Picking a city updates the context and sends the user home, where the movie
 *     list re-fetches for the new city.
 */
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useCity } from "./CityContext";
import { getCities } from "../lib/api";

// Popular cities shown in the grid, with BookMyShow's own region icons.
const ICON = "https://assets-in.bmscdn.com/m6/images/common-modules/regions/";
const POPULAR = [
  { name: "Mumbai", img: "mumbai.png" },
  { name: "Delhi-NCR", img: "ncr.png" },
  { name: "Bengaluru", img: "bang.png" },
  { name: "Hyderabad", img: "hyd.png" },
  { name: "Chandigarh", img: "chd.png" },
  { name: "Ahmedabad", img: "ahd.png" },
  { name: "Pune", img: "pune.png" },
  { name: "Chennai", img: "chen.png" },
  { name: "Kolkata", img: "kolk.png" },
  { name: "Kochi", img: "koch.png" },
];

export default function CitySelector() {
  const { city, setCity } = useCity();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [available, setAvailable] = useState(new Set());

  // Which cities have real data (so we can enable only those).
  useEffect(() => {
    getCities()
      .then((cs) => setAvailable(new Set(cs.map((c) => c.name))))
      .catch(() => {});
  }, []);

  const choose = (name) => {
    if (!available.has(name)) return;   // "coming soon" cities are inert
    setCity(name);
    setOpen(false);
    setQuery("");
    router.push("/");                   // land on the new city's home
  };

  const shown = POPULAR.filter((c) =>
    c.name.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <>
      <span className="city" onClick={() => setOpen(true)}>
        {city} ▾
      </span>

      {open && (
        <div className="city-overlay" onClick={() => setOpen(false)}>
          {/* stopPropagation so clicking inside the box doesn't close it */}
          <div className="city-modal" onClick={(e) => e.stopPropagation()}>
            <div className="city-search">
              <span>🔍</span>
              <input
                autoFocus
                placeholder="Search for your city"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>

            <div className="city-detect">📍 Detect my location</div>

            <p className="city-pop-label">Popular Cities</p>
            <div className="city-grid">
              {shown.map((c) => {
                const enabled = available.has(c.name);
                return (
                  <div
                    key={c.name}
                    className={`city-item ${enabled ? "" : "disabled"} ${c.name === city ? "active" : ""}`}
                    onClick={() => choose(c.name)}
                    title={enabled ? `Browse ${c.name}` : "Coming soon"}
                  >
                    <img src={`${ICON}${c.img}`} alt={c.name}
                         onError={(e) => (e.currentTarget.style.visibility = "hidden")} />
                    <span>{c.name}</span>
                    {!enabled && <small>Coming soon</small>}
                  </div>
                );
              })}
            </div>

            <div className="city-viewall">View All Cities</div>
          </div>
        </div>
      )}
    </>
  );
}
