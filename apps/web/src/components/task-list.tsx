"use client";

import { useId, useRef, useState, type KeyboardEvent } from "react";

import { StatusPill } from "./status-pill";
import {
  EMPTY_TASK_INBOX_FILTER,
  TASK_SEARCH_MAX_LENGTH,
  TASK_STATUS_FILTER_OPTIONS,
  TASK_STATUS_LABELS,
  countTasks,
  describeTaskFilter,
  filterTasks,
  hasActiveTaskFilter,
  normalizeTaskQuery,
  taskIdentifierLabel,
  type TaskInboxFilter,
} from "./task-inbox-filter";
import type { TaskSummary } from "../lib/task-types";

interface TaskListProps {
  /** Initial filter state; used by presets and component tests. */
  defaultFilter?: TaskInboxFilter;
  error?: string;
  loading: boolean;
  onRetry: () => void;
  onSelect: (taskId: string) => void;
  selectedTaskId?: string;
  tasks: readonly TaskSummary[];
}

function ArrowUpRightIcon() {
  return (
    <svg aria-hidden="true" className="task-row-arrow" fill="none" viewBox="0 0 16 16">
      <path d="M4 12 12 4M6 4h6v6" stroke="currentColor" strokeLinecap="round" strokeWidth="1.5" />
    </svg>
  );
}

function truncateTitle(title: string): string {
  return title.length > 64 ? `${title.slice(0, 63)}…` : title;
}

