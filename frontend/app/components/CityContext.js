/**
 * CityContext.js — the selected city, shared across the whole app.
 * ================================================================
 * WHY a React Context? The chosen city is needed in many places (the header
 * button, the home movie list, the showtimes page) that aren't parent/child of
 * each other. Threading it through props ("prop drilling") would be painful, so
 * we put it in a Context — a global value any component can read with a hook.
 *
 * WHY persist to localStorage? So the choice survives a page refresh / new tab,
 * exactly like the real BookMyShow remembers your city.
 *
 * SSR note: localStorage only exists in the browser, so we read it inside
 * useEffect (after mount), starting from a safe default to avoid a server/client
 * mismatch during hydration.
 */
"use client";

import { createContext, useContext, useEffect, useState } from "react";

const CityContext = createContext(null);
const STORAGE_KEY = "bms_city";
const DEFAULT_CITY = "Bengaluru";

export function CityProvider({ children }) {
  const [city, setCityState] = useState(DEFAULT_CITY);

  // After mount, load the saved city (if any).
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) setCityState(saved);
  }, []);

  // Setter that also persists.
  const setCity = (next) => {
    setCityState(next);
    localStorage.setItem(STORAGE_KEY, next);
  };

  return (
    <CityContext.Provider value={{ city, setCity }}>
      {children}
    </CityContext.Provider>
  );
}

// Tiny hook so components do `const { city, setCity } = useCity()`.
export function useCity() {
  return useContext(CityContext);
}
