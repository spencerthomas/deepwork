import { TASK_STATUS_LABELS } from "./task-inbox-filter";
import type { TaskStatus } from "../lib/task-types";

export function StatusPill({ status }: { status: TaskStatus }) {
  return (
    <span className={`status-pill status-${status}`}>
      <span className="status-dot" aria-hidden="true" />
      {TASK_STATUS_LABELS[status]}
    </span>
  );
}
