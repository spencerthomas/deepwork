"use client";

/**
 * Last-resort boundary for an error thrown by the root layout itself. It
 * replaces the whole document, so it renders its own <html>/<body> and styles
 * inline — the app stylesheet may not have loaded when the layout failed.
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body
        style={{
          minHeight: "100vh",
          margin: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "1rem",
          padding: "1.5rem",
          textAlign: "center",
          fontFamily: "system-ui, sans-serif",
          color: "#161f34",
          background: "#ffffff",
        }}
      >
        <h1 style={{ fontSize: "1.25rem", fontWeight: 600, margin: 0 }}>Something went wrong</h1>
        <p style={{ maxWidth: "28rem", color: "#5b6472", margin: 0 }}>
          The application failed to load. Reloading usually clears it.
        </p>
        {error.digest && (
          <p style={{ fontFamily: "monospace", fontSize: "0.6875rem", color: "#5b6472" }}>
            ref: {error.digest}
          </p>
        )}
        <button
          type="button"
          onClick={reset}
          style={{
            cursor: "pointer",
            borderRadius: "0.75rem",
            border: "none",
            background: "#006ddd",
            color: "#ffffff",
            padding: "0.5rem 0.85rem",
            fontSize: "0.8125rem",
            fontWeight: 500,
          }}
        >
          Try again
        </button>
      </body>
    </html>
  );
}
