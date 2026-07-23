import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { TaskList } from "./task-list";
import { EMPTY_TASK_INBOX_FILTER, type TaskInboxFilter } from "./task-inbox-filter";
import type { TaskSummary } from "../lib/task-types";

const tasks: TaskSummary[] = [
  {
    taskId: "fixture-task-1",
    runId: "fixture-run-1",
    title: "Refresh the billing summary",
    status: "waiting-approval",
  },
  {
    taskId: "fixture-task-2",
    runId: "fixture-run-2",
    title: "Draft the release notes",
    status: "running",
  },
  {
    taskId: "fixture-task-3",
    runId: "fixture-run-3",
    title: "Archive stale sandboxes",
    status: "completed",
  },
];

interface RenderOptions {
  defaultFilter?: TaskInboxFilter;
  error?: string;
  loading?: boolean;
  selectedTaskId?: string;
  tasks?: readonly TaskSummary[];
}

function render(options: RenderOptions = {}): string {
  return renderToStaticMarkup(
    createElement(TaskList, {
      defaultFilter: options.defaultFilter,
      error: options.error,
      loading: options.loading ?? false,
      onRetry: () => undefined,
      onSelect: () => undefined,
      selectedTaskId: options.selectedTaskId,
      tasks: options.tasks ?? tasks,
    }),
  );
}

describe("task inbox controls", () => {
  it("names the search and filter controls and reports status counts", () => {
    const markup = render({ selectedTaskId: "fixture-task-1" });

    expect(markup).toContain('role="search"');
    expect(markup).toContain("Search loaded tasks");
    expect(markup).toContain('type="search"');
    expect(markup).toContain('name="task-search"');
    expect(markup).toContain('name="task-status"');
    expect(markup).toContain('name="task-attention"');
    expect(markup).toContain("All statuses (3)");
    expect(markup).toContain("Waiting approval (1)");
    expect(markup).toContain("Running (1)");
    expect(markup).toContain("Failed (0)");
    expect(markup).toContain("Needs attention (1)");
    expect(markup).toContain("3 loaded tasks · 1 needs attention");
  });

  it("never claims global, provider, or server-side search capabilities", () => {
    const markup = render();

    expect(markup).toContain("only the tasks already loaded in this local session");
    expect(markup).toContain(
      "Global or provider thread search and server-side pagination are not available.",
    );
  });

  it("shows every row and marks the selected task when no filter is active", () => {
    const markup = render({ selectedTaskId: "fixture-task-2" });

    expect(markup).toContain("Refresh the billing summary");
    expect(markup).toContain("Draft the release notes");
    expect(markup).toContain("Archive stale sandboxes");
    expect(markup.match(/aria-current="page"/g)).toHaveLength(1);
    expect(markup).not.toContain("Selected task hidden by filters.");
  });
});

describe("task inbox filtered states", () => {
  it("filters rows by search text and reports the visible count", () => {
    const markup = render({
      defaultFilter: { ...EMPTY_TASK_INBOX_FILTER, query: "billing" },
    });

    expect(markup).toContain("Refresh the billing summary");
    expect(markup).not.toContain("Draft the release notes");
    expect(markup).toContain("Showing 1 of 3 loaded tasks · 1 needs attention");
  });

  it("explains a filtered-empty result and offers one clear action", () => {
    const markup = render({
      defaultFilter: { ...EMPTY_TASK_INBOX_FILTER, query: "no-such-task" },
    });

    expect(markup).toContain("No matching tasks");
    expect(markup).toContain("No loaded tasks match “no-such-task”.");
    expect(markup).toContain("Clear filters");
    expect(markup).toContain("Showing 0 of 3 loaded tasks");
    expect(markup).not.toContain("task-row-title");
  });

  it("keeps the hidden selected task disclosed instead of dropping it", () => {
    const markup = render({
      defaultFilter: { ...EMPTY_TASK_INBOX_FILTER, status: "running" },
      selectedTaskId: "fixture-task-1",
    });

    expect(markup).toContain("Selected task hidden by filters.");
    expect(markup).toContain("stays open in the task detail panel.");
    expect(markup).toContain("Clear filters and show it");
    expect(markup).toContain("Draft the release notes");
    expect(markup).not.toContain('aria-current="page"');
  });

  it("mentions the hidden selection inside the filtered-empty state", () => {
    const markup = render({
      defaultFilter: { ...EMPTY_TASK_INBOX_FILTER, status: "failed" },
      selectedTaskId: "fixture-task-1",
    });

    expect(markup).toContain("No loaded tasks have the Failed status.");
    expect(markup).toContain("The selected task stays open in the task detail panel.");
  });
});

describe("task inbox loading, error, and empty states", () => {
  it("shows the loading state and disables the controls before tasks arrive", () => {
    const markup = render({ loading: true, tasks: [] });

    expect(markup).toContain("Loading tasks…");
    expect(markup).toContain("disabled");
    expect(markup).not.toContain("No tasks yet");
    expect(markup).not.toContain("loaded tasks ·");
  });

  it("teaches the empty workspace state when no tasks exist", () => {
    const markup = render({ tasks: [] });

    expect(markup).toContain("No tasks yet");
    expect(markup).toContain("Your first task will appear here as soon as you create it.");
    expect(markup).not.toContain("No matching tasks");
  });

  it("keeps loaded tasks filterable while showing an API error", () => {
    const markup = render({ error: "The task service refused the request." });

    expect(markup).toContain('role="alert"');
    expect(markup).toContain("Tasks unavailable");
    expect(markup).toContain("The task service refused the request.");
    expect(markup).toContain("Try again");
    expect(markup).toContain("Refresh the billing summary");
    expect(markup).not.toContain('disabled=""');
  });
});
