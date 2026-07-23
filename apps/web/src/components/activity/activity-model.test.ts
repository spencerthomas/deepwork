import { describe, expect, it } from "vitest";

import type { TaskEvent, TaskStatus, TaskSummary } from "../../lib/task-types";
import {
  activityFilterCounts,
  buildActivityFeed,
  eventDetailText,
  filterActivityFeed,
} from "./activity-model";

function task(taskId: string, status: TaskStatus, title = `Task ${taskId}`): TaskSummary {
  return { taskId, title, status };
}

function event(id: string, name: TaskEvent["name"], data: Record<string, unknown> = {}): TaskEvent {
  return { id, name, data };
}

describe("buildActivityFeed", () => {
  it("orders tasks newest first by numeric id with status before that task's events", () => {
    const tasks = [task("task_00000001", "completed"), task("task_00000003", "waiting-approval")];
    const eventsByTask = {
      task_00000001: [
        event("task_00000001:2", "run.started"),
        event("task_00000001:1", "task.created"),
      ],
    };

    const keys = buildActivityFeed(tasks, eventsByTask).map((entry) => entry.key);
    expect(keys).toEqual([
      "status:task_00000003",
      "status:task_00000001",
      "event:task_00000001:task_00000001:1",
      "event:task_00000001:task_00000001:2",
    ]);
  });

  it("keeps events for tasks missing from the list, using the task id as the title", () => {
    const feed = buildActivityFeed([], {
      task_00000009: [event("task_00000009:1", "run.started")],
    });
    expect(feed).toHaveLength(1);
    expect(feed[0]?.kind).toBe("event");
    expect(feed[0]?.taskTitle).toBe("task_00000009");
  });

  it("omits status entries for unknown tasks and event groups that are empty", () => {
    const feed = buildActivityFeed([task("task_00000002", "running")], {
      task_00000002: [],
    });
    expect(feed.map((entry) => entry.key)).toEqual(["status:task_00000002"]);
  });

  it("retains arrival order when event ids carry no trailing number", () => {
    const feed = buildActivityFeed([], {
      task_00000001: [event("first-a", "task.created"), event("second-b", "run.started")],
    });
    expect(feed.map((entry) => (entry.kind === "event" ? entry.eventId : ""))).toEqual([
      "first-a",
      "second-b",
    ]);
  });
});

describe("eventDetailText", () => {
  it("reports the recorded decision verb", () => {
    expect(eventDetailText(event("1", "decision.recorded", { decision: "approve" }))).toBe(
      "Decision: approve",
    );
  });

  it("summarizes plan events from their real revision and title", () => {
    expect(
      eventDetailText(event("1", "plan.proposed", { revision: 2, title: "Research plan" })),
    ).toBe("Revision 2 — Research plan");
  });

  it("uses the interrupt's own question", () => {
    expect(
      eventDetailText(event("1", "interrupt.requested", { question: "Approve this plan?" })),
    ).toBe("Approve this plan?");
  });

  it("falls back to streamed text and truncates long payloads", () => {
    expect(eventDetailText(event("1", "content.delta", { delta: "partial output" }))).toBe(
      "partial output",
    );
    const long = "x".repeat(500);
    const detail = eventDetailText(event("1", "content.delta", { delta: long }));
    expect(detail?.endsWith("…")).toBe(true);
    expect([...(detail ?? "")].length).toBe(160);
  });

  it("returns undefined instead of inventing a summary", () => {
    expect(eventDetailText(event("1", "run.started", {}))).toBeUndefined();
  });
});

describe("filterActivityFeed", () => {
  const feed = buildActivityFeed([task("task_00000001", "running")], {
    task_00000001: [
      event("task_00000001:1", "task.created"),
      event("task_00000001:2", "plan.proposed", { revision: 1, title: "Plan" }),
      event("task_00000001:3", "plan.updated", { revision: 2, title: "Plan" }),
      event("task_00000001:4", "evidence.recorded"),
      event("task_00000001:5", "interrupt.requested"),
      event("task_00000001:6", "decision.recorded", { decision: "approve" }),
      event("task_00000001:7", "run.completed"),
    ],
  });

  it("keeps everything, including status entries, under all", () => {
    expect(filterActivityFeed(feed, "all")).toHaveLength(8);
  });

  it("keeps only the named event group and drops status entries", () => {
    expect(
      filterActivityFeed(feed, "plans").map((entry) =>
        entry.kind === "event" ? entry.eventName : entry.kind,
      ),
    ).toEqual(["plan.proposed", "plan.updated"]);
    expect(
      filterActivityFeed(feed, "decisions").map((entry) =>
        entry.kind === "event" ? entry.eventName : entry.kind,
      ),
    ).toEqual(["interrupt.requested", "decision.recorded"]);
    expect(filterActivityFeed(feed, "evidence")).toHaveLength(1);
    expect(filterActivityFeed(feed, "completions")).toHaveLength(1);
  });

  it("counts every filter for the sidebar", () => {
    expect(activityFilterCounts(feed)).toEqual({
      all: 8,
      plans: 2,
      evidence: 1,
      decisions: 2,
      completions: 1,
    });
  });
});
