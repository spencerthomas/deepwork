import { panelTabToQuery } from "../tasks/run-panel-url";
import type { ActivityEntry } from "./activity-model";

/**
 * The task-detail link for an activity entry, deep-linking to the run-panel tab
 * that best shows it: an evidence event opens the Evidence tab, any other event
 * opens the Stream (where it appears in context with its detail), and a status
 * entry opens the default Status tab. Relies on the run panel restoring its tab
 * from the ?panel= param.
 */
export function activityEntryHref(entry: ActivityEntry): string {
  const base = `/tasks/${entry.taskId}`;
  if (entry.kind !== "event") {
    return base;
  }
  const tab = entry.eventName === "evidence.recorded" ? "evidence" : "stream";
  const query = panelTabToQuery(tab);
  return query ? `${base}?${query}` : base;
}
