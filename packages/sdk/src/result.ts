import type {
  CapabilitySafeReason,
  CapabilityState,
  UnavailableCapabilitySummary,
} from "@deepwork/domain";

export const SDK_ERROR_CATEGORIES = Object.freeze([
  "capability-unavailable",
  "permission-denied",
  "offline",
  "cancelled",
  "contract",
  "recovery-required",
  "upstream",
  "unknown",
] as const);

export type SdkErrorCategory = (typeof SDK_ERROR_CATEGORIES)[number];

export interface SdkError {
  readonly category: SdkErrorCategory;
  readonly safeMessage: string;
  readonly retryable: boolean;
  readonly capability?: UnavailableCapabilitySummary;
  readonly code?: ApplicationProblemCode;
  readonly recovery?: "hydrate-and-reconnect" | "authoritative-refetch";
}

export type SdkResult<T> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: SdkError };

export function capabilityUnavailableError(capability: UnavailableCapabilitySummary): SdkError {
  return Object.freeze({
    category:
      capability.state === "permission-denied" ? "permission-denied" : "capability-unavailable",
    safeMessage: unavailableMessage(capability.state, capability.safeReason),
    retryable: capability.state === "unavailable" && capability.safeReason === "source-unavailable",
    capability,
  });
}

export function contractError(safeMessage: string): SdkError {
  if (safeMessage.trim().length === 0 || safeMessage.length > 300) {
    throw new TypeError("SDK contract errors require a bounded safe message.");
  }
  return Object.freeze({
    category: "contract",
    safeMessage,
    retryable: false,
  });
}

export const APPLICATION_PROBLEM_CODES = Object.freeze([
  "task_not_found",
  "task_result_unavailable",
  "event_cursor_invalid",
  "interrupt_mismatch",
  "interrupt_stale",
  "decision_conflict",
  "plan_unavailable",
  "plan_revision_conflict",
] as const);

export type ApplicationProblemCode = (typeof APPLICATION_PROBLEM_CODES)[number];

export class TaskTransportProblemError extends Error {
  readonly status: 404 | 409;
  readonly code: ApplicationProblemCode;

  constructor(status: number, code: string) {
    const accepted =
      (status === 404 && code === "task_not_found") ||
      (status === 409 &&
        [
          "task_result_unavailable",
          "event_cursor_invalid",
          "interrupt_mismatch",
          "interrupt_stale",
          "decision_conflict",
          "plan_unavailable",
          "plan_revision_conflict",
        ].includes(code));
    if (!accepted) {
      throw new TypeError("Task transport problem status/code pair is not accepted.");
    }
    super("Accepted task transport problem.");
    this.name = "TaskTransportProblemError";
    this.status = status;
    this.code = code as ApplicationProblemCode;
  }
}

export function taskTransportProblem(status: number, code: string): TaskTransportProblemError {
  return new TaskTransportProblemError(status, code);
}

const APPLICATION_PROBLEM_MESSAGES: Readonly<Record<ApplicationProblemCode, string>> =
  Object.freeze({
    task_not_found: "Task was not found.",
    task_result_unavailable: "Task does not have a completed result.",
    event_cursor_invalid: "Event replay cursor is invalid.",
    interrupt_mismatch: "Interrupt does not match the pending task decision.",
    interrupt_stale: "Interrupt is no longer actionable.",
    decision_conflict: "A different decision was already recorded.",
    plan_unavailable: "Task has no editable proposed plan.",
    plan_revision_conflict: "Plan revision is stale or conflicting.",
  });

export function applicationProblemError(problem: TaskTransportProblemError): SdkError {
  const recovery =
    problem.code === "event_cursor_invalid"
      ? "hydrate-and-reconnect"
      : problem.code === "interrupt_mismatch" ||
          problem.code === "interrupt_stale" ||
          problem.code === "decision_conflict" ||
          problem.code === "plan_revision_conflict"
        ? "authoritative-refetch"
        : undefined;
  return Object.freeze({
    category: recovery === undefined ? "upstream" : "recovery-required",
    code: problem.code,
    safeMessage: APPLICATION_PROBLEM_MESSAGES[problem.code],
    retryable: false,
    ...(recovery === undefined ? {} : { recovery }),
  });
}

function unavailableMessage(
  state: CapabilityState,
  reason: CapabilitySafeReason | undefined,
): string {
  if (state === "permission-denied" || reason === "permission-required") {
    return "This action requires additional permission.";
  }
  if (state === "unknown" || reason === "contract-not-verified") {
    return "This capability has not been verified.";
  }
  if (reason === "source-unavailable") {
    return "The source is currently unavailable.";
  }

  return "This capability is unavailable.";
}
