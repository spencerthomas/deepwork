import { describe, expect, it } from "vitest";

import {
  getCompletionResultText,
  getEvidenceRecords,
  getActiveInterrupt,
  getLatestPlan,
  isTerminalStatus,
  normalizeCreateTaskResult,
  normalizeDecisionResult,
  normalizeTaskList,
  normalizeTaskDetail,
  normalizeTaskStatus,
  reduceEventsIntoDetail,
  terminalEventNeedsDetail,
  validateDecisionComment,
  validateDecisionInput,
  validatePlanSteps,
  validatePrompt,
} from "./task-normalizers";
import type { TaskEvent } from "./task-types";

describe("task response normalization", () => {
  it("normalizes API status aliases without treating unknown values as success", () => {
    expect(normalizeTaskStatus("awaiting_approval")).toBe("waiting-approval");
    expect(normalizeTaskStatus("waiting_approval")).toBe("waiting-approval");
    expect(normalizeTaskStatus("complete")).toBe("completed");
    expect(normalizeTaskStatus("surprising")).toBe("unknown");
  });

  it("requires the declared task-list envelope", () => {
    expect(() => normalizeTaskList([])).toThrow("items array");
    expect(
      normalizeTaskList({
        items: [{ taskId: "task-1", status: "queued", prompt: "Draft plan" }],
      }),
    ).toEqual([
      {
        taskId: "task-1",
        title: "Draft plan",
        prompt: "Draft plan",
        status: "queued",
      },
    ]);
  });

  it("requires the exact queued create response", () => {
    expect(
      normalizeCreateTaskResult({
        taskId: "task-1",
        runId: "run-1",
        status: "queued",
      }),
    ).toEqual({ taskId: "task-1", runId: "run-1", status: "queued" });
    expect(() =>
      normalizeCreateTaskResult({
        taskId: "task-1",
        runId: "run-1",
        status: "completed",
      }),
    ).toThrow("must be queued");
  });

  it("rejects malformed decision receipts", () => {
    expect(() =>
      normalizeDecisionResult({
        taskId: "task-1",
        runId: "run-1",
        interruptId: "interrupt-1",
        decision: "approve",
        status: "accepted",
      }),
    ).toThrow("receipt status");
  });
});

describe("validatePrompt", () => {
  it("accepts 8,000 characters and rejects 8,001 without truncating", () => {
    expect(validatePrompt("a".repeat(8_000))).toHaveLength(8_000);
    expect(() => validatePrompt("a".repeat(8_001))).toThrow("cannot exceed 8,000");
  });

  it("counts Unicode code points like the API", () => {
    expect(validatePrompt("😀".repeat(8_000))).toBe("😀".repeat(8_000));
    expect(() => validatePrompt("😀".repeat(8_001))).toThrow("cannot exceed 8,000");
  });
});

describe("validateDecisionComment", () => {
  it("accepts 1,000 Unicode code points and rejects 1,001", () => {
    expect(validateDecisionComment("😀".repeat(1_000))).toBe("😀".repeat(1_000));
    expect(() => validateDecisionComment("😀".repeat(1_001))).toThrow("cannot exceed 1,000");
  });

  it("requires a nonblank response only for respond decisions", () => {
    expect(() =>
      validateDecisionInput({
        interruptId: "interrupt-1",
        decision: "respond",
        comment: "  ",
      }),
    ).toThrow("answering the agent");
    expect(
      validateDecisionInput({
        interruptId: "interrupt-1",
        decision: "approve",
      }),
    ).toEqual({
      interruptId: "interrupt-1",
      decision: "approve",
      comment: undefined,
    });
  });
});

