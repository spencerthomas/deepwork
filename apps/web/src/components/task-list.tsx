import { StatusPill } from "./status-pill";
import type { TaskSummary } from "../lib/task-types";

interface TaskListProps {
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

export function TaskList({
  error,
  loading,
  onRetry,
  onSelect,
  selectedTaskId,
  tasks,
}: TaskListProps) {
  return (
    <nav className="task-list-panel" aria-labelledby="task-list-heading">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Task views</p>
          <h2 id="task-list-heading">Task inbox</h2>
        </div>
        <span className="task-count" aria-label={`${tasks.length} tasks`}>
          {tasks.length}
        </span>
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
        <ul className="task-list">
          {tasks.map((task) => (
            <li key={task.taskId}>
              <button
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
                    <code>
                      {task.runId
                        ? `Run ${task.runId.slice(0, 10)}`
                        : `Task ${task.taskId.slice(0, 10)}`}
                    </code>
                  </span>
                </span>
                <StatusPill status={task.status} />
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </nav>
  );
}
