import { getEventText } from "../../lib/task-normalizers";
import type { TaskEvent, TaskEventName, TaskStatus, TaskSummary } from "../../lib/task-types";

export const ACTIVITY_FILTERS = ["all", "plans", "evidence", "decisions", "completions"] as const;

export type ActivityFilter = (typeof ACTIVITY_FILTERS)[number];

export const ACTIVITY_FILTER_LABELS: Record<ActivityFilter, string> = {
  all: "All events",
  plans: "Plans",
  evidence: "Evidence",
  decisions: "Decisions",
  completions: "Completions",
};

const FILTER_EVENT_NAMES: Record<Exclude<ActivityFilter, "all">, readonly TaskEventName[]> = {
  plans: ["plan.proposed", "plan.updated"],
  evidence: ["evidence.recorded"],
  decisions: ["interrupt.requested", "decision.recorded"],
  completions: ["run.completed"],
};

export const EVENT_LABELS: Record<TaskEventName, string> = {
  "task.created": "Task created",
  "run.started": "Run started",
  "content.delta": "Output streamed",
  "plan.proposed": "Plan proposed",
  "plan.updated": "Plan updated",
  "evidence.recorded": "Evidence recorded",
  "interrupt.requested": "Approval requested",
  "decision.recorded": "Decision recorded",
  "run.completed": "Run completed",
};

export interface ActivityStatusEntry {
  key: string;
  kind: "status";
  status: TaskStatus;
  taskId: string;
  taskTitle: string;
}

export interface ActivityEventEntry {
  detail?: string;
  eventId: string;
  eventName: TaskEventName;
  key: string;
  kind: "event";
  taskId: string;
  taskTitle: string;
}

export type ActivityEntry = ActivityStatusEntry | ActivityEventEntry;

/** Trailing digits of an id ("task_00000003" → 3, "task_00000003:12" → 12). */
export function trailingNumber(id: string): number | undefined {
  const match = /(\d+)$/.exec(id);
  return match ? Number.parseInt(match[1], 10) : undefined;
}

/**
 * Newest task first, by the runner-assigned numeric id — no fabricated
 * timestamps. Ids without trailing digits sort after numbered ids,
 * reverse-lexicographically.
 */
export function compareTaskIdsNewestFirst(a: string, b: string): number {
  const numericA = trailingNumber(a);
  const numericB = trailingNumber(b);
  if (numericA !== undefined && numericB !== undefined && numericA !== numericB) {
    return numericB - numericA;
  }
  if (numericA !== undefined && numericB === undefined) {
    return -1;
  }
  if (numericA === undefined && numericB !== undefined) {
    return 1;
  }
  return a > b ? -1 : a < b ? 1 : 0;
}

/**
 * Within one task, events keep the runner's own sequence: ascending numeric
 * event id when both ids carry one, otherwise stable arrival order.
 */
export function compareEventIdsAscending(a: string, b: string): number {
  const numericA = trailingNumber(a);
  const numericB = trailingNumber(b);
  return numericA !== undefined && numericB !== undefined ? numericA - numericB : 0;
}

const DETAIL_MAX_LENGTH = 160;

function condense(text: string): string {
  const flat = text.replaceAll(/\s+/g, " ").trim();
  const characters = [...flat];
  return characters.length > DETAIL_MAX_LENGTH
    ? `${characters.slice(0, DETAIL_MAX_LENGTH - 1).join("")}…`
    : flat;
}

/** A short, real excerpt from the event payload. Undefined when there is none. */
export function eventDetailText(event: TaskEvent): string | undefined {
  if (event.name === "decision.recorded") {
    const decision = event.data.decision;
    if (decision === "approve" || decision === "reject" || decision === "respond") {
      return `Decision: ${decision}`;
    }
  }
  if (event.name === "plan.proposed" || event.name === "plan.updated") {
    const title =
      typeof event.data.title === "string" && event.data.title.trim() !== ""
        ? event.data.title.trim()
        : undefined;
    const revision = Number.isInteger(event.data.revision)
      ? Number(event.data.revision)
      : undefined;
    const parts = [revision === undefined ? undefined : `Revision ${revision}`, title].filter(
      (part): part is string => part !== undefined,
    );
    if (parts.length > 0) {
      return condense(parts.join(" — "));
    }
  }
  if (event.name === "interrupt.requested") {
    for (const key of ["question", "title"]) {
      const value = event.data[key];
      if (typeof value === "string" && value.trim() !== "") {
        return condense(value);
      }
    }
  }
  const text = getEventText(event);
  return text === undefined ? undefined : condense(text);
}

/**
 * Merge real store data into one feed: a status entry per known task, plus
 * every event this browser session has observed, grouped under its task.
 * Tasks are ordered newest first by numeric task id; a task's events follow
 * its status entry in the runner's own event-id order. Events for tasks
 * missing from the list (e.g. after a failed list fetch) still appear, with
 * the task id standing in for the unknown title.
 */
export function buildActivityFeed(
  tasks: readonly TaskSummary[],
  eventsByTask: Readonly<Record<string, readonly TaskEvent[]>>,
): ActivityEntry[] {
  const tasksById = new Map(tasks.map((task) => [task.taskId, task] as const));
  const taskIds = new Set<string>(tasksById.keys());
  for (const [taskId, events] of Object.entries(eventsByTask)) {
    if (events.length > 0) {
      taskIds.add(taskId);
    }
  }

  const entries: ActivityEntry[] = [];
  for (const taskId of [...taskIds].sort(compareTaskIdsNewestFirst)) {
    const task = tasksById.get(taskId);
    const taskTitle = task?.title ?? taskId;
    if (task) {
      entries.push({
        key: `status:${taskId}`,
        kind: "status",
        status: task.status,
        taskId,
        taskTitle,
      });
    }
    const events = [...(eventsByTask[taskId] ?? [])].sort((a, b) =>
      compareEventIdsAscending(a.id, b.id),
    );
    for (const event of events) {
      entries.push({
        detail: eventDetailText(event),
        eventId: event.id,
        eventName: event.name,
        key: `event:${taskId}:${event.id}`,
        kind: "event",
        taskId,
        taskTitle,
      });
    }
  }
  return entries;
}

/**
 * "all" keeps everything, including per-task status entries. A named filter
 * keeps only the event entries in its group.
 */
export function filterActivityFeed(
  entries: readonly ActivityEntry[],
  filter: ActivityFilter,
): ActivityEntry[] {
  if (filter === "all") {
    return [...entries];
  }
  const names = FILTER_EVENT_NAMES[filter];
  return entries.filter((entry) => entry.kind === "event" && names.includes(entry.eventName));
}

export function activityFilterCounts(
  entries: readonly ActivityEntry[],
): Record<ActivityFilter, number> {
  return {
    all: entries.length,
    plans: filterActivityFeed(entries, "plans").length,
    evidence: filterActivityFeed(entries, "evidence").length,
    decisions: filterActivityFeed(entries, "decisions").length,
    completions: filterActivityFeed(entries, "completions").length,
  };
}
