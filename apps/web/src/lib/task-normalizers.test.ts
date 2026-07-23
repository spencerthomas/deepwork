import { describe, expect, it } from "vitest";

import {
  getCompletionResultText,
  getActiveInterrupt,
  isTerminalStatus,
  normalizeCreateTaskResult,
  normalizeTaskList,
  normalizeTaskStatus,
  reduceEventsIntoDetail,
  terminalEventNeedsDetail,
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
});

describe("validatePrompt", () => {
  it("accepts 8,000 characters and rejects 8,001 without truncating", () => {
    expect(validatePrompt("a".repeat(8_000))).toHaveLength(8_000);
    expect(() => validatePrompt("a".repeat(8_001))).toThrow(
      "cannot exceed 8,000",
    );
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

    expect(getActiveInterrupt([requested, uncorrelated])?.interruptId).toBe(
      "interrupt-1",
    );
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
});
