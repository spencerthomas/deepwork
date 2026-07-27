import { type ApprovalCapabilityFilter, DECISION_VERB_ORDER } from "./approvals-model";

const FILTER_PARAM = "capability";

const KNOWN_FILTERS = new Set<string>(["all", ...DECISION_VERB_ORDER]);

interface ReadonlyParams {
  get(name: string): string | null;
}

/**
 * Derive the approvals capability filter from URL search params, ignoring
 * anything unrecognised so a hand-edited or stale link fails closed to the
 * default ("all"), matching how the inbox and activity feed restore their views.
 */
export function readApprovalFilter(params: ReadonlyParams): ApprovalCapabilityFilter {
  const raw = params.get(FILTER_PARAM);
  return raw !== null && KNOWN_FILTERS.has(raw) ? (raw as ApprovalCapabilityFilter) : "all";
}

/**
 * Serialize a filter to a query string, emitting the param only when it differs
 * from the default so a pristine queue stays at a clean URL.
 */
export function approvalFilterToQuery(filter: ApprovalCapabilityFilter): string {
  const params = new URLSearchParams();
  if (filter !== "all") {
    params.set(FILTER_PARAM, filter);
  }
  return params.toString();
}
