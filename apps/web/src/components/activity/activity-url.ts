import { ACTIVITY_FILTERS, type ActivityFilter } from "./activity-model";

const FILTER_PARAM = "type";

const KNOWN_FILTERS = new Set<string>(ACTIVITY_FILTERS);

interface ReadonlyParams {
  get(name: string): string | null;
}

/**
 * Derive the activity filter from URL search params, ignoring anything
 * unrecognised so a hand-edited or stale link fails closed to the default
 * ("all"), matching how the inbox restores its view.
 */
export function readActivityFilter(params: ReadonlyParams): ActivityFilter {
  const raw = params.get(FILTER_PARAM);
  return raw !== null && KNOWN_FILTERS.has(raw) ? (raw as ActivityFilter) : "all";
}

/**
 * Serialize a filter to a query string, emitting the param only when it differs
 * from the default so a pristine feed stays at a clean URL.
 */
export function activityFilterToQuery(filter: ActivityFilter): string {
  const params = new URLSearchParams();
  if (filter !== "all") {
    params.set(FILTER_PARAM, filter);
  }
  return params.toString();
}
