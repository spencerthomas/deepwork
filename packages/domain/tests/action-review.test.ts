import {
  actionRequest,
  batchDecisionInput,
  interruptId,
  pendingInterrupt,
  reviewConfig,
  runId,
  sourceId,
  sourceInterruptKey,
  taskId,
  threadId,
} from "@deepwork/domain";
import { describe, expect, it } from "vitest";

const identity = sourceInterruptKey(
  sourceId("source-a"),
  taskId("task_00000001"),
  threadId("thread-a"),
  runId("run_00000001"),
  interruptId("interrupt_00000001"),
);

function repeatedActionInterrupt() {
  return pendingInterrupt({
    identity,
    decisions: ["approve", "reject", "respond"],
    planRevision: 2,
    version: "7",
    actionRequests: [
      actionRequest({ name: "write_file", args: { path: "first.txt", body: { value: 1 } } }),
      actionRequest({ name: "write_file", args: { path: "second.txt", body: { value: 2 } } }),
    ],
    reviewConfigs: [
      reviewConfig({ actionName: "write_file", allowedDecisions: ["approve", "reject"] }),
      reviewConfig({
        actionName: "write_file",
        allowedDecisions: ["edit", "reject"],
        argsSchema: { type: "object", required: ["path", "body"] },
      }),
    ],
  });
}

describe("ordered action review contracts", () => {
  it("preserves repeated action names by position and accepts approve plus edit", () => {
    const current = repeatedActionInterrupt();
    const input = batchDecisionInput(current, {
      expectedVersion: "7",
      idempotencyKey: "decision-key-0001",
      decisions: [
        { type: "approve" },
        {
          type: "edit",
          editedAction: { name: "write_file", args: { path: "second.txt", body: { value: 3 } } },
        },
      ],
    });

    expect(current.actionRequests?.map((request) => request.args.path)).toEqual([
      "first.txt",
      "second.txt",
    ]);
    expect(input.decisions.map((decision) => decision.type)).toEqual(["approve", "edit"]);
    expect(input.interrupt).toEqual(identity);
    expect(Object.isFrozen(input.decisions)).toBe(true);
    expect(Object.isFrozen(input.decisions[1])).toBe(true);
    expect(
      Object.isFrozen(
        input.decisions[1]?.type === "edit" ? input.decisions[1].editedAction.args : undefined,
      ),
    ).toBe(true);
  });

  it("rejects misaligned configs, disallowed decisions, and incomplete vectors", () => {
    expect(() =>
      pendingInterrupt({
        identity,
        decisions: ["approve"],
        planRevision: 2,
        version: "7",
        actionRequests: [actionRequest({ name: "write_file", args: {} })],
        reviewConfigs: [reviewConfig({ actionName: "send_email", allowedDecisions: ["approve"] })],
      }),
    ).toThrow(TypeError);

    const current = repeatedActionInterrupt();
    expect(() =>
      batchDecisionInput(current, {
        expectedVersion: "7",
        idempotencyKey: "decision-key-0002",
        decisions: [{ type: "respond", message: "Not allowed at index zero." }, { type: "reject" }],
      }),
    ).toThrow(TypeError);
    expect(() =>
      batchDecisionInput(current, {
        expectedVersion: "7",
        idempotencyKey: "decision-key-0003",
        decisions: [{ type: "approve" }],
      }),
    ).toThrow(TypeError);
    expect(() =>
      batchDecisionInput(current, {
        expectedVersion: "7",
        idempotencyKey: "decision-key-0004",
        decisions: [
          { type: "approve" },
          { type: "edit", editedAction: { name: "send_email", args: {} } },
        ],
      }),
    ).toThrow(TypeError);
  });

  it("requires a bounded respond message and deeply snapshots JSON-safe values", () => {
    const mutableArgs = { path: "first.txt", nested: { labels: ["original"] } };
    const request = actionRequest({ name: "write_file", args: mutableArgs });
    mutableArgs.nested.labels[0] = "mutated";

    expect(request.args).toEqual({ path: "first.txt", nested: { labels: ["original"] } });
    expect(Object.isFrozen(request)).toBe(true);
    expect(Object.isFrozen(request.args)).toBe(true);
    expect(Object.isFrozen(request.args.nested)).toBe(true);
    expect(
      Object.isFrozen((request.args.nested as { readonly labels: readonly string[] }).labels),
    ).toBe(true);
    expect(() =>
      actionRequest({ name: "write_file", args: { invalid: undefined } as never }),
    ).toThrow(TypeError);

    const current = pendingInterrupt({
      identity,
      decisions: ["respond"],
      planRevision: 2,
      version: "8",
      actionRequests: [request],
      reviewConfigs: [reviewConfig({ actionName: "write_file", allowedDecisions: ["respond"] })],
    });
    expect(() =>
      batchDecisionInput(current, {
        expectedVersion: "8",
        idempotencyKey: "decision-key-0005",
        decisions: [{ type: "respond", message: "   " }],
      }),
    ).toThrow(TypeError);
  });

  it("matches the API limits for eight actions and 128-character idempotency keys", () => {
    const requests = Array.from({ length: 8 }, (_, index) =>
      actionRequest({ name: "write_file", args: { path: `${index}.txt` } }),
    );
    const configs = requests.map(() =>
      reviewConfig({ actionName: "write_file", allowedDecisions: ["approve"] }),
    );
    const current = pendingInterrupt({
      identity,
      decisions: ["approve"],
      planRevision: 1,
      version: "1",
      actionRequests: requests,
      reviewConfigs: configs,
    });
    expect(
      batchDecisionInput(current, {
        expectedVersion: "1",
        idempotencyKey: "k".repeat(128),
        decisions: requests.map(() => ({ type: "approve" as const })),
      }).decisions,
    ).toHaveLength(8);
    expect(() =>
      pendingInterrupt({
        identity,
        decisions: ["approve"],
        planRevision: 1,
        version: "1",
        actionRequests: [...requests, requests[0]!],
        reviewConfigs: [...configs, configs[0]!],
      }),
    ).toThrow(TypeError);
    expect(() =>
      batchDecisionInput(current, {
        expectedVersion: "1",
        idempotencyKey: "k".repeat(129),
        decisions: requests.map(() => ({ type: "approve" as const })),
      }),
    ).toThrow(TypeError);
  });
});
