/**
 * AuthContext.js — the signed-in user, shared across the app.
 * ===========================================================
 * Same idea as CityContext: a global value (the current user, or null) any
 * component can read via useAuth(), persisted to localStorage so the "session"
 * survives refresh. There's no real token here — it's a mock session holding the
 * user row returned by /api/auth/login.
 *
 * SSR-safe: start at null, read localStorage only after mount (in useEffect).
 */
"use client";

import { createContext, useContext, useEffect, useState } from "react";

const AuthContext = createContext(null);
const STORAGE_KEY = "bms_user";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try { setUser(JSON.parse(saved)); } catch { /* ignore bad json */ }
    }
  }, []);

  const login = (u) => {
    setUser(u);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(u));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem(STORAGE_KEY);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
