import { getEventText } from "@/lib/task-normalizers";
import type { TaskDetail, TaskEvent } from "@/lib/task-types";

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

function decisionLabel(event: TaskEvent): string {
  const decision = event.data.decision;
  if (decision === "approve") return "Plan approved — the agent continued.";
  if (decision === "reject") return "Plan rejected — the run stopped.";
  if (decision === "respond") return "Response sent — the agent revised its plan.";
  return "Decision recorded.";
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
      const revision = typeof event.data.revision === "number" ? event.data.revision : undefined;
      const planData = event.data.plan;
      const nestedRevision =
        planData !== null &&
        typeof planData === "object" &&
        "revision" in planData &&
        typeof (planData as { revision: unknown }).revision === "number"
          ? (planData as { revision: number }).revision
          : undefined;
      const effective = revision ?? nestedRevision ?? latestPlanRevision + 1;
      if (effective >= latestPlanRevision) {
        latestPlanRevision = effective;
        latestPlanEventId = event.id;
      }
    }
  }

  for (const event of events) {
    switch (event.name) {
      case "task.created":
        items.push({ kind: "marker", id: event.id, label: "Task created" });
        break;
      case "run.started":
        items.push({ kind: "marker", id: event.id, label: "Run started" });
        break;
      case "content.delta": {
        const text = getEventText(event) ?? "";
        if (text.trim() !== "") {
          items.push({ kind: "narration", id: event.id, label: "Local agent", text });
        }
        break;
      }
      case "plan.proposed":
      case "plan.updated":
        if (event.id === latestPlanEventId) {
          items.push({ kind: "plan", id: event.id, revision: latestPlanRevision });
        } else {
          items.push({
            kind: "marker",
            id: event.id,
            label: event.name === "plan.proposed" ? "Plan proposed" : "Plan updated",
            detail: "Superseded by a newer revision.",
          });
        }
        break;
      case "evidence.recorded":
        items.push({
          kind: "marker",
          id: event.id,
          label: "Evidence recorded",
          detail: typeof event.data.summary === "string" ? event.data.summary : undefined,
        });
        break;
      case "interrupt.requested": {
        const interruptId =
          typeof event.data.interruptId === "string" ? event.data.interruptId : "";
        if (interruptId !== "" && interruptId === pendingInterruptId) {
          items.push({ kind: "interrupt", id: event.id, interruptId });
        } else {
          items.push({
            kind: "marker",
            id: event.id,
            label: "Approval requested",
            detail: "Resolved below.",
          });
        }
        break;
      }
      case "decision.recorded":
        items.push({ kind: "marker", id: event.id, label: decisionLabel(event) });
        break;
      case "run.completed": {
        const status = typeof event.data.status === "string" ? event.data.status : "unknown";
        items.push({
          kind: "result",
          id: event.id,
          status:
            status === "completed" ||
            status === "rejected" ||
            status === "failed" ||
            status === "cancelled"
              ? status
              : "unknown",
        });
        break;
      }
      default:
        break;
    }
  }

  return items;
}
