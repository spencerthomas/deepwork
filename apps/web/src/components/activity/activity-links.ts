import type { PanelTab } from "../tasks/run-panel-tabs";
import { panelTabToQuery } from "../tasks/run-panel-url";
import type { ActivityEntry, ActivityEventEntry } from "./activity-model";

/**
 * The run-panel tab that best shows a given event: evidence opens the Evidence
 * tab; a plan proposal/update opens the Status tab, where the run panel renders
 * the plan steps; everything else opens the Stream, where it appears in context
 * with its detail. Status is the run panel's default, so it needs no ?panel=.
 */
function tabForEvent(eventName: ActivityEventEntry["eventName"]): PanelTab {
  if (eventName === "evidence.recorded") {
    return "evidence";
  }
  if (eventName === "plan.proposed" || eventName === "plan.updated") {
    return "status";
  }
  return "stream";
}

/**
 * The task-detail link for an activity entry, deep-linking to the run-panel tab
 * that best shows it (see tabForEvent). A status entry opens the default Status
 * tab. Relies on the run panel restoring its tab from the ?panel= param.
 */
export function activityEntryHref(entry: ActivityEntry): string {
  const base = `/tasks/${entry.taskId}`;
  if (entry.kind !== "event") {
    return base;
  }
  const query = panelTabToQuery(tabForEvent(entry.eventName));
  return query ? `${base}?${query}` : base;
}
