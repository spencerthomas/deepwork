import type { TaskSummary } from "@/lib/task-types";

/**
 * A count breakdown of the tasks visible in a session, used to give the agent
 * detail's "Recent tasks" panel an at-a-glance header. Only real, observed
 * tasks are counted — nothing is inferred or fabricated.
 */
export interface TaskCountSummary {
  readonly total: number;
  readonly awaitingApproval: number;
  readonly completed: number;
}

export function summarizeTasks(tasks: readonly TaskSummary[]): TaskCountSummary {
  let awaitingApproval = 0;
  let completed = 0;
  for (const task of tasks) {
    if (task.status === "waiting-approval") {
      awaitingApproval += 1;
    } else if (task.status === "completed") {
      completed += 1;
    }
  }
  return { total: tasks.length, awaitingApproval, completed };
}

/**
 * A short, honest one-line description of a task count summary, e.g.
 * "12 tasks · 2 awaiting approval · 5 completed". The total is always stated;
 * the awaiting-approval and completed clauses are omitted when zero so the line
 * never claims work that isn't there. Returns `undefined` when there is nothing
 * to describe, so the caller can render no header at all.
 */
export function describeTaskCounts(summary: TaskCountSummary): string | undefined {
  if (summary.total < 1) {
    return undefined;
  }
  const clauses = [`${summary.total} ${summary.total === 1 ? "task" : "tasks"}`];
  if (summary.awaitingApproval > 0) {
    clauses.push(`${summary.awaitingApproval} awaiting approval`);
  }
  if (summary.completed > 0) {
    clauses.push(`${summary.completed} completed`);
  }
  return clauses.join(" · ");
}
