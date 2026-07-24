import {
  EMPTY_TASK_INBOX_FILTER,
  normalizeTaskQuery,
  TASK_DATE_WINDOW_OPTIONS,
  TASK_STATUS_FILTER_OPTIONS,
  type TaskDateWindow,
  type TaskInboxFilter,
  type TaskStatusFilter,
} from "../task-inbox-filter";

/** The inbox view state that is reflected in the URL so it can be shared and restored. */
export interface InboxView {
  filter: TaskInboxFilter;
  grouped: boolean;
}

const STATUS_PARAM = "status";
const QUERY_PARAM = "q";
const VIEW_PARAM = "view";
const CREATED_PARAM = "created";
const RECENT_VIEW = "recent";

const KNOWN_STATUS = new Set<string>(["all", ...TASK_STATUS_FILTER_OPTIONS]);
const KNOWN_WINDOW = new Set<string>(TASK_DATE_WINDOW_OPTIONS);

interface ReadonlyParams {
  get(name: string): string | null;
}

/**
 * Derive the inbox view from URL search params, ignoring anything unrecognised so
 * a hand-edited or stale link fails closed to the default (grouped, unfiltered).
 */
export function readInboxView(params: ReadonlyParams): InboxView {
  const rawStatus = params.get(STATUS_PARAM);
  const status: TaskStatusFilter =
    rawStatus !== null && KNOWN_STATUS.has(rawStatus) ? (rawStatus as TaskStatusFilter) : "all";
  const query = normalizeTaskQuery(params.get(QUERY_PARAM) ?? "");
  const grouped = params.get(VIEW_PARAM) !== RECENT_VIEW;
  const rawCreated = params.get(CREATED_PARAM);
  const createdWithin =
    rawCreated !== null && KNOWN_WINDOW.has(rawCreated)
      ? (rawCreated as TaskDateWindow)
      : undefined;
  return {
    filter: {
      ...EMPTY_TASK_INBOX_FILTER,
      status,
      query,
      ...(createdWithin === undefined ? {} : { createdWithin }),
    },
    grouped,
  };
}

/**
 * Serialize a view to a query string, emitting only the params that differ from the
 * default so a pristine inbox stays at a clean URL.
 */
export function inboxViewToQuery(view: InboxView): string {
  const params = new URLSearchParams();
  if (view.filter.status !== "all") {
    params.set(STATUS_PARAM, view.filter.status);
  }
  if (view.filter.query.trim() !== "") {
    params.set(QUERY_PARAM, view.filter.query);
  }
  if (view.filter.createdWithin !== undefined) {
    params.set(CREATED_PARAM, view.filter.createdWithin);
  }
  if (!view.grouped) {
    params.set(VIEW_PARAM, RECENT_VIEW);
  }
  return params.toString();
}
