export const AGENT_FILTERS = ["all", "active"] as const;

export type AgentFilter = (typeof AGENT_FILTERS)[number];

const FILTER_PARAM = "show";

const KNOWN_FILTERS = new Set<string>(AGENT_FILTERS);

interface ReadonlyParams {
  get(name: string): string | null;
}

/**
 * Derive the fleet filter from URL search params, ignoring anything
 * unrecognised so a hand-edited or stale link fails closed to the default
 * ("all"), matching the URL-restore contract the inbox and queues use.
 */
export function readAgentFilter(params: ReadonlyParams): AgentFilter {
  const raw = params.get(FILTER_PARAM);
  return raw !== null && KNOWN_FILTERS.has(raw) ? (raw as AgentFilter) : "all";
}

/**
 * Serialize a filter to a query string, emitting the param only when it differs
 * from the default so a pristine fleet stays at a clean URL.
 */
export function agentFilterToQuery(filter: AgentFilter): string {
  const params = new URLSearchParams();
  if (filter !== "all") {
    params.set(FILTER_PARAM, filter);
  }
  return params.toString();
}
