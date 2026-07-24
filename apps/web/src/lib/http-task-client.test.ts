import { afterEach, describe, expect, it, vi } from "vitest";

import { createHttpTaskClient } from "./http-task-client";
import {
  recoverCurrentTaskAfterDecisionProblem,
  recoverCurrentTaskAfterPlanProblem,
} from "./plan-recovery";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Outcome 2 HTTP client", () => {
  it("sends the exact interrupt and revision guard when updating a plan", async () => {
    const fetchMock = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            taskId: "task-1",
            runId: "run-1",
            interruptId: "interrupt-1",
            plan: {
              revision: 3,
              title: "Updated",
              steps: ["Inspect", "Verify"],
              evidenceRefs: ["evidence-1"],
            },
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createHttpTaskClient("http://api.test");
    const result = await client.updatePlan("task-1", {
      interruptId: "interrupt-1",
      expectedRevision: 2,
      steps: ["Inspect", "Verify"],
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/api/v1/tasks/task-1/plan",
      expect.objectContaining({
        method: "PATCH",
        body: JSON.stringify({
          interruptId: "interrupt-1",
          expectedRevision: 2,
          steps: ["Inspect", "Verify"],
        }),
      }),
    );
    expect(result.plan.revision).toBe(3);
  });

  it("surfaces a stale plan conflict and does not retry or overwrite", async () => {
    const fetchMock = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            code: "plan_revision_conflict",
            message: "The proposed plan revision changed.",
          }),
          { status: 409, headers: { "content-type": "application/json" } },
        ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      createHttpTaskClient("http://api.test").updatePlan("task-1", {
        interruptId: "interrupt-1",
        expectedRevision: 1,
        steps: ["Inspect"],
      }),
    ).rejects.toThrow("The proposed plan revision changed.");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("recovers a stale edit by refetching authoritative task state, never resubmitting", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            code: "plan_revision_conflict",
            message: "The proposed plan revision changed.",
          }),
          { status: 409, headers: { "content-type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            taskId: "task-1",
            runId: "run-1",
            title: "Current task",
            status: "waiting-approval",
            proposedPlan: {
              revision: 3,
              title: "Current plan",
              steps: ["Inspect current state"],
              evidenceRefs: [],
            },
            pendingInterrupt: {
              interruptId: "interrupt-2",
              planRevision: 3,
              decisions: ["approve", "reject", "respond"],
            },
            evidence: [],
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        ),
      );
    vi.stubGlobal("fetch", fetchMock);
    const client = createHttpTaskClient("http://api.test");

    let conflict: unknown;
    try {
      await client.updatePlan("task-1", {
        interruptId: "interrupt-1",
        expectedRevision: 1,
        steps: ["Stale edit"],
      });
    } catch (error) {
      conflict = error;
    }
    const recovered = await recoverCurrentTaskAfterPlanProblem(client, "task-1", conflict);

    expect(recovered).toMatchObject({
      proposedPlan: { revision: 3 },
      pendingInterrupt: { interruptId: "interrupt-2", planRevision: 3 },
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock.mock.calls[1]?.[1]).toMatchObject({ method: "GET" });
  });

  it("fails closed when a plan receipt is not correlated to the requested revision", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              taskId: "task-1",
              runId: "run-1",
              interruptId: "interrupt-1",
              plan: {
                revision: 8,
                title: "Unexpected",
                steps: ["Inspect"],
                evidenceRefs: [],
              },
            }),
            { status: 200, headers: { "content-type": "application/json" } },
          ),
      ),
    );

    await expect(
      createHttpTaskClient("http://api.test").updatePlan("task-1", {
        interruptId: "interrupt-1",
        expectedRevision: 1,
        steps: ["Inspect"],
      }),
    ).rejects.toThrow("did not match");
  });

  it("requires a response body before calling the decision endpoint", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      createHttpTaskClient("http://api.test").decide("task-1", {
        interruptId: "interrupt-1",
        decision: "respond",
        comment: " ",
      }),
    ).rejects.toThrow("answering the agent");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("returns only a correlated typed decision receipt", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            taskId: "task-1",
            runId: "run-1",
            interruptId: "interrupt-1",
            decision: "respond",
            status: "accepted",
            duplicate: false,
          }),
          { status: 202, headers: { "content-type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            taskId: "task-other",
            runId: "run-1",
            interruptId: "interrupt-1",
            decision: "respond",
            status: "accepted",
            duplicate: false,
          }),
          { status: 202, headers: { "content-type": "application/json" } },
        ),
      );
    vi.stubGlobal("fetch", fetchMock);
    const client = createHttpTaskClient("http://api.test");
    const input = {
      interruptId: "interrupt-1",
      decision: "respond" as const,
      comment: "The requested answer",
    };

    await expect(client.decide("task-1", input)).resolves.toMatchObject({
      taskId: "task-1",
      runId: "run-1",
      decision: "respond",
    });
    await expect(client.decide("task-1", input)).rejects.toThrow("did not match");
  });

  it("recovers a stale decision from detail even when no SSE event is available", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            code: "interrupt_stale",
            message: "The interruption is no longer active.",
          }),
          { status: 409, headers: { "content-type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            taskId: "task-1",
            runId: "run-1",
            title: "Current task",
            status: "waiting-approval",
            pendingInterrupt: {
              interruptId: "interrupt-current",
              planRevision: 2,
              decisions: ["approve", "reject", "respond"],
            },
            proposedPlan: {
              revision: 2,
              title: "Current plan",
              steps: ["Inspect current state"],
              evidenceRefs: [],
            },
            evidence: [],
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        ),
      );
    vi.stubGlobal("fetch", fetchMock);
    const client = createHttpTaskClient("http://api.test");

    let stale: unknown;
    try {
      await client.decide("task-1", {
        interruptId: "interrupt-old",
        decision: "approve",
      });
    } catch (error) {
      stale = error;
    }
    const recovered = await recoverCurrentTaskAfterDecisionProblem(client, "task-1", stale);

    expect(recovered?.pendingInterrupt).toMatchObject({
      interruptId: "interrupt-current",
      planRevision: 2,
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock.mock.calls[1]?.[1]).toMatchObject({ method: "GET" });
  });

  it("posts to the cancel endpoint and normalizes the receipt", async () => {
    const fetchMock = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            taskId: "task-1",
            runId: "run-1",
            status: "cancelled",
            duplicate: false,
          }),
          { status: 202, headers: { "content-type": "application/json" } },
        ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await createHttpTaskClient("http://api.test").cancelTask("task-1");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/api/v1/tasks/task-1/cancel",
      expect.objectContaining({ method: "POST" }),
    );
    expect(result).toEqual({
      taskId: "task-1",
      runId: "run-1",
      status: "cancelled",
      duplicate: false,
    });
  });

  it("reports a 409 when a finished task can no longer be cancelled", async () => {
    const fetchMock = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            code: "task_already_resolved",
            message: "Task already finished and can no longer be cancelled.",
          }),
          { status: 409, headers: { "content-type": "application/json" } },
        ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(createHttpTaskClient("http://api.test").cancelTask("task-1")).rejects.toThrow(
      /can no longer be cancelled/,
    );
  });

  it("rejects a cancel receipt for a different task", async () => {
    const fetchMock = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            taskId: "task-2",
            runId: "run-2",
            status: "cancelled",
            duplicate: false,
          }),
          { status: 202, headers: { "content-type": "application/json" } },
        ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(createHttpTaskClient("http://api.test").cancelTask("task-1")).rejects.toThrow(
      /did not match the requested task/,
    );
  });
});
