"use client";

import { type FormEvent, useState } from "react";

export default function LoginPage() {
  const [accessKey, setAccessKey] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ accessKey }),
      });
      if (response.ok) {
        // Full navigation so middleware re-evaluates with the new session cookie.
        window.location.assign("/tasks");
        return;
      }
      setError(response.status === 401 ? "That access key was not accepted." : "Sign in failed.");
    } catch {
      setError("Could not reach Deep Work. Please try again.");
    }
    setBusy(false);
  }

  return (
    <main
      style={{
        minHeight: "100dvh",
        display: "grid",
        placeItems: "center",
        padding: "1.5rem",
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          width: "100%",
          maxWidth: "22rem",
          display: "flex",
          flexDirection: "column",
          gap: "1rem",
          padding: "1.75rem",
          border: "1px solid color-mix(in oklab, currentColor 15%, transparent)",
          borderRadius: "0.75rem",
        }}
      >
        <div>
          <h1 style={{ fontSize: "1.25rem", fontWeight: 600, margin: 0 }}>Deep Work</h1>
          <p style={{ opacity: 0.7, margin: "0.35rem 0 0", fontSize: "0.9rem" }}>
            Enter your access key to continue.
          </p>
        </div>
        <label style={{ display: "flex", flexDirection: "column", gap: "0.4rem", fontSize: "0.85rem" }}>
          Access key
          <input
            type="password"
            autoComplete="current-password"
            value={accessKey}
            onChange={(event) => setAccessKey(event.target.value)}
            required
            autoFocus
            style={{
              padding: "0.6rem 0.7rem",
              borderRadius: "0.5rem",
              border: "1px solid color-mix(in oklab, currentColor 25%, transparent)",
              background: "transparent",
              color: "inherit",
              font: "inherit",
            }}
          />
        </label>
        {error ? (
          <p role="alert" style={{ color: "#dc2626", fontSize: "0.85rem", margin: 0 }}>
            {error}
          </p>
        ) : null}
        <button
          type="submit"
          disabled={busy || accessKey.trim() === ""}
          style={{
            padding: "0.6rem 0.7rem",
            borderRadius: "0.5rem",
            border: "none",
            background: "currentColor",
            cursor: busy ? "default" : "pointer",
            font: "inherit",
            opacity: busy || accessKey.trim() === "" ? 0.6 : 1,
          }}
        >
          <span style={{ color: "var(--background, #fff)", mixBlendMode: "difference" }}>
            {busy ? "Signing in…" : "Sign in"}
          </span>
        </button>
      </form>
    </main>
  );
}
