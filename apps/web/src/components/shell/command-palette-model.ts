import type { TaskSummary } from "@/lib/task-types";

export type CommandIconKey =
  | "new-task"
  | "tasks"
  | "approvals"
  | "agents"
  | "schedules"
  | "activity"
  | "settings"
  | "task";

export interface CommandItem {
  id: string;
  label: string;
  hint: string;
  href: string;
  icon: CommandIconKey;
}

export const ROUTE_COMMANDS: readonly CommandItem[] = [
  {
    id: "route:new",
    label: "New task",
    hint: "Dispatch the local agent",
    href: "/tasks/new",
    icon: "new-task",
  },
  { id: "route:tasks", label: "Tasks", hint: "Task inbox", href: "/tasks", icon: "tasks" },
  {
    id: "route:approvals",
    label: "Approvals",
    hint: "What agents need from you",
    href: "/approvals",
    icon: "approvals",
  },
  {
    id: "route:agents",
    label: "Agents",
    hint: "Manage your fleet",
    href: "/agents",
    icon: "agents",
  },
  {
    id: "route:schedules",
    label: "Schedules",
    hint: "Recurring runs",
    href: "/schedules",
    icon: "schedules",
  },
  {
    id: "route:activity",
    label: "Activity",
    hint: "Recent runs",
    href: "/activity",
    icon: "activity",
  },
  {
    id: "route:settings",
    label: "Settings",
    hint: "Workspace settings",
    href: "/settings",
    icon: "settings",
  },
];

/** How many task matches the palette surfaces at once. */
export const TASK_RESULT_LIMIT = 6;

function matches(query: string, ...fields: readonly string[]): boolean {
  const needle = query.trim().toLowerCase();
  if (needle === "") return true;
  return fields.some((field) => field.toLowerCase().includes(needle));
}

/** The command row for a loaded task — navigates to its detail page. */
export function taskCommandItem(task: TaskSummary): CommandItem {
  const identifier = task.runId
    ? `Run ${task.runId.slice(0, 10)}`
    : `Task ${task.taskId.slice(0, 10)}`;
  return {
    id: `task:${task.taskId}`,
    label: task.title,
    hint: `Open task · ${identifier}`,
    href: `/tasks/${task.taskId}`,
    icon: "task",
  };
}

/**
 * Merge the static route commands with matching loaded tasks. Route commands
 * always show (filtered by the query); tasks surface only once the user types,
 * matched on their visible title, and capped — the palette searches the tasks
 * already loaded in this session, never a global or provider index.
 */
export function buildCommandResults(
  query: string,
  tasks: readonly TaskSummary[],
  limit: number = TASK_RESULT_LIMIT,
): CommandItem[] {
  const routes = ROUTE_COMMANDS.filter((command) => matches(query, command.label, command.hint));
  const trimmed = query.trim();
  const taskItems =
    trimmed === ""
      ? []
      : tasks
          .filter((task) => matches(query, task.title))
          .slice(0, limit)
          .map(taskCommandItem);
  return [...routes, ...taskItems];
}
