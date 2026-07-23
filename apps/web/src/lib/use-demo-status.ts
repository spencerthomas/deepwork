"use client";

import { useEffect, useState } from "react";

import { type DemoStatus, fetchDemoStatus, fixtureDemoStatus } from "./demo-status";
import { useTasksStore } from "./tasks-store";

export interface DemoStatusResult {
  /** Undefined while loading or after a failed/malformed fetch (fail closed). */
  status: DemoStatus | undefined;
  loading: boolean;
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
  }, [fixture, apiBaseUrl]);

  return { status, loading };
}
