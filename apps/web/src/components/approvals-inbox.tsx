"use client";

import { useEffect, useState } from "react";

import { AppHeader } from "./app-header";
import { StatusPill } from "./status-pill";
import { requiresAttention, taskIdentifierLabel } from "./task-inbox-filter";
import { taskClient } from "../lib/task-client";
import type { TaskSummary } from "../lib/task-types";

/** The storage key the task workspace reads to reopen a specific task on load. */
const SELECTED_TASK_STORAGE_KEY = "deepwork.selectedTaskId";

function messageFrom(error: unknown): string {
  return error instanceof Error ? error.message : "Something unexpected happened.";
}

/** Tasks awaiting a human decision, in the order the source returned them. */
export function selectApprovals(tasks: readonly TaskSummary[]): TaskSummary[] {
  return tasks.filter(requiresAttention);
}

export function ApprovalsInbox() {
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

  const approvals = selectApprovals(tasks);
  const countLabel = `${approvals.length} ${approvals.length === 1 ? "approval" : "approvals"} awaiting a decision`;

  function reviewInTasks(taskId: string) {
    window.sessionStorage.setItem(SELECTED_TASK_STORAGE_KEY, taskId);
  }

  return (
    <div className="app-shell">
      <AppHeader
        mode={taskClient.mode}
        apiBaseUrl={taskClient.apiBaseUrl}
        activePath="/approvals"
      />
      <main id="main-content" className="main-content">
        <header className="page-header">
          <div>
            <p className="eyebrow">Workspace · local / product</p>
            <h1>Approvals</h1>
            <p>
              Every task paused on a human decision, gathered in one place. Open a task to review
              its plan and evidence before you approve, reject, or respond.
            </p>
          </div>
        </header>

        <section className="task-list-panel" aria-labelledby="approvals-heading">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Human decisions</p>
              <h2 id="approvals-heading">Approval queue</h2>
            </div>
            <span className="task-count" aria-label={countLabel}>
              {approvals.length}
            </span>
          </div>

          <p className="inbox-scope-note">
            This queue covers only the tasks already loaded in this local session. Global or
            provider approval search is not available.
          </p>

          {error ? (
            <div className="inline-error" role="alert">
              <strong>Approvals unavailable</strong>
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
              Loading approvals…
            </div>
          ) : null}

          {!loading && !error && approvals.length === 0 ? (
            <div className="empty-list">
              <span className="empty-list-icon" aria-hidden="true">
                ✓
              </span>
              <strong>No approvals waiting</strong>
              <p>
                When a task pauses for your decision it appears here. <a href="/">Open Tasks</a> to
                delegate new work.
              </p>
            </div>
          ) : null}

          {approvals.length > 0 ? (
            <ul className="task-list">
              {approvals.map((task) => (
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
                      </span>
                    </span>
                    <StatusPill status={task.status} />
                  </a>
                </li>
              ))}
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
