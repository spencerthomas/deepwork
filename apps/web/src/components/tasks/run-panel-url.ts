import { type PanelTab, PANEL_TABS } from "./run-panel-tabs";

const TAB_PARAM = "panel";
const DEFAULT_TAB: PanelTab = "status";

const KNOWN_TABS = new Set<string>(PANEL_TABS.map((tab) => tab.key));

interface ReadonlyParams {
  get(name: string): string | null;
}

/**
 * Derive the run-panel tab from URL search params, ignoring anything
 * unrecognised so a hand-edited or stale link fails closed to the default
 * ("status"), matching the URL-restore contract the inbox and queues use.
 */
export function readPanelTab(params: ReadonlyParams): PanelTab {
  const raw = params.get(TAB_PARAM);
  return raw !== null && KNOWN_TABS.has(raw) ? (raw as PanelTab) : DEFAULT_TAB;
}

/**
 * Serialize a tab to a query string, emitting the param only when it differs
 * from the default so a pristine task detail stays at a clean URL. Any other
 * existing params are preserved.
 */
export function panelTabToQuery(tab: PanelTab, existing?: URLSearchParams): string {
  const params = new URLSearchParams(existing);
  if (tab === DEFAULT_TAB) {
    params.delete(TAB_PARAM);
  } else {
    params.set(TAB_PARAM, tab);
  }
  return params.toString();
}
