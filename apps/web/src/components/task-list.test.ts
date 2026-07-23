import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { filterLoadedTasks, INITIAL_INBOX_FILTERS, TaskList } from "./task-list";
import type { TaskSummary } from "../lib/task-types";

const tasks: TaskSummary[] = [
  { taskId: "approval", title: "Review deployment plan", prompt: "Approve the safe rollout", status: "waiting-approval" },
  { taskId: "running", title: "Inspect repository", status: "running" },
  { taskId: "done", title: "Write release notes", status: "completed" },
];

describe("task inbox filters", () => {
  it("searches only loaded, visible task text and combines canonical status and attention filters", () => {
    expect(filterLoadedTasks(tasks, { ...INITIAL_INBOX_FILTERS, query: "safe rollout" }).map((task) => task.taskId)).toEqual(["approval"]);
    expect(filterLoadedTasks(tasks, { ...INITIAL_INBOX_FILTERS, status: "running" }).map((task) => task.taskId)).toEqual(["running"]);
    expect(filterLoadedTasks(tasks, { ...INITIAL_INBOX_FILTERS, attentionOnly: true }).map((task) => task.taskId)).toEqual(["approval"]);
  });

  it("names controls and describes loaded result counts without claiming provider search", () => {
    const markup = renderToStaticMarkup(createElement(TaskList, {
      tasks,
      totalTaskCount: tasks.length,
      filters: INITIAL_INBOX_FILTERS,
      loading: false,
      firstTaskRef: { current: null },
      searchRef: { current: null },
      onFiltersChange: () => undefined,
      onRetry: () => undefined,
      onSelect: () => undefined,
    }));
    expect(markup).toContain('for="task-inbox-search"');
    expect(markup).toContain("Search loaded tasks");
    expect(markup).toContain("Attention required");
    expect(markup).toContain("3 of 3 loaded tasks shown");
    expect(markup).not.toContain("provider search");
  });
});
