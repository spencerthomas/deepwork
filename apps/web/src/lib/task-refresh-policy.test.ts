import { describe, expect, it } from "vitest";

import {
  AUTHORITATIVE_SILENCE_THRESHOLD_MS,
  sameTaskDetailProjection,
  shouldRefreshAuthoritativeTask,
} from "./task-refresh-policy";
import type { TaskDetail } from "./task-types";

const runningTask: TaskDetail = {
  taskId: "task-1",
  title: "Task",
  status: "running",
  lastEventId: 2,
  updatedAt: "2026-08-03T00:00:00Z",
};

describe("authoritative task refresh policy", () => {
  it("refreshes a running task only after the stream stays silent", () => {
    expect(
      shouldRefreshAuthoritativeTask(runningTask, {
        inFlight: false,
        silentForMs: AUTHORITATIVE_SILENCE_THRESHOLD_MS - 1,
      }),
    ).toBe(false);
    expect(
      shouldRefreshAuthoritativeTask(runningTask, {
        inFlight: false,
        silentForMs: AUTHORITATIVE_SILENCE_THRESHOLD_MS,
      }),
    ).toBe(true);
  });

  it("does not poll a task paused for approval or a terminal task", () => {
    for (const status of ["waiting-approval", "completed", "rejected"] as const) {
      expect(
        shouldRefreshAuthoritativeTask(
          { ...runningTask, status },
          { inFlight: false, silentForMs: AUTHORITATIVE_SILENCE_THRESHOLD_MS },
        ),
      ).toBe(false);
    }
  });

  it("recognizes an equivalent projection without replacing it", () => {
    expect(sameTaskDetailProjection(runningTask, { ...runningTask })).toBe(true);
    expect(sameTaskDetailProjection(runningTask, { ...runningTask, lastEventId: 3 })).toBe(false);
  });
});
