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
});
