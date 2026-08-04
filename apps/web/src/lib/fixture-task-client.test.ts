import { afterEach, describe, expect, it, vi } from "vitest";

import { createFixtureTaskClient } from "./fixture-task-client";
import type { TaskEvent } from "./task-types";

afterEach(() => {
  vi.useRealTimers();
});

describe("fixture task client", () => {
  it("preserves repeated actions and applies an ordered approve/edit vector atomically", async () => {
    vi.useFakeTimers();
    const client = createFixtureTaskClient();
    const created = await client.createTask("Prepare an ordered release plan");
    const events: TaskEvent[] = [];
    client.subscribe(created.taskId, {
      onConnectionChange: () => undefined,
      onError: (message) => {
        throw new Error(message);
      },
      onEvent: (event) => events.push(event),
    });
    await Promise.resolve();
    await vi.advanceTimersByTimeAsync(940);

    const waiting = await client.getTask(created.taskId);
    const interrupt = waiting.pendingInterrupt!;
    expect(interrupt.actionRequests?.map((action) => action.name)).toEqual([
      "execute_plan_step",
      "execute_plan_step",
      "execute_plan_step",
    ]);

    const input = {
      interruptId: interrupt.interruptId,
      expectedVersion: interrupt.version!,
      idempotencyKey: "fixture-batch-key-1",
      decisions: [
        { type: "approve" as const },
        {
          type: "edit" as const,
          editedAction: {
            ...interrupt.actionRequests![1]!,
            args: { position: 2, text: "Execute the bounded hosted work" },
          },
        },
        { type: "approve" as const },
      ],
    };
    const receipt = await client.decideBatch(created.taskId, input);
    expect(receipt).toMatchObject({
      version: interrupt.version,
      decisionTypes: ["approve", "edit", "approve"],
      duplicate: false,
    });
    expect(events.at(-1)?.data).toMatchObject({
      interruptId: interrupt.interruptId,
      decisionTypes: ["approve", "edit", "approve"],
    });
    expect(events.at(-1)?.data).not.toHaveProperty("decisions");
    expect((await client.decideBatch(created.taskId, input)).duplicate).toBe(true);

    await vi.advanceTimersByTimeAsync(420);
    const completed = await client.getTask(created.taskId);
    expect(completed.status).toBe("completed");
    expect(completed.result).toContain("Execute the bounded hosted work");
  });

  it("records a rejected ordered batch as one terminal fixture outcome", async () => {
    vi.useFakeTimers();
    const client = createFixtureTaskClient();
    const created = await client.createTask("Reject an ordered release plan");
    const events: TaskEvent[] = [];
    client.subscribe(created.taskId, {
      onConnectionChange: () => undefined,
      onError: (message) => {
        throw new Error(message);
      },
      onEvent: (event) => events.push(event),
    });
    await Promise.resolve();
    await vi.advanceTimersByTimeAsync(940);
    const interrupt = (await client.getTask(created.taskId)).pendingInterrupt!;

    await client.decideBatch(created.taskId, {
      interruptId: interrupt.interruptId,
      expectedVersion: interrupt.version!,
      idempotencyKey: "fixture-reject-key-1",
      decisions: interrupt.actionRequests!.map((_, index) =>
        index === 1
          ? { type: "reject" as const, message: "Stop here" }
          : { type: "approve" as const },
      ),
    });

    expect((await client.getTask(created.taskId)).status).toBe("running");
    await vi.advanceTimersByTimeAsync(420);
    const rejected = await client.getTask(created.taskId);
    expect(rejected.status).toBe("rejected");
    expect(rejected.result).toContain("stopped after the ordered proposal was rejected");
    expect(events.filter((event) => event.name === "run.completed")).toHaveLength(1);
    expect(events.at(-1)?.data).toMatchObject({ status: "rejected" });
  });

  it("runs create, evidence, plan edit, response, approval, and result locally", async () => {
    vi.useFakeTimers();
    const client = createFixtureTaskClient();
    const created = await client.createTask("Prepare a release checklist");
    const events: TaskEvent[] = [];
    let connection = "closed";
    const close = client.subscribe(created.taskId, {
      onConnectionChange: (state) => {
        connection = state;
      },
      onError: (message) => {
        throw new Error(message);
      },
      onEvent: (event) => events.push(event),
    });

    await Promise.resolve();
    expect(connection).toBe("connected");
    expect(events.map((event) => event.name)).toEqual(["task.created"]);

    await vi.advanceTimersByTimeAsync(940);
    expect(events.at(-1)?.name).toBe("interrupt.requested");
    const waiting = await client.getTask(created.taskId);
    expect(waiting.status).toBe("waiting-approval");
    expect(waiting.proposedPlan?.revision).toBe(1);
    expect(waiting.evidence?.at(0)?.source).toBe("deterministic-local-runner");
    const initialInterruptId = waiting.pendingInterrupt?.interruptId;
    expect(initialInterruptId).toBeTruthy();

    const updated = await client.updatePlan(created.taskId, {
      interruptId: initialInterruptId!,
      expectedRevision: 1,
      steps: ["Inspect the request safely", "Verify the bounded result"],
    });
    expect(updated.plan).toMatchObject({
      revision: 2,
      steps: ["Inspect the request safely", "Verify the bounded result"],
    });
    await expect(
      client.updatePlan(created.taskId, {
        interruptId: initialInterruptId!,
        expectedRevision: 1,
        steps: ["Stale edit"],
      }),
    ).rejects.toThrow("plan changed");

    await client.decide(created.taskId, {
      interruptId: initialInterruptId!,
      decision: "respond",
      comment: "Which acceptance check is authoritative?",
    });
    expect(events.at(-1)?.data).not.toHaveProperty("comment");
    await vi.advanceTimersByTimeAsync(300);
    const revisedInterrupt = events.at(-1);
    expect(revisedInterrupt?.name).toBe("interrupt.requested");
    expect(revisedInterrupt?.data.planRevision).toBe(3);

    await client.decide(created.taskId, {
      interruptId: String(revisedInterrupt?.data.interruptId),
      decision: "approve",
      comment: "Approved after review",
    });
    const decisionEvent = events.find((event) => event.name === "decision.recorded");
    expect(decisionEvent?.data).toMatchObject({ commentProvided: true });
    expect(decisionEvent?.data).not.toHaveProperty("comment");
    expect((await client.getTask(created.taskId)).status).toBe("running");
    await vi.advanceTimersByTimeAsync(420);

    const completed = await client.getTask(created.taskId);
    expect(events.at(-1)?.name).toBe("run.completed");
    expect(completed.status).toBe("completed");
    expect(completed.result).toContain("Prepare a release checklist");
    expect((await client.listTasks()).map((task) => task.taskId)).toContain(created.taskId);
    close();
    expect(connection).toBe("closed");
  });

  it("cancels a waiting task, stays terminal, and refuses a finished task", async () => {
    vi.useFakeTimers();
    const client = createFixtureTaskClient();
    const created = await client.createTask("Prepare a plan I will stop");
    const events: TaskEvent[] = [];
    const close = client.subscribe(created.taskId, {
      onConnectionChange: () => undefined,
      onError: (message) => {
        throw new Error(message);
      },
      onEvent: (event) => events.push(event),
    });
    await Promise.resolve();

    await vi.advanceTimersByTimeAsync(940);
    expect((await client.getTask(created.taskId)).status).toBe("waiting-approval");

    const receipt = await client.cancelTask(created.taskId);
    expect(receipt).toMatchObject({ status: "cancelled", duplicate: false });
    const completion = events.at(-1);
    expect(completion?.name).toBe("run.completed");
    expect(completion?.data).toMatchObject({ status: "cancelled", resultAvailable: false });

    const cancelled = await client.getTask(created.taskId);
    expect(cancelled.status).toBe("cancelled");
    expect(cancelled.result).toBeUndefined();

    // Any still-pending scheduled step must not re-animate the cancelled task.
    await vi.advanceTimersByTimeAsync(5000);
    expect((await client.getTask(created.taskId)).status).toBe("cancelled");
    expect(events.filter((event) => event.name === "run.completed")).toHaveLength(1);

    // Cancelling again is an idempotent duplicate; deciding is refused.
    expect((await client.cancelTask(created.taskId)).duplicate).toBe(true);
    await expect(
      client.decide(created.taskId, { interruptId: "fixture-interrupt-1", decision: "approve" }),
    ).rejects.toThrow(/not waiting for a decision/);
    close();
  });

  it("refuses to cancel an already completed task", async () => {
    vi.useFakeTimers();
    const client = createFixtureTaskClient();
    const created = await client.createTask("Approve me to completion");
    const events: TaskEvent[] = [];
    client.subscribe(created.taskId, {
      onConnectionChange: () => undefined,
      onError: () => undefined,
      onEvent: (event) => events.push(event),
    });
    await Promise.resolve();
    await vi.advanceTimersByTimeAsync(940);
    const interrupt = events.find((event) => event.name === "interrupt.requested");
    await client.decide(created.taskId, {
      interruptId: String(interrupt?.data.interruptId),
      decision: "approve",
    });
    await vi.advanceTimersByTimeAsync(420);
    expect((await client.getTask(created.taskId)).status).toBe("completed");

    await expect(client.cancelTask(created.taskId)).rejects.toThrow(/can no longer be cancelled/);
    expect((await client.getTask(created.taskId)).status).toBe("completed");
  });
});