export function TaskList({
  defaultFilter,
  error,
  loading,
  onRetry,
  onSelect,
  selectedTaskId,
  tasks,
}: TaskListProps) {
  const [filter, setFilter] = useState<TaskInboxFilter>(defaultFilter ?? EMPTY_TASK_INBOX_FILTER);
  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const rowRefs = useRef(new Map<string, HTMLButtonElement>());
  const baseId = useId();
  const searchId = `${baseId}-search`;
  const statusId = `${baseId}-status`;
  const attentionId = `${baseId}-attention`;
  const scopeNoteId = `${baseId}-scope`;

  const counts = countTasks(tasks);
  const visibleTasks = filterTasks(tasks, filter);
  const filterActive = hasActiveTaskFilter(filter);
  const controlsDisabled = tasks.length === 0;
  const selectedTask = selectedTaskId
    ? tasks.find((task) => task.taskId === selectedTaskId)
    : undefined;
  const hiddenSelectedTask =
    filterActive &&
    selectedTask !== undefined &&
    !visibleTasks.some((task) => task.taskId === selectedTask.taskId)
      ? selectedTask
      : undefined;

  const totalLabel = `${counts.total} loaded ${counts.total === 1 ? "task" : "tasks"}`;
  const attentionLabel = `${counts.attention} ${counts.attention === 1 ? "needs" : "need"} attention`;
  const countBadgeLabel = filterActive
    ? `Showing ${visibleTasks.length} of ${counts.total} loaded tasks`
    : `${counts.total} loaded tasks`;

  function clearFilters(focusTarget: "search" | "selected-row") {
    setFilter(EMPTY_TASK_INBOX_FILTER);
    window.requestAnimationFrame(() => {
      const selectedRow = selectedTaskId ? rowRefs.current.get(selectedTaskId) : undefined;
      if (focusTarget === "selected-row" && selectedRow) {
        selectedRow.focus();
      } else {
        searchInputRef.current?.focus();
      }
    });
  }

  function clearQueryOnEscape(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Escape" && filter.query !== "") {
      event.preventDefault();
      setFilter((current) => ({ ...current, query: "" }));
    }
  }

  return (
    <section className="task-list-panel" aria-labelledby="task-list-heading">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Task views</p>
          <h2 id="task-list-heading">Task inbox</h2>
        </div>
        <span className="task-count" aria-label={countBadgeLabel}>
          {filterActive ? `${visibleTasks.length}/${counts.total}` : counts.total}
        </span>
      </div>

      <form
        className="inbox-controls"
        role="search"
        aria-label="Search and filter loaded tasks"
        onSubmit={(event) => event.preventDefault()}
      >
        <div className="inbox-search-field">
          <label htmlFor={searchId}>Search loaded tasks</label>
          <input
            ref={searchInputRef}
            id={searchId}
            name="task-search"
            type="search"
            autoComplete="off"
            maxLength={TASK_SEARCH_MAX_LENGTH}
            placeholder="Title, visible run ID, or status"
            value={filter.query}
            disabled={controlsDisabled}
            aria-describedby={scopeNoteId}
            onChange={(event) => {
              const query = normalizeTaskQuery(event.target.value);
              setFilter((current) => ({ ...current, query }));
            }}
            onKeyDown={clearQueryOnEscape}
          />
        </div>
        <div className="inbox-filter-row">
          <div className="inbox-status-field">
            <label htmlFor={statusId}>Status</label>
            <select
              id={statusId}
              name="task-status"
              value={filter.status}
              disabled={controlsDisabled}
              onChange={(event) => {
                const status = event.target.value as TaskInboxFilter["status"];
                setFilter((current) => ({ ...current, status }));
              }}
            >
              <option value="all">All statuses ({counts.total})</option>
              {TASK_STATUS_FILTER_OPTIONS.map((status) => (
                <option key={status} value={status}>
                  {TASK_STATUS_LABELS[status]} ({counts.byStatus[status]})
                </option>
              ))}
            </select>
          </div>
          <div className="inbox-attention-field">
            <input
              id={attentionId}
              name="task-attention"
              type="checkbox"
              checked={filter.attentionOnly}
              disabled={controlsDisabled}
              onChange={(event) => {
                const attentionOnly = event.target.checked;
                setFilter((current) => ({ ...current, attentionOnly }));
              }}
            />
            <label htmlFor={attentionId}>Needs attention ({counts.attention})</label>
          </div>
          {filterActive ? (
            <button
              className="text-button inbox-clear"
              type="button"
              onClick={() => clearFilters("search")}
            >
              Clear filters
            </button>
          ) : null}
        </div>
        <p className="inbox-scope-note" id={scopeNoteId}>
          Search and filters cover only the tasks already loaded in this local session. Global or
          provider thread search and server-side pagination are not available.
        </p>
      </form>

      {error ? (
        <div className="inline-error" role="alert">
          <strong>Tasks unavailable</strong>
          <p>{error}</p>
          <button className="text-button" type="button" onClick={onRetry}>
            Try again
          </button>
        </div>
      ) : null}

      {loading && tasks.length === 0 ? (
        <div className="list-loading" role="status">
          <span className="button-spinner" aria-hidden="true" />
          Loading tasks…
        </div>
      ) : null}

      {!loading && !error && tasks.length === 0 ? (
        <div className="empty-list">
          <span className="empty-list-icon" aria-hidden="true">
            ↗
          </span>
          <strong>No tasks yet</strong>
          <p>Your first task will appear here as soon as you create it.</p>
        </div>
      ) : null}

      {tasks.length > 0 ? (
        <p className="inbox-results-line" role="status">
          {filterActive
            ? `Showing ${visibleTasks.length} of ${totalLabel} · ${attentionLabel}`
            : `${totalLabel} · ${attentionLabel}`}
        </p>
      ) : null}

      {hiddenSelectedTask && visibleTasks.length > 0 ? (
        <div className="hidden-selection-notice" role="status">
          <p>
            <strong>Selected task hidden by filters.</strong> “
            {truncateTitle(hiddenSelectedTask.title)}” stays open in the task detail panel.
          </p>
          <button
            className="text-button"
            type="button"
            onClick={() => clearFilters("selected-row")}
          >
            Clear filters and show it
          </button>
        </div>
      ) : null}

      {tasks.length > 0 && visibleTasks.length === 0 ? (
        <div className="empty-list filtered-empty">
          <strong>No matching tasks</strong>
          <p>
            {describeTaskFilter(filter)}
            {hiddenSelectedTask ? " The selected task stays open in the task detail panel." : ""}
          </p>
          <button
            className="secondary-button"
            type="button"
            onClick={() => clearFilters(hiddenSelectedTask ? "selected-row" : "search")}
          >
            Clear filters
          </button>
        </div>
      ) : null}

      {visibleTasks.length > 0 ? (
        <ul className="task-list">
          {visibleTasks.map((task) => (
            <li key={task.taskId}>
              <button
                ref={(node) => {
                  if (node) {
                    rowRefs.current.set(task.taskId, node);
                  } else {
                    rowRefs.current.delete(task.taskId);
                  }
                }}
                className="task-row"
                type="button"
                aria-current={selectedTaskId === task.taskId ? "page" : undefined}
                onClick={() => onSelect(task.taskId)}
              >
                <span className="task-row-copy">
                  <span className="task-row-title">
                    <strong>{task.title}</strong>
                    <ArrowUpRightIcon />
                  </span>
                  <span className="task-row-meta">
                    <span>Local agent</span>
                    <span aria-hidden="true">·</span>
                    <code>{taskIdentifierLabel(task)}</code>
                  </span>
                </span>
                <StatusPill status={task.status} />
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
