export const INSPECT_TABS = ["capabilities", "recent-tasks"] as const;

export type InspectTab = (typeof INSPECT_TABS)[number];

const TAB_PARAM = "inspect";
const DEFAULT_TAB: InspectTab = "capabilities";

const KNOWN_TABS = new Set<string>(INSPECT_TABS);

interface ReadonlyParams {
  get(name: string): string | null;
}

/**
 * Derive the inspect tab from URL search params, ignoring anything unrecognised
 * so a hand-edited or stale link fails closed to the default ("capabilities"),
 * matching the URL-restore contract the run panel and queues use.
 */
export function readInspectTab(params: ReadonlyParams): InspectTab {
  const raw = params.get(TAB_PARAM);
  return raw !== null && KNOWN_TABS.has(raw) ? (raw as InspectTab) : DEFAULT_TAB;
}

/**
 * Serialize a tab to a query string, emitting the param only when it differs
 * from the default so a pristine inspector stays at a clean URL.
 */
export function inspectTabToQuery(tab: InspectTab): string {
  const params = new URLSearchParams();
  if (tab !== DEFAULT_TAB) {
    params.set(TAB_PARAM, tab);
  }
  return params.toString();
}