describe("editable plan contracts", () => {
  it("matches the API plan step bounds without truncating Unicode", () => {
    expect(validatePlanSteps(["😀".repeat(1_000)])).toEqual(["😀".repeat(1_000)]);
    expect(() => validatePlanSteps(["😀".repeat(1_001)])).toThrow("cannot exceed 1,000");
    expect(() => validatePlanSteps([])).toThrow("between 1 and 8");
    expect(() => validatePlanSteps(Array.from({ length: 9 }, () => "Step"))).toThrow(
      "between 1 and 8",
    );
    expect(() => validatePlanSteps(["  "])).toThrow("cannot be blank");
    expect(() => validatePlanSteps(["Inspect\u0000Verify"])).toThrow("control characters");
  });

  it("fails closed when an untrusted plan has a mixed steps array", () => {
    expect(() =>
      normalizeTaskDetail({
        taskId: "task-1",
        status: "waiting-approval",
        proposedPlan: {
          revision: 1,
          title: "Safe plan",
          steps: ["Inspect", { secret: "x" }, "Verify"],
          evidenceRefs: [],
        },
      }),
    ).toThrow("steps must all be strings");
  });

  it("normalizes optional detail plan and evidence", () => {
    expect(
      normalizeTaskDetail({
        taskId: "task-1",
        status: "waiting-approval",
        proposedPlan: {
          revision: 2,
          title: "Revised plan",
          steps: ["Inspect", "Verify"],
          evidenceRefs: ["evidence-1"],
        },
        evidence: [
          {
            evidenceId: "evidence-1",
            kind: "fixture",
            summary: "Local inspection",
            source: "deterministic-local-runner",
            verified: false,
          },
        ],
      }),
    ).toMatchObject({
      proposedPlan: { revision: 2, steps: ["Inspect", "Verify"] },
      evidence: [{ evidenceId: "evidence-1", verified: false }],
    });
  });

  it("prefers the latest valid streamed plan and evidence while preserving detail data", () => {
    const events: TaskEvent[] = [
      {
        id: "2",
        name: "plan.updated",
        data: {
          revision: 2,
          title: "Updated",
          steps: ["Inspect safely", "Verify"],
          evidenceRefs: ["evidence-1"],
        },
      },
      {
        id: "3",
        name: "evidence.recorded",
        data: {
          evidenceId: "evidence-2",
          kind: "fixture",
          summary: "Revision checked",
          source: "deterministic-local-runner",
          verified: false,
        },
      },
    ];

    expect(
      getLatestPlan(
        { revision: 1, title: "Original", steps: ["Inspect"], evidenceRefs: [] },
        events,
      )?.revision,
    ).toBe(2);
    expect(
      getEvidenceRecords(
        [
          {
            evidenceId: "evidence-1",
            kind: "fixture",
            summary: "Request inspected",
            source: "deterministic-local-runner",
            verified: false,
          },
        ],
        events,
      ).map((record) => record.evidenceId),
    ).toEqual(["evidence-1", "evidence-2"]);
  });

  it("never downgrades an accepted plan receipt with buffered older events", () => {
    const accepted = {
      revision: 2,
      title: "Accepted revision",
      steps: ["Inspect revision two"],
      evidenceRefs: [],
    };
    const buffered: TaskEvent[] = [
      {
        id: "1",
        name: "plan.proposed",
        data: {
          revision: 1,
          title: "Buffered revision",
          steps: ["Inspect revision one"],
          evidenceRefs: [],
        },
      },
    ];

    expect(getLatestPlan(accepted, buffered)).toEqual(accepted);
  });

  it("treats an equal plan revision as immutable", () => {
    const authoritative = {
      revision: 2,
      title: "Authoritative",
      steps: ["Inspect safely"],
      evidenceRefs: ["evidence-1"],
    };

    expect(
      getLatestPlan(authoritative, [
        {
          id: "conflict",
          name: "plan.updated",
          data: {
            revision: 2,
            title: "Conflicting payload",
            steps: ["Do something else"],
            evidenceRefs: [],
          },
        },
      ]),
    ).toEqual(authoritative);
  });
});

describe("terminal result handling", () => {
  it("reads structured completion output and requests detail when absent", () => {
    const withResult: TaskEvent = {
      id: "complete-1",
      name: "run.completed",
      data: { result: { output: "Prompt-specific result" } },
    };
    const withoutResult: TaskEvent = {
      id: "complete-2",
      name: "run.completed",
      data: { status: "completed" },
    };

    expect(getCompletionResultText(withResult)).toBe("Prompt-specific result");
    expect(terminalEventNeedsDetail(withResult)).toBe(false);
    expect(terminalEventNeedsDetail(withoutResult)).toBe(true);
  });

  it("fails closed on a completion event with a nonterminal status", () => {
    const malformedCompletion: TaskEvent = {
      id: "complete-invalid",
      name: "run.completed",
      data: { status: "running" },
    };
    const reduced = reduceEventsIntoDetail(
      { taskId: "task-1", title: "Ship it", status: "running" },
      [malformedCompletion],
    );

    expect(reduced.status).toBe("unknown");
    expect(isTerminalStatus(reduced.status)).toBe(false);
  });

  it("does not make a rejection terminal before run.completed", () => {
    const status = reduceEventsIntoDetail(
      {
        taskId: "task-1",
        title: "Ship it",
        status: "waiting-approval",
        pendingInterrupt: {
          interruptId: "interrupt-1",
          decisions: ["approve", "reject"],
          title: "Approval required",
          question: "Continue?",
        },
      },
      [
        {
          id: "decision-1",
          name: "decision.recorded",
          data: {
            interruptId: "interrupt-1",
            decision: "reject",
          },
        },
      ],
    ).status;

    expect(status).toBe("running");
    expect(isTerminalStatus(status)).toBe(false);
  });

  it("does not change status or controls for a stale decision", () => {
    const detail = reduceEventsIntoDetail(
      {
        taskId: "task-1",
        title: "Ship it",
        status: "waiting-approval",
        pendingInterrupt: {
          interruptId: "interrupt-current",
          decisions: ["approve", "reject", "respond"],
          title: "Current request",
          question: "Continue?",
        },
      },
      [
        {
          id: "decision-stale",
          name: "decision.recorded",
          data: { interruptId: "interrupt-old", decision: "approve" },
        },
      ],
    );

    expect(detail.status).toBe("waiting-approval");
    expect(detail.pendingInterrupt?.interruptId).toBe("interrupt-current");
  });

  it("reduces early stream events into a later detail response", () => {
    const detail = reduceEventsIntoDetail(
      {
        taskId: "task-1",
        title: "Ship it",
        status: "queued",
      },
      [
        { id: "1", name: "run.started", data: { status: "running" } },
        {
          id: "2",
          name: "interrupt.requested",
          data: { interruptId: "interrupt-1" },
        },
      ],
    );

    expect(detail.status).toBe("waiting-approval");
  });
});

