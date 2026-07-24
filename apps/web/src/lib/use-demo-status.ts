"use client";

import { useCallback, useEffect, useState } from "react";

import { type DemoStatus, fetchDemoStatus, fixtureDemoStatus } from "./demo-status";
import { useTasksStore } from "./tasks-store";

export interface DemoStatusResult {
  /** Undefined while loading or after a failed/malformed fetch (fail closed). */
  status: DemoStatus | undefined;
  loading: boolean;
  /**
   * Re-fetch the status. In api mode this retries the network request (so a
   * status that was momentarily unreachable can recover without a full page
   * reload); in fixture mode the status is synthesized locally, so this is a
   * no-op.
   */
  refetch: () => void;
}

/**
 * Demo status for the current client. In fixture mode nothing is fetched; the
 * equivalent status is synthesized locally and labeled fixture. In api mode a
 * fetch failure resolves to `undefined` so callers render an unknown state.
 */
export function useDemoStatus(): DemoStatusResult {
  const { mode, apiBaseUrl } = useTasksStore();
  const fixture = mode === "fixture";
  const [status, setStatus] = useState<DemoStatus | undefined>(() =>
    fixture ? fixtureDemoStatus() : undefined,
  );
  const [loading, setLoading] = useState(!fixture);
  // Bumped by refetch() to re-run the fetch effect.
  const [reloadNonce, setReloadNonce] = useState(0);
  const refetch = useCallback(() => setReloadNonce((nonce) => nonce + 1), []);

  useEffect(() => {
    if (fixture) {
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    void fetchDemoStatus(apiBaseUrl, controller.signal).then((result) => {
      if (!controller.signal.aborted) {
        setStatus(result);
        setLoading(false);
      }
    });
    return () => controller.abort();
  }, [fixture, apiBaseUrl, reloadNonce]);

  return { status, loading, refetch };
}
