import { describe, expect, it } from "vitest";

import type { TaskEventName } from "../../lib/task-types";
import { activityEntryHref } from "./activity-links";
import type { ActivityEntry } from "./activity-model";

function eventEntry(eventName: TaskEventName): ActivityEntry {
  return {
    kind: "event",
    eventName,
    eventId: "1",
    key: `event:task_1:1`,
    taskId: "task_1",
    taskTitle: "A task",
  };
}

describe("activityEntryHref", () => {
  it("links a status entry to the task with no panel override", () => {
    const entry: ActivityEntry = {
      kind: "status",
      status: "running",
      key: "status:task_1",
      taskId: "task_1",
      taskTitle: "A task",
    };
    expect(activityEntryHref(entry)).toBe("/tasks/task_1");
  });

  it("deep-links an evidence event to the Evidence tab", () => {
    expect(activityEntryHref(eventEntry("evidence.recorded"))).toBe("/tasks/task_1?panel=evidence");
  });

  it("deep-links a plan event to the Status tab, where the plan renders", () => {
    // Status is the run panel's default tab, so no ?panel= is needed.
    expect(activityEntryHref(eventEntry("plan.proposed"))).toBe("/tasks/task_1");
    expect(activityEntryHref(eventEntry("plan.updated"))).toBe("/tasks/task_1");
  });

  it("deep-links other events to the Stream tab", () => {
    expect(activityEntryHref(eventEntry("decision.recorded"))).toBe("/tasks/task_1?panel=stream");
    expect(activityEntryHref(eventEntry("content.delta"))).toBe("/tasks/task_1?panel=stream");
    expect(activityEntryHref(eventEntry("run.completed"))).toBe("/tasks/task_1?panel=stream");
  });
});
