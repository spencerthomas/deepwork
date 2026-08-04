import type { TaskSummary } from "./task-types";

export type TaskCreateFailureKind = "rejected" | "conflict" | "unknown";

export class TaskCreateFailure extends Error {
  readonly kind: TaskCreateFailureKind;
  readonly code?: string;

  constructor(kind: TaskCreateFailureKind, message: string, code?: string) {
    super(message);
    this.name = "TaskCreateFailure";
    this.kind = kind;
    this.code = code;
  }
}

export function isTaskCreateFailure(
  error: unknown,
  kind?: TaskCreateFailureKind,
): error is TaskCreateFailure {
  return error instanceof TaskCreateFailure && (kind === undefined || error.kind === kind);
}

export type TaskCreateOutcome =
  | { kind: "accepted"; task: TaskSummary; duplicate: boolean }
  | { kind: TaskCreateFailureKind; message: string; code?: string };
