import { describe, expect, it } from "vitest";

import type { ActiveInterrupt, TaskDetail, TaskStatus, TaskSummary } from "../../lib/task-types";
import {
  approvalCapabilityCounts,
  deriveApprovalRows,
  filterRowsByCapability,
  orderedDecisions,
  waitingTaskIdsNeedingDetail,
} from "./approvals-model";

function task(taskId: string, status: TaskStatus): TaskSummary {
  return { taskId, title: `Task ${taskId}`, status };
}

function interrupt(interruptId: string, decisions: ActiveInterrupt["decisions"]): ActiveInterrupt {
  return {
    interruptId,
    decisions,
    title: "Approval required",
    question: "Proceed?",
  };
}

function detailWithInterrupt(summary: TaskSummary, active: ActiveInterrupt): TaskDetail {
  return {
    ...summary,
    pendingInterrupt: active,
    proposedPlan: {
      evidenceRefs: ["ref-1"],
      revision: 2,
      steps: ["step one", "step two"],
      title: "The plan",
    },
  };
}

describe("deriveApprovalRows", () => {
  const waitingOld = task("task_00000002", "waiting-approval");
  const waitingNew = task("task_00000010", "waiting-approval");
  const running = task("task_00000004", "running");
  const completed = task("task_00000003", "completed");

  it("keeps only waiting-approval tasks, oldest dispatch first by numeric id", () => {
    const rows = deriveApprovalRows([waitingNew, running, completed, waitingOld], {});
    expect(rows.map((row) => row.task.taskId)).toEqual(["task_00000002", "task_00000010"]);
  });

  it("attaches the hydrated interrupt and plan from detailsByTask", () => {
    const active = interrupt("int-1", ["approve", "reject"]);
    const rows = deriveApprovalRows([waitingOld], {
      [waitingOld.taskId]: detailWithInterrupt(waitingOld, active),
    });
    expect(rows[0]?.interrupt).toEqual(active);
    expect(rows[0]?.plan?.revision).toBe(2);
    expect(rows[0]?.plan?.steps).toEqual(["step one", "step two"]);
  });

  it("leaves interrupt undefined until loadDetail hydrates the task", () => {
    const rows = deriveApprovalRows([waitingOld], {});
    expect(rows[0]?.interrupt).toBeUndefined();
    expect(rows[0]?.plan).toBeUndefined();
  });

  it("drops rows whose interrupt was already decided in this session", () => {
    const active = interrupt("int-decided", ["approve"]);
    const rows = deriveApprovalRows(
      [waitingOld],
      { [waitingOld.taskId]: detailWithInterrupt(waitingOld, active) },
      new Set(["int-decided"]),
    );
    expect(rows).toEqual([]);
  });

  it("keeps an undecided row even when other interrupts were resolved", () => {
    const active = interrupt("int-live", ["approve"]);
    const rows = deriveApprovalRows(
      [waitingOld],
      { [waitingOld.taskId]: detailWithInterrupt(waitingOld, active) },
      new Set(["int-other"]),
    );
    expect(rows).toHaveLength(1);
  });
});

describe("waitingTaskIdsNeedingDetail", () => {
  it("lists waiting tasks with no detail or with a detail that lacks an interrupt", () => {
    const bare = task("task_00000001", "waiting-approval");
    const summaryOnly = task("task_00000002", "waiting-approval");
    const hydrated = task("task_00000003", "waiting-approval");
    const running = task("task_00000004", "running");

    const needing = waitingTaskIdsNeedingDetail([bare, summaryOnly, hydrated, running], {
      [summaryOnly.taskId]: { ...summaryOnly },
      [hydrated.taskId]: detailWithInterrupt(hydrated, interrupt("int-3", ["approve"])),
    });

    expect(needing).toEqual(["task_00000001", "task_00000002"]);
  });
});

describe("orderedDecisions", () => {
  it("renders verbs in canonical order regardless of the wire order", () => {
    expect(orderedDecisions(interrupt("i", ["respond", "approve"]))).toEqual([
      "approve",
      "respond",
    ]);
    expect(orderedDecisions(interrupt("i", ["reject", "respond", "approve"]))).toEqual([
      "approve",
      "reject",
      "respond",
    ]);
  });

  it("never invents a verb the interrupt did not advertise", () => {
    expect(orderedDecisions(interrupt("i", []))).toEqual([]);
    expect(orderedDecisions(interrupt("i", ["respond"]))).toEqual(["respond"]);
  });
});

describe("capability counts and filtering", () => {
  const a = task("task_00000001", "waiting-approval");
  const b = task("task_00000002", "waiting-approval");
  const c = task("task_00000003", "waiting-approval");
  const rows = deriveApprovalRows([a, b, c], {
    [a.taskId]: detailWithInterrupt(a, interrupt("int-a", ["approve", "reject"])),
    [b.taskId]: detailWithInterrupt(b, interrupt("int-b", ["respond"])),
    // c stays unhydrated.
  });

  it("counts each verb only across loaded interrupts", () => {
    expect(approvalCapabilityCounts(rows)).toEqual({ approve: 1, reject: 1, respond: 1 });
  });

  it("keeps unhydrated rows under the all filter but not under verb filters", () => {
    expect(filterRowsByCapability(rows, "all").map((row) => row.task.taskId)).toEqual([
      "task_00000001",
      "task_00000002",
      "task_00000003",
    ]);
    expect(filterRowsByCapability(rows, "approve").map((row) => row.task.taskId)).toEqual([
      "task_00000001",
    ]);
    expect(filterRowsByCapability(rows, "respond").map((row) => row.task.taskId)).toEqual([
      "task_00000002",
    ]);
    expect(filterRowsByCapability(rows, "reject").map((row) => row.task.taskId)).toEqual([
      "task_00000001",
    ]);
  });
});
