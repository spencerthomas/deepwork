"use client";

import { useEffect } from "react";

/**
 * Route-segment error boundary. An unexpected render error below the root
 * layout lands here instead of a blank screen; the user can retry the segment
 * or return to their tasks.
 */
export default function RouteError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // No external reporting in this client — surface it for local debugging.
    console.error(error);
  }, [error]);

  return (
    <div
      role="alert"
      className="mx-auto flex min-h-[60vh] max-w-md flex-col items-center justify-center px-4 text-center"
    >
      <h1 className="text-xl font-semibold tracking-tight">Something went wrong</h1>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
        This screen hit an unexpected error. You can retry it, or head back to your tasks.
      </p>
      {error.digest && (
        <p className="mt-2 font-mono text-[11px] text-muted-foreground">ref: {error.digest}</p>
      )}
      <div className="mt-5 flex items-center gap-2">
        <button
          type="button"
          onClick={reset}
          className="rounded-xl bg-brand px-3 py-1.5 text-[13px] font-medium text-brand-foreground transition-colors hover:bg-brand/90"
        >
          Try again
        </button>
        <a
          href="/tasks"
          className="rounded-xl border border-border px-3 py-1.5 text-[13px] font-medium transition-colors hover:bg-accent"
        >
          Back to tasks
        </a>
      </div>
    </div>
  );
}
