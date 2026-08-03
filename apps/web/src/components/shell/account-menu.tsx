"use client";

import { LogOut, User } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { getSession, logout, type Session } from "@/lib/auth-client";

/**
 * Who's signed in, and a real sign-out. Reads /api/v1/auth/session (the
 * session already required to reach any page past middleware) and posts to
 * /api/v1/auth/logout, which clears the HttpOnly cookie server-side.
 */
export function AccountMenu() {
  const [open, setOpen] = useState(false);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [signingOut, setSigningOut] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    getSession()
      .then((body) => {
        if (!cancelled) setSession(body);
      })
      .catch(() => {
        if (!cancelled) setSession(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!open) return;
    function onDown(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    window.addEventListener("mousedown", onDown);
    return () => window.removeEventListener("mousedown", onDown);
  }, [open]);

  async function signOut() {
    setSigningOut(true);
    try {
      await logout();
    } finally {
      // Full navigation so middleware re-evaluates without the cleared cookie,
      // even if the logout request itself failed to reach the API.
      window.location.assign("/login");
    }
  }

  // No session to show or sign out of (fixture demo, or auth not configured).
  if (!loading && session === null) {
    return null;
  }

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        aria-label="Account menu"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        className="flex size-8 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
      >
        <User aria-hidden className="size-4" />
      </button>
      {open && (
        <div
          role="menu"
          className="absolute right-0 top-full z-40 mt-2 w-64 rounded-2xl border border-border bg-card p-3 shadow-lg"
        >
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Signed in as
          </p>
          <p className="mt-1 truncate text-[13px] font-medium text-crisp">
            {loading ? "Loading…" : (session?.actorId ?? "Unknown")}
          </p>
          <button
            type="button"
            role="menuitem"
            onClick={() => void signOut()}
            disabled={signingOut}
            className="mt-3 flex w-full items-center gap-2 rounded-xl border border-border px-3 py-1.5 text-[13px] font-medium text-status-failed transition-colors hover:bg-status-failed-bg disabled:cursor-not-allowed disabled:opacity-60"
          >
            <LogOut aria-hidden className="size-3.5" />
            {signingOut ? "Signing out…" : "Sign out"}
          </button>
        </div>
      )}
    </div>
  );
}
