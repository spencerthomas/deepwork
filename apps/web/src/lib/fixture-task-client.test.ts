import { afterEach, describe, expect, it, vi } from "vitest";

import { createFixtureTaskClient } from "./fixture-task-client";
import type { TaskEvent } from "./task-types";

afterEach(() => {
  vi.useRealTimers();
});

describe("fixture task client", () => {
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

    const updated = await client.updatePlan(created.taskId, {
      interruptId: "fixture-interrupt-1",
      expectedRevision: 1,
      steps: ["Inspect the request safely", "Verify the bounded result"],
    });
    expect(updated.plan).toMatchObject({
      revision: 2,
      steps: ["Inspect the request safely", "Verify the bounded result"],
    });
    await expect(
      client.updatePlan(created.taskId, {
        interruptId: "fixture-interrupt-1",
        expectedRevision: 1,
        steps: ["Stale edit"],
      }),
    ).rejects.toThrow("plan changed");

    await client.decide(created.taskId, {
      interruptId: "fixture-interrupt-1",
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
