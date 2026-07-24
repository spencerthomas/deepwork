import { taskRuntimePresentation } from "@/lib/task-runtime-presentation";
import { formatTaskAge } from "@/lib/task-time";
import type { ClientMode, TaskSummary } from "@/lib/task-types";

import { countTasks, visibleTaskText } from "../task-inbox-filter";

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

export function routeCommands(mode: ClientMode): readonly CommandItem[] {
  const runtimeCopy = taskRuntimePresentation(mode);
  return [
    {
      id: "route:new",
      label: "New task",
      hint: runtimeCopy.commandNewTaskHint,
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
}

/** Fail-closed default retained for consumers that do not select a client mode. */
export const ROUTE_COMMANDS: readonly CommandItem[] = routeCommands("api");

/**
 * The Approvals command hint, folding in how many loaded tasks are waiting on a
 * decision so the count is visible the moment the palette opens (mirrors the nav
 * badge). Zero or an invalid count leaves the descriptive base hint untouched.
 */
export function approvalsCommandHint(pending: number, base: string): string {
  if (!Number.isFinite(pending) || pending <= 0) {
    return base;
  }
  return `${Math.floor(pending)} waiting for you`;
}

/** How many task matches the palette surfaces at once. */
export const TASK_RESULT_LIMIT = 6;

function matches(query: string, ...fields: readonly string[]): boolean {
  const needle = query.trim().toLowerCase();
  if (needle === "") return true;
  return fields.some((field) => field.toLowerCase().includes(needle));
}

/**
 * The command row for a loaded task — navigates to its detail page. The hint
 * carries the same visible facts a row shows: the truncated run/task identifier
 * and, when the API recorded one, the task's age (never a fabricated time).
 */
export function taskCommandItem(task: TaskSummary, now: number = Date.now()): CommandItem {
  const identifier = task.runId
    ? `Run ${task.runId.slice(0, 10)}`
    : `Task ${task.taskId.slice(0, 10)}`;
  const age = formatTaskAge(task.createdAt, now);
  return {
    id: `task:${task.taskId}`,
    label: task.title,
    hint: age === undefined ? `Open task · ${identifier}` : `Open task · ${identifier} · ${age}`,
    href: `/tasks/${task.taskId}`,
    icon: "task",
  };
}

/**
 * Merge the static route commands with matching loaded tasks. Route commands
 * always show (filtered by the query); tasks surface only once the user types,
 * matched on the same visible text the inbox row shows — title, the truncated
 * run/task identifier, and the canonical status label — and capped. The palette
 * searches the tasks already loaded in this session, never a global or provider
 * index, and never hidden fields the row does not display.
 */
export function buildCommandResults(
  query: string,
  tasks: readonly TaskSummary[],
  limit: number = TASK_RESULT_LIMIT,
  mode: ClientMode = "api",
  now: number = Date.now(),
): CommandItem[] {
  const pending = countTasks(tasks).attention;
  const routes = routeCommands(mode)
    .map((command) =>
      command.id === "route:approvals"
        ? { ...command, hint: approvalsCommandHint(pending, command.hint) }
        : command,
    )
    .filter((command) => matches(query, command.label, command.hint));
  const trimmed = query.trim();
  const taskItems =
    trimmed === ""
      ? []
      : tasks
          .filter((task) => matches(query, visibleTaskText(task)))
          .slice(0, limit)
          .map((task) => taskCommandItem(task, now));
  return [...routes, ...taskItems];
}
