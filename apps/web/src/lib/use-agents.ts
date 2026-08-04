"use client";

import { useCallback, useEffect, useState } from "react";

import { agentClient, type AgentSummary } from "./agent-client";

export interface AgentsResult {
  /** False until the first load resolves (mirrors the API's "available" flag while loading). */
  available: boolean;
  agents: AgentSummary[];
  loading: boolean;
  error?: string;
  refetch: () => void;
}

/**
 * The agent registry for the current client. `available` is false while
 * loading, on a failed fetch, and whenever no real task source is
 * configured — never a fabricated non-empty list.
 */
export function useAgents(enabled = true): AgentsResult {
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [available, setAvailable] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();
  const [reloadNonce, setReloadNonce] = useState(0);
  const refetch = useCallback(() => setReloadNonce((nonce) => nonce + 1), []);

  useEffect(() => {
    if (!enabled) {
      setAgents([]);
      setAvailable(false);
      setLoading(false);
      setError(undefined);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(undefined);
    void agentClient
      .listAgents(controller.signal)
      .then((result) => {
        if (controller.signal.aborted) {
          return;
        }
        setAvailable(result.available);
        setAgents(result.items);
      })
      .catch((caught: unknown) => {
        if (!controller.signal.aborted) {
          setAvailable(false);
          setAgents([]);
          setError(caught instanceof Error ? caught.message : "Could not load agents.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, [enabled, reloadNonce]);

  return { available, agents, loading, error, refetch };
}