describe("getActiveInterrupt", () => {
  it("retains an interrupt until its streamed decision is recorded", () => {
    const requested: TaskEvent = {
      id: "1",
      name: "interrupt.requested",
      data: {
        interruptId: "interrupt-1",
        question: "Continue?",
      },
    };
    const recorded: TaskEvent = {
      id: "2",
      name: "decision.recorded",
      data: {
        interruptId: "interrupt-1",
        decision: "approve",
      },
    };

    expect(getActiveInterrupt([requested])?.interruptId).toBe("interrupt-1");
    expect(getActiveInterrupt([requested, recorded])).toBeUndefined();
  });

  it("does not clear a gate for an uncorrelated decision", () => {
    const requested: TaskEvent = {
      id: "1",
      name: "interrupt.requested",
      data: { interruptId: "interrupt-1" },
    };
    const uncorrelated: TaskEvent = {
      id: "2",
      name: "decision.recorded",
      data: { decision: "approve" },
    };

    expect(getActiveInterrupt([requested, uncorrelated])?.interruptId).toBe("interrupt-1");
  });

  it("does not leave approval controls active after a terminal event", () => {
    const requested: TaskEvent = {
      id: "1",
      name: "interrupt.requested",
      data: { interruptId: "interrupt-1" },
    };
    const completed: TaskEvent = {
      id: "2",
      name: "run.completed",
      data: { status: "rejected" },
    };

    expect(getActiveInterrupt([requested, completed])).toBeUndefined();
  });

  it("advertises respond and the guarded plan revision only when declared", () => {
    const interrupt = getActiveInterrupt([
      {
        id: "1",
        name: "interrupt.requested",
        data: {
          interruptId: "interrupt-1",
          decisions: ["approve", "reject", "respond"],
          planRevision: 3,
        },
      },
    ]);

    expect(interrupt).toMatchObject({
      decisions: ["approve", "reject", "respond"],
      planRevision: 3,
    });
  });

  it("defaults only an absent decisions field and fails closed for explicit invalid lists", () => {
    const absent = getActiveInterrupt([
      {
        id: "1",
        name: "interrupt.requested",
        data: { interruptId: "interrupt-1" },
      },
    ]);
    const empty = getActiveInterrupt([
      {
        id: "2",
        name: "interrupt.requested",
        data: { interruptId: "interrupt-2", decisions: [] },
      },
    ]);
    const mixed = getActiveInterrupt([
      {
        id: "3",
        name: "interrupt.requested",
        data: { interruptId: "interrupt-3", decisions: ["approve", "skip"] },
      },
    ]);

    expect(absent?.decisions).toEqual(["approve", "reject"]);
    expect(empty?.decisions).toEqual([]);
    expect(mixed?.decisions).toEqual([]);
  });

  it("advances the revision for repeated edits under the same interrupt", () => {
    const interrupt: TaskEvent = {
      id: "1",
      name: "interrupt.requested",
      data: {
        interruptId: "interrupt-1",
        decisions: ["approve", "reject", "respond"],
        planRevision: 1,
      },
    };
    const revisionTwo: TaskEvent = {
      id: "2",
      name: "plan.updated",
      data: {
        revision: 2,
        title: "Revision two",
        steps: ["Inspect"],
        evidenceRefs: [],
      },
    };
    const revisionThree: TaskEvent = {
      id: "3",
      name: "plan.updated",
      data: {
        revision: 3,
        title: "Revision three",
        steps: ["Inspect", "Verify"],
        evidenceRefs: [],
      },
    };

    expect(getActiveInterrupt([interrupt, revisionTwo])?.planRevision).toBe(2);
    expect(getActiveInterrupt([interrupt, revisionTwo, revisionThree])).toMatchObject({
      interruptId: "interrupt-1",
      planRevision: 3,
    });
  });

  it("offers fresh controls after a response resolves the old interrupt", () => {
    const active = getActiveInterrupt([
      {
        id: "1",
        name: "interrupt.requested",
        data: {
          interruptId: "interrupt-1",
          decisions: ["approve", "reject", "respond"],
          planRevision: 1,
        },
      },
      {
        id: "2",
        name: "decision.recorded",
        data: {
          interruptId: "interrupt-1",
          decision: "respond",
          responseProvided: true,
        },
      },
      {
        id: "3",
        name: "interrupt.requested",
        data: {
          interruptId: "interrupt-2",
          decisions: ["approve", "reject", "respond"],
          planRevision: 2,
        },
      },
    ]);

    expect(active).toMatchObject({
      interruptId: "interrupt-2",
      decisions: ["approve", "reject", "respond"],
      planRevision: 2,
    });
  });
});
