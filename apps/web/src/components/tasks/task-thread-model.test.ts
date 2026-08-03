import { describe, expect, it } from "vitest";

import { buildBoundedThread, buildThread } from "./task-thread-model";
import { getLatestPlan } from "../../lib/task-normalizers";
import type { ProposedPlan, TaskDetail, TaskEvent } from "../../lib/task-types";

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

const eventPlan: ProposedPlan = {
  revision: 2,
  title: "Review the bounded plan",
  steps: ["Inspect the retained history", "Approve the current plan"],
  evidenceRefs: ["event-stream"],
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
    expect(items[2]).toMatchObject({ kind: "narration", label: "Task update" });
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

  it("keeps the latest thread window and reports how much history is hidden", () => {
    const events = Array.from({ length: 105 }, (_, index) =>
      event(String(index + 1), "content.delta", { text: `Update ${String(index + 1)}` }),
    );

    const bounded = buildBoundedThread(undefined, events, undefined, 10);
    expect(bounded.hiddenEventCount).toBe(95);
    expect(bounded.items).toHaveLength(10);
    expect(bounded.items[0]).toMatchObject({ id: "96", kind: "narration" });
    expect(bounded.items[9]).toMatchObject({ id: "105", kind: "narration" });
  });

  it("uses the event-derived current plan revision", () => {
    const detail = {
      ...detailWaiting,
      pendingInterrupt: { ...detailWaiting.pendingInterrupt!, planRevision: eventPlan.revision },
    };
    const events = [
      event("1", "plan.proposed", { ...eventPlan }),
      event("2", "interrupt.requested", { interruptId: "interrupt_00000001" }),
    ];
    const currentPlan = getLatestPlan(detail.proposedPlan, events);

    const bounded = buildBoundedThread(detail, events, currentPlan);

    expect(bounded.items).toEqual([
      { id: "1", kind: "plan", revision: 2 },
      { id: "2", kind: "interrupt", interruptId: "interrupt_00000001" },
    ]);
  });

  it("keeps the current plan beside approval when over 100 later events hide its event", () => {
    const detail = {
      ...detailWaiting,
      pendingInterrupt: { ...detailWaiting.pendingInterrupt!, planRevision: eventPlan.revision },
    };
    const events = [
      event("1", "plan.proposed", { ...eventPlan }),
      ...Array.from({ length: 105 }, (_, index) =>
        event(String(index + 2), "content.delta", { text: `Later update ${String(index + 1)}` }),
      ),
      event("107", "interrupt.requested", { interruptId: "interrupt_00000001" }),
    ];
    const currentPlan = getLatestPlan(detail.proposedPlan, events);

    const bounded = buildBoundedThread(detail, events, currentPlan, 100);
    const planIndex = bounded.items.findIndex((item) => item.kind === "plan");
    const interruptIndex = bounded.items.findIndex((item) => item.kind === "interrupt");

    expect(bounded.items).toHaveLength(100);
    expect(bounded.hiddenEventCount).toBe(7);
    expect(bounded.items[planIndex]).toMatchObject({ id: "1", kind: "plan", revision: 2 });
    expect(interruptIndex).toBe(planIndex + 1);
  });
});
