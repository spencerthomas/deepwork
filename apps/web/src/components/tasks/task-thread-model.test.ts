import { describe, expect, it } from "vitest";

import { buildThread } from "./task-thread-model";
import type { TaskDetail, TaskEvent } from "../../lib/task-types";

function event(id: string, name: TaskEvent["name"], data: Record<string, unknown> = {}): TaskEvent {
  return { id, name, data };
}

const detailWaiting: TaskDetail = {
  taskId: "task_00000001",
  runId: "run_00000001",
  title: "Research the landscape",
  status: "waiting-approval",
  pendingInterrupt: {
    interruptId: "interrupt_00000001",
    title: "Review the proposed plan",
    question: "Approve, edit, reject, or respond?",
    decisions: ["approve", "reject", "respond"],
    planRevision: 1,
  },
};

describe("buildThread", () => {
  it("projects the canonical happy-path event sequence", () => {
    const items = buildThread(detailWaiting, [
      event("1", "task.created"),
      event("2", "run.started"),
      event("3", "content.delta", { text: "I prepared a brief." }),
      event("4", "evidence.recorded", { summary: "Objective recorded." }),
      event("5", "plan.proposed", { revision: 1 }),
      event("6", "interrupt.requested", { interruptId: "interrupt_00000001" }),
    ]);

    expect(items.map((item) => item.kind)).toEqual([
      "marker",
      "marker",
      "narration",
      "marker",
      "plan",
      "interrupt",
    ]);
  });

  it("only renders the pending interrupt as actionable", () => {
    const items = buildThread(detailWaiting, [
      event("1", "interrupt.requested", { interruptId: "interrupt_10000001" }),
      event("2", "decision.recorded", { interruptId: "interrupt_10000001", decision: "respond" }),
      event("3", "interrupt.requested", { interruptId: "interrupt_00000001" }),
    ]);

    const interrupts = items.filter((item) => item.kind === "interrupt");
    expect(interrupts).toHaveLength(1);
    expect(interrupts[0]).toMatchObject({ interruptId: "interrupt_00000001" });
    expect(items[0]).toMatchObject({ kind: "marker", label: "Approval requested" });
  });

  it("collapses superseded plans into markers and keeps only the newest revision", () => {
    const items = buildThread(detailWaiting, [
      event("1", "plan.proposed", { revision: 1 }),
      event("2", "plan.updated", { revision: 2 }),
    ]);

    expect(items[0]).toMatchObject({ kind: "marker", label: "Plan proposed" });
    expect(items[1]).toMatchObject({ kind: "plan", revision: 2 });
  });

  it("maps completion statuses and never invents success from unknown data", () => {
    const done = buildThread(undefined, [event("9", "run.completed", { status: "completed" })]);
    expect(done[0]).toMatchObject({ kind: "result", status: "completed" });

    const strange = buildThread(undefined, [event("9", "run.completed", { status: "party" })]);
    expect(strange[0]).toMatchObject({ kind: "result", status: "unknown" });
  });

  it("labels decisions honestly", () => {
    const items = buildThread(undefined, [
      event("1", "decision.recorded", { interruptId: "interrupt_00000001", decision: "approve" }),
      event("2", "decision.recorded", { interruptId: "interrupt_00000001", decision: "reject" }),
    ]);
    expect(items[0]).toMatchObject({ label: "Plan approved — the agent continued." });
    expect(items[1]).toMatchObject({ label: "Plan rejected — the run stopped." });
  });

  it("drops blank narration instead of rendering empty cards", () => {
    const items = buildThread(undefined, [event("1", "content.delta", { text: "   " })]);
    expect(items).toHaveLength(0);
  });
});
