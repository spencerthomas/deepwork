import type { RefObject } from "react";

import { STATUS_LABELS, StatusPill } from "./status-pill";
import type { TaskStatus, TaskSummary } from "../lib/task-types";

const STATUS_OPTIONS: ReadonlyArray<{ label: string; value: TaskStatus | "all" }> = [
  { value: "all", label: "All statuses" },
  { value: "waiting-approval", label: "Waiting approval" },
  { value: "running", label: "Running" },
  { value: "queued", label: "Queued" },
  { value: "completed", label: "Completed" },
  { value: "rejected", label: "Rejected" },
  { value: "failed", label: "Failed" },
  { value: "cancelled", label: "Cancelled" },
  { value: "unknown", label: "Unknown" },
];

export interface InboxFilters {
  attentionOnly: boolean;
  query: string;
  status: TaskStatus | "all";
}

export const INITIAL_INBOX_FILTERS: InboxFilters = {
  attentionOnly: false,
  query: "",
  status: "all",
};

export function taskNeedsAttention(task: TaskSummary): boolean {
  return task.status === "waiting-approval";
}

/** Filters only browser-loaded, user-visible task copy; it does not query a provider. */
export function filterLoadedTasks(
  tasks: readonly TaskSummary[],
  filters: InboxFilters,
): TaskSummary[] {
  const query = filters.query.trim().toLocaleLowerCase();
  return tasks.filter((task) => {
    const visibleText = [task.title, task.prompt].filter(Boolean).join(" ").toLocaleLowerCase();
    return (
      (filters.status === "all" || task.status === filters.status) &&
      (!filters.attentionOnly || taskNeedsAttention(task)) &&
      (!query || visibleText.includes(query))
    );
  });
}

interface TaskListProps {
  error?: string;
  filters: InboxFilters;
  firstTaskRef: RefObject<HTMLButtonElement | null>;
  searchRef: RefObject<HTMLInputElement | null>;
  loading: boolean;
  onFiltersChange: (filters: InboxFilters) => void;
  onRetry: () => void;
  onSelect: (taskId: string) => void;
  selectedTaskId?: string;
  tasks: readonly TaskSummary[];
  totalTaskCount: number;
}

function ArrowUpRightIcon() {
  return (
    <svg aria-hidden="true" className="task-row-arrow" fill="none" viewBox="0 0 16 16">
      <path d="M4 12 12 4M6 4h6v6" stroke="currentColor" strokeLinecap="round" strokeWidth="1.5" />
    </svg>
  );
}

export function TaskList({
  error,
  filters,
  firstTaskRef,
  loading,
  onFiltersChange,
  onRetry,
  onSelect,
  selectedTaskId,
  searchRef,
  tasks,
  totalTaskCount,
}: TaskListProps) {
  const activeFilterCount = Number(filters.query.length > 0) + Number(filters.status !== "all") + Number(filters.attentionOnly);
  const filteredEmpty = !loading && !error && totalTaskCount > 0 && tasks.length === 0;
  const noTasks = !loading && !error && totalTaskCount === 0;
  const setFilter = (update: Partial<InboxFilters>) => onFiltersChange({ ...filters, ...update });

  return (
    <section className="task-list-panel" aria-labelledby="task-list-heading">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Task views</p>
          <h2 id="task-list-heading">Task inbox</h2>
        </div>
        <span className="task-count" aria-label={`${tasks.length} of ${totalTaskCount} loaded tasks`}>
          {tasks.length}
        </span>
      </div>

      <div className="inbox-controls" aria-label="Filter loaded tasks">
        <label className="inbox-search" htmlFor="task-inbox-search">
          <span>Search loaded tasks</span>
          <input
            ref={searchRef}
            id="task-inbox-search"
            type="search"
            value={filters.query}
            maxLength={200}
            onChange={(event) => setFilter({ query: event.target.value })}
            placeholder="Search visible task text"
          />
        </label>
        <div className="inbox-filter-row">
          <label htmlFor="task-inbox-status">
            <span>Status</span>
            <select
              id="task-inbox-status"
              value={filters.status}
              onChange={(event) => setFilter({ status: event.target.value as InboxFilters["status"] })}
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="attention-filter" htmlFor="task-inbox-attention">
            <input
              id="task-inbox-attention"
              type="checkbox"
              checked={filters.attentionOnly}
              onChange={(event) => setFilter({ attentionOnly: event.target.checked })}
            />
            <span>Attention required</span>
          </label>
        </div>
        <div className="inbox-filter-summary" aria-live="polite" aria-atomic="true">
          <span>
            {tasks.length} of {totalTaskCount} loaded {totalTaskCount === 1 ? "task" : "tasks"} shown
            {activeFilterCount ? ` · ${activeFilterCount} filter${activeFilterCount === 1 ? "" : "s"} active` : ""}
          </span>
          <button
            className="text-button"
            type="button"
            disabled={activeFilterCount === 0}
            onClick={() => onFiltersChange(INITIAL_INBOX_FILTERS)}
          >
            Clear all
          </button>
        </div>
      </div>

      {error ? (
        <div className="inline-error" role="alert">
          <strong>Tasks unavailable</strong>
          <p>{error}</p>
          <button className="text-button" type="button" onClick={onRetry}>
            Try again
          </button>
        </div>
      ) : null}

      {loading && totalTaskCount === 0 ? (
        <div className="list-loading" role="status">
          <span className="button-spinner" aria-hidden="true" />
          Loading tasks…
        </div>
      ) : null}

      {filteredEmpty ? (
        <div className="empty-list" role="status">
          <strong>No loaded tasks match these filters</strong>
          <p>Change a filter or clear all to see the loaded inbox again.</p>
          <button className="text-button" type="button" onClick={() => onFiltersChange(INITIAL_INBOX_FILTERS)}>
            Clear all filters
          </button>
        </div>
      ) : null}

      {noTasks ? (
        <div className="empty-list">
          <span className="empty-list-icon" aria-hidden="true">↗</span>
          <strong>No tasks yet</strong>
          <p>Your first task will appear here as soon as you create it.</p>
        </div>
      ) : null}

      {tasks.length > 0 ? (
        <ul className="task-list" aria-label="Loaded tasks">
          {tasks.map((task, index) => {
            const attention = taskNeedsAttention(task) ? "Attention required: approval is waiting." : "No attention required.";
            return (
              <li key={task.taskId}>
                <button
                  ref={index === 0 ? firstTaskRef : undefined}
                  className="task-row"
                  type="button"
                  aria-current={selectedTaskId === task.taskId ? "page" : undefined}
                  aria-label={`${task.title}. ${STATUS_LABELS[task.status]}. ${attention}`}
                  onClick={() => onSelect(task.taskId)}
                >
                  <span className="task-row-copy">
                    <span className="task-row-title"><strong>{task.title}</strong><ArrowUpRightIcon /></span>
                    <span className="task-row-meta">
                      <span>Local agent</span><span aria-hidden="true">·</span>
                      <code>{task.runId ? `Run ${task.runId.slice(0, 10)}` : `Task ${task.taskId.slice(0, 10)}`}</code>
                    </span>
                    {taskNeedsAttention(task) ? <span className="attention-note">Attention required</span> : null}
                  </span>
                  <StatusPill status={task.status} />
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
    </section>
  );
}
