import { afterEach, describe, expect, it, vi } from "vitest";

import { createFixtureTaskClient } from "./fixture-task-client";
import type { TaskEvent } from "./task-types";

afterEach(() => {
  vi.useRealTimers();
});

describe("fixture task client", () => {
  it("runs the same create, event, approval, and result interface locally", async () => {
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
    expect((await client.getTask(created.taskId)).status).toBe("waiting-approval");

    await client.decide(created.taskId, {
      interruptId: "fixture-interrupt-1",
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
