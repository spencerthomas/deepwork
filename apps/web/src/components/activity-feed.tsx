"use client";

import { useEffect, useState } from "react";

import { AppHeader } from "./app-header";
import { StatusPill } from "./status-pill";
import { taskIdentifierLabel } from "./task-inbox-filter";
import { taskClient } from "../lib/task-client";
import type { TaskSummary } from "../lib/task-types";

/** The storage key the task workspace reads to reopen a specific task on load. */
const SELECTED_TASK_STORAGE_KEY = "deepwork.selectedTaskId";

function messageFrom(error: unknown): string {
  return error instanceof Error ? error.message : "Something unexpected happened.";
}

/** The most recent timestamp a task carries, if any. */
export function activityTimestamp(task: TaskSummary): string | undefined {
  return task.updatedAt ?? task.createdAt;
}

/**
 * Loaded tasks ordered newest activity first. ISO 8601 strings sort
 * lexicographically, so undated tasks fall to the end in their original order.
 */
export function sortByRecency(tasks: readonly TaskSummary[]): TaskSummary[] {
  return [...tasks].sort((a, b) => {
    const aKey = activityTimestamp(a);
    const bKey = activityTimestamp(b);
    if (aKey && bKey) {
      return aKey < bKey ? 1 : aKey > bKey ? -1 : 0;
    }
    if (aKey) {
      return -1;
    }
    if (bKey) {
      return 1;
    }
    return 0;
  });
}

/** A human-readable label for a task's latest activity time. */
export function describeActivityTime(iso: string | undefined): string {
  if (!iso) {
    return "Time unavailable";
  }
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return "Time unavailable";
  }
  return date.toLocaleString();
}

export function ActivityFeed() {
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(undefined);

    void taskClient
      .listTasks(controller.signal)
      .then((items) => {
        if (!controller.signal.aborted) {
          setTasks(items);
        }
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setError(messageFrom(cause));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });

    return () => controller.abort();
  }, [attempt]);

  const entries = sortByRecency(tasks);
  const countLabel = `${entries.length} ${entries.length === 1 ? "task" : "tasks"} in this session`;

  function reviewInTasks(taskId: string) {
    window.sessionStorage.setItem(SELECTED_TASK_STORAGE_KEY, taskId);
  }

  return (
    <div className="app-shell">
      <AppHeader mode={taskClient.mode} apiBaseUrl={taskClient.apiBaseUrl} activePath="/activity" />
      <main id="main-content" className="main-content">
        <header className="page-header">
          <div>
            <p className="eyebrow">Workspace · local / product</p>
            <h1>Activity</h1>
            <p>
              A running record of the tasks in this session, newest activity first. Open any entry
              to return to its full timeline and evidence.
            </p>
          </div>
        </header>

        <section className="task-list-panel" aria-labelledby="activity-heading">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Session record</p>
              <h2 id="activity-heading">Recent activity</h2>
            </div>
            <span className="task-count" aria-label={countLabel}>
              {entries.length}
            </span>
          </div>

          <p className="inbox-scope-note">
            This feed covers only the tasks already loaded in this local session. It is not a
            durable provider audit log, and global or cross-session history is not available.
          </p>

          {error ? (
            <div className="inline-error" role="alert">
              <strong>Activity unavailable</strong>
              <p>{error}</p>
              <button
                className="text-button"
                type="button"
                onClick={() => setAttempt((current) => current + 1)}
              >
                Try again
              </button>
            </div>
          ) : null}

          {loading && tasks.length === 0 ? (
            <div className="list-loading" role="status">
              <span className="button-spinner" aria-hidden="true" />
              Loading activity…
            </div>
          ) : null}

          {!loading && !error && entries.length === 0 ? (
            <div className="empty-list">
              <span className="empty-list-icon" aria-hidden="true">
                ↗
              </span>
              <strong>No activity yet</strong>
              <p>
                Task activity appears here as soon as you create work. <a href="/">Open Tasks</a> to
                get started.
              </p>
            </div>
          ) : null}

          {entries.length > 0 ? (
            <ul className="task-list">
              {entries.map((task) => {
                const iso = activityTimestamp(task);
                return (
                  <li key={task.taskId}>
                    <a className="task-row" href="/" onClick={() => reviewInTasks(task.taskId)}>
                      <span className="task-row-copy">
                        <span className="task-row-title">
                          <strong>{task.title}</strong>
                        </span>
                        <span className="task-row-meta">
                          <span>Local agent</span>
                          <span aria-hidden="true">·</span>
                          <code>{taskIdentifierLabel(task)}</code>
                          <span aria-hidden="true">·</span>
                          {iso ? (
                            <time dateTime={iso}>{describeActivityTime(iso)}</time>
                          ) : (
                            <span>{describeActivityTime(iso)}</span>
                          )}
                        </span>
                      </span>
                      <StatusPill status={task.status} />
                    </a>
                  </li>
                );
              })}
            </ul>
          ) : null}
        </section>
      </main>
      <footer className="app-footer">
        <span>deepwork</span>
        <span>Human-supervised local task execution · external providers unavailable</span>
      </footer>
    </div>
  );
}
