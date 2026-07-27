"use client";

import { useCallback, useEffect, useState } from "react";

import { scheduleClient, type ScheduleSummary } from "./schedule-client";

export interface SchedulesResult {
  /** False while loading, on a failed fetch, and whenever no real task source is configured. */
  available: boolean;
  schedules: ScheduleSummary[];
  loading: boolean;
  error?: string;
  refetch: () => void;
}

/**
 * The schedule registry for the current client. `available` is false while
 * loading, on a failed fetch, and whenever no real task source is
 * configured — never a fabricated non-empty list.
 */
export function useSchedules(): SchedulesResult {
  const [schedules, setSchedules] = useState<ScheduleSummary[]>([]);
  const [available, setAvailable] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();
  const [reloadNonce, setReloadNonce] = useState(0);
  const refetch = useCallback(() => setReloadNonce((nonce) => nonce + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(undefined);
    void scheduleClient
      .listSchedules(controller.signal)
      .then((result) => {
        if (controller.signal.aborted) {
          return;
        }
        setAvailable(result.available);
        setSchedules(result.items);
      })
      .catch((caught: unknown) => {
        if (!controller.signal.aborted) {
          setAvailable(false);
          setError(caught instanceof Error ? caught.message : "Could not load schedules.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, [reloadNonce]);

  return { available, schedules, loading, error, refetch };
}
