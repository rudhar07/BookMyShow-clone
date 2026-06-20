/**
 * SignIn.js — the header "Sign in" button + sign-in modal + signed-in chip.
 * =========================================================================
 *   • Signed OUT → a red "Sign in" button that opens a modal (name + email +
 *     optional phone). Submitting calls POST /api/auth/login (find-or-create)
 *     and stores the returned user in AuthContext (persisted to localStorage).
 *   • Signed IN  → "Hi, <first name> ▾" with a small dropdown to sign out.
 *
 * It reuses the same .overlay/.modal styles as the booking modal for consistency.
 */
"use client";

import { useState } from "react";
import { useAuth } from "./AuthContext";
import { login as loginApi } from "../lib/api";

export default function SignIn() {
  const { user, login, logout } = useAuth();
  const [open, setOpen] = useState(false);   // sign-in modal
  const [menu, setMenu] = useState(false);    // signed-in dropdown
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const submit = async () => {
    setError(null);
    setBusy(true);
    try {
      const u = await loginApi({ name, email, phone: phone || null });
      login(u);
      setOpen(false);
      setName(""); setEmail(""); setPhone("");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  // ---- Signed-in chip ----
  if (user) {
    const first = user.name?.split(" ")[0] || "Account";
    return (
      <div className="auth-chip-wrap">
        <span className="auth-chip" onClick={() => setMenu((m) => !m)}>
          Hi, {first} ▾
        </span>
        {menu && (
          <div className="auth-menu" onMouseLeave={() => setMenu(false)}>
            <div className="auth-menu-email">{user.email}</div>
            <div className="auth-menu-item" onClick={() => { logout(); setMenu(false); }}>
              Sign out
            </div>
          </div>
        )}
      </div>
    );
  }

  // ---- Signed-out button + modal ----
  return (
    <>
      <button className="signin" onClick={() => setOpen(true)}>Sign in</button>

      {open && (
        <div className="overlay" onClick={() => setOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Sign in to BookMyShow</h3>
            <div className="card-sub">Enter your details to continue.</div>
            <label>Name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" />
            <label>Email</label>
            <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
            <label>Phone (optional)</label>
            <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="9876543210" />
            {error && <div className="msg-error">{error}</div>}
            <div className="modal-actions">
              <button className="btn-ghost" onClick={() => setOpen(false)} disabled={busy}>Cancel</button>
              <button
                className="btn-primary"
                style={{ flex: 1 }}
                onClick={submit}
                disabled={busy || !name || !email}
              >
                {busy ? "Signing in…" : "Continue"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
