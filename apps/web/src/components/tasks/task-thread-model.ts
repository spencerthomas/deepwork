import { getEventText } from "@/lib/task-normalizers";
import type { ProposedPlan, TaskDetail, TaskEvent } from "@/lib/task-types";

export type ThreadItem =
  | { kind: "narration"; id: string; label: string; text: string }
  | { kind: "marker"; id: string; label: string; detail?: string }
  | { kind: "plan"; id: string; revision: number }
  | { kind: "interrupt"; id: string; interruptId: string }
  | {
      kind: "result";
      id: string;
      status: "completed" | "rejected" | "failed" | "cancelled" | "unknown";
    };

export const TASK_THREAD_RENDER_LIMIT = 100;

export interface BoundedThread {
  hiddenEventCount: number;
  items: readonly ThreadItem[];
}

/**
 * Keep the latest lifecycle items mounted while retaining the complete event
 * transcript in the store and Stream panel. The result and current approval
 * live at the tail of the ordered thread, so they remain immediately usable.
 */
export function buildBoundedThread(
  detail: TaskDetail | undefined,
  events: readonly TaskEvent[],
  currentPlan: ProposedPlan | undefined,
  maximumItems = TASK_THREAD_RENDER_LIMIT,
): BoundedThread {
  const limit = Math.max(1, Math.floor(maximumItems));
  const pendingInterruptId = detail?.pendingInterrupt?.interruptId;
  const currentPlanRevision = currentPlan?.revision;
  let currentPlanEventId: string | undefined;

  if (currentPlanRevision !== undefined) {
    for (let index = events.length - 1; index >= 0; index -= 1) {
      const event = events[index];
      if (
        event !== undefined &&
        (event.name === "plan.proposed" || event.name === "plan.updated") &&
        eventPlanRevision(event) === currentPlanRevision
      ) {
        currentPlanEventId = event.id;
        break;
      }
    }
  }

  const items: ThreadItem[] = [];
  let index = events.length - 1;
  for (; index >= 0 && items.length < limit; index -= 1) {
    const event = events[index];
    if (event === undefined) continue;
    const item = threadItem(
      event,
      pendingInterruptId,
      currentPlanEventId,
      currentPlanRevision ?? 0,
    );
    if (item !== undefined) items.push(item);
  }

  const visibleItems = items.reverse();
  const hasActiveInterrupt = visibleItems.some(
    (item) => item.kind === "interrupt" && item.interruptId === pendingInterruptId,
  );
  const hasCurrentPlan = visibleItems.some(
    (item) => item.kind === "plan" && item.revision === currentPlanRevision,
  );
  let displacedEventCount = 0;

  // A long narration tail can push the current plan outside the fixed window
  // while its approval remains visible. Keep that checkpoint together by
  // replacing the oldest passive item with the authoritative current plan.
  if (hasActiveInterrupt && currentPlanRevision !== undefined && !hasCurrentPlan) {
    if (visibleItems.length >= limit) {
      const removableIndex = visibleItems.findIndex((item) => item.kind !== "interrupt");
      if (removableIndex >= 0) {
        visibleItems.splice(removableIndex, 1);
        if (currentPlanEventId === undefined) displacedEventCount = 1;
      }
    }
    const interruptIndex = visibleItems.findIndex(
      (item) => item.kind === "interrupt" && item.interruptId === pendingInterruptId,
    );
    visibleItems.splice(interruptIndex, 0, {
      kind: "plan",
      id: currentPlanEventId ?? `current-plan:${String(currentPlanRevision)}`,
      revision: currentPlanRevision,
    });
  }

  return {
    hiddenEventCount: index + 1 + displacedEventCount,
    items: visibleItems,
  };
}

function decisionLabel(event: TaskEvent): string {
  const decision = event.data.decision;
  if (decision === "approve") return "Plan approved — the agent continued.";
  if (decision === "reject") return "Plan rejected — the run stopped.";
  if (decision === "respond") return "Response sent — the agent revised its plan.";
  return "Decision recorded.";
}

function eventPlanRevision(event: TaskEvent): number | undefined {
  if (typeof event.data.revision === "number") return event.data.revision;
  const plan = event.data.plan;
  return plan !== null &&
    typeof plan === "object" &&
    "revision" in plan &&
    typeof (plan as { revision: unknown }).revision === "number"
    ? (plan as { revision: number }).revision
    : undefined;
}

function threadItem(
  event: TaskEvent,
  pendingInterruptId: string | undefined,
  latestPlanEventId: string | undefined,
  latestPlanRevision: number,
): ThreadItem | undefined {
  switch (event.name) {
    case "task.created":
      return { kind: "marker", id: event.id, label: "Task created" };
    case "run.started":
      return { kind: "marker", id: event.id, label: "Run started" };
    case "content.delta": {
      const text = getEventText(event) ?? "";
      return text.trim() === ""
        ? undefined
        : { kind: "narration", id: event.id, label: "Task update", text };
    }
    case "plan.proposed":
    case "plan.updated":
      return event.id === latestPlanEventId
        ? { kind: "plan", id: event.id, revision: latestPlanRevision }
        : {
            kind: "marker",
            id: event.id,
            label: event.name === "plan.proposed" ? "Plan proposed" : "Plan updated",
            detail: "Superseded by a newer revision.",
          };
    case "evidence.recorded":
      return {
        kind: "marker",
        id: event.id,
        label: "Sources recorded",
        detail: typeof event.data.summary === "string" ? event.data.summary : undefined,
      };
    case "interrupt.requested": {
      const interruptId = typeof event.data.interruptId === "string" ? event.data.interruptId : "";
      return interruptId !== "" && interruptId === pendingInterruptId
        ? { kind: "interrupt", id: event.id, interruptId }
        : {
            kind: "marker",
            id: event.id,
            label: "Approval requested",
            detail: "Resolved below.",
          };
    }
    case "decision.recorded":
      return { kind: "marker", id: event.id, label: decisionLabel(event) };
    case "run.completed": {
      const status = typeof event.data.status === "string" ? event.data.status : "unknown";
      return {
        kind: "result",
        id: event.id,
        status:
          status === "completed" ||
          status === "rejected" ||
          status === "failed" ||
          status === "cancelled"
            ? status
            : "unknown",
      };
    }
    default:
      return undefined;
  }
}

/**
 * Project the ordered SSE events into renderable thread items. Only the
 * currently pending interrupt renders as an actionable card; superseded
 * interrupts and plans collapse into markers so history stays honest without
 * offering stale controls.
 */
export function buildThread(
  detail: TaskDetail | undefined,
  events: readonly TaskEvent[],
): ThreadItem[] {
  const items: ThreadItem[] = [];
  const pendingInterruptId = detail?.pendingInterrupt?.interruptId;
  let latestPlanEventId: string | undefined;
  let latestPlanRevision = 0;

  for (const event of events) {
    if (event.name === "plan.proposed" || event.name === "plan.updated") {
      const effective = eventPlanRevision(event) ?? latestPlanRevision + 1;
      if (effective >= latestPlanRevision) {
        latestPlanRevision = effective;
        latestPlanEventId = event.id;
      }
    }
  }

  for (const event of events) {
    const item = threadItem(event, pendingInterruptId, latestPlanEventId, latestPlanRevision);
    if (item !== undefined) items.push(item);
  }

  return items;
}
