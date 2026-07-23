import type {
  ActiveInterrupt,
  CreateTaskResult,
  TaskDetail,
  TaskEvent,
  TaskStatus,
  TaskSummary,
} from "./task-types";
import { DECISION_COMMENT_MAX_LENGTH, PROMPT_MAX_LENGTH } from "./task-types";

export class ContractError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ContractError";
  }
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function validatePrompt(prompt: string): string {
  const normalized = prompt.trim();
  if (normalized === "") {
    throw new ContractError("Task prompt cannot be empty.");
  }
  if (unicodeLength(normalized) > PROMPT_MAX_LENGTH) {
    throw new ContractError(
      `Task prompt cannot exceed ${PROMPT_MAX_LENGTH.toLocaleString("en-US")} characters.`,
    );
  }
  return normalized;
}

export function unicodeLength(value: string): number {
  return [...value].length;
}

export function validateDecisionComment(comment: string | undefined): string | undefined {
  const normalized = comment?.trim();
  if (!normalized) {
    return undefined;
  }
  if (unicodeLength(normalized) > DECISION_COMMENT_MAX_LENGTH) {
    throw new ContractError(
      `Decision note cannot exceed ${DECISION_COMMENT_MAX_LENGTH.toLocaleString("en-US")} characters.`,
    );
  }
  return normalized;
}

function requiredString(record: Record<string, unknown>, key: string, context: string): string {
  const value = record[key];
  if (typeof value !== "string" || value.trim() === "") {
    throw new ContractError(`${context} is missing a valid ${key}.`);
  }
  return value;
}

function optionalString(record: Record<string, unknown>, key: string): string | undefined {
  const value = record[key];
  return typeof value === "string" && value.trim() !== "" ? value : undefined;
}

export function normalizeTaskStatus(value: unknown): TaskStatus {
  if (typeof value !== "string") {
    return "unknown";
  }

  switch (value.toLowerCase().replaceAll("_", "-")) {
    case "queued":
      return "queued";
    case "active":
    case "in-progress":
    case "running":
      return "running";
    case "awaiting-approval":
    case "blocked":
    case "interrupted":
    case "needs-review":
    case "waiting-approval":
      return "waiting-approval";
    case "complete":
    case "completed":
    case "succeeded":
      return "completed";
    case "declined":
    case "rejected":
      return "rejected";
    case "error":
    case "failed":
      return "failed";
    case "canceled":
    case "cancelled":
      return "cancelled";
    default:
      return "unknown";
  }
}

export function normalizeTaskSummary(value: unknown, context = "Task"): TaskSummary {
  if (!isRecord(value)) {
    throw new ContractError(`${context} must be an object.`);
  }

  const taskId = requiredString(value, "taskId", context);
  const prompt = optionalString(value, "prompt");
  const explicitTitle = optionalString(value, "title");
  const fallbackTitle = prompt ?? `Task ${taskId.slice(0, 8)}`;

  return {
    taskId,
    runId: optionalString(value, "runId"),
    title: explicitTitle ?? fallbackTitle,
    prompt,
    status: normalizeTaskStatus(value.status),
    createdAt: optionalString(value, "createdAt"),
    updatedAt: optionalString(value, "updatedAt"),
  };
}

export function normalizeTaskDetail(value: unknown): TaskDetail {
  if (!isRecord(value)) {
    throw new ContractError("Task detail must be an object.");
  }

  return {
    ...normalizeTaskSummary(value, "Task detail"),
    result:
      getResultText(value.result) ?? getResultText(value.output) ?? getResultText(value.summary),
  };
}

export function normalizeTaskList(value: unknown): TaskSummary[] {
  if (!isRecord(value) || !Array.isArray(value.items)) {
    throw new ContractError("Task list response must contain an items array.");
  }

  return value.items.map((item, index) =>
    normalizeTaskSummary(item, `Task list item ${index + 1}`),
  );
}

export function normalizeCreateTaskResult(value: unknown): CreateTaskResult {
  if (!isRecord(value)) {
    throw new ContractError("Create-task response must be an object.");
  }

  const status = requiredString(value, "status", "Create-task response");
  if (status !== "queued") {
    throw new ContractError(`Create-task response status must be queued, received ${status}.`);
  }

  return {
    taskId: requiredString(value, "taskId", "Create-task response"),
    runId: requiredString(value, "runId", "Create-task response"),
    status,
  };
}

export function getEventText(event: TaskEvent): string | undefined {
  for (const key of ["delta", "text", "content", "summary", "message", "result", "output"]) {
    const text = getResultText(event.data[key]);
    if (text) {
      return text;
    }
  }
  return undefined;
}

export function getCompletionResultText(event: TaskEvent): string | undefined {
  if (event.name !== "run.completed") {
    return undefined;
  }
  for (const key of ["result", "output", "summary", "content", "text"]) {
    const text = getResultText(event.data[key]);
    if (text) {
      return text;
    }
  }
  return undefined;
}

export function terminalEventNeedsDetail(event: TaskEvent): boolean {
  return event.name === "run.completed" && !getCompletionResultText(event);
}

export function getResultText(value: unknown): string | undefined {
  if (typeof value === "string" && value.trim() !== "") {
    return value;
  }
  if (Array.isArray(value)) {
    const lines = value
      .map((item) => getResultText(item))
      .filter((item): item is string => item !== undefined);
    return lines.length > 0 ? lines.join("\n") : undefined;
  }
  if (isRecord(value)) {
    for (const key of ["summary", "output", "text", "content", "message"]) {
      const text = getResultText(value[key]);
      if (text) {
        return text;
      }
    }
  }
  return undefined;
}

export function getActiveInterrupt(events: readonly TaskEvent[]): ActiveInterrupt | undefined {
  let active: ActiveInterrupt | undefined;

  for (const event of events) {
    if (event.name === "interrupt.requested") {
      const interruptId = event.data.interruptId;
      if (typeof interruptId !== "string" || interruptId.trim() === "") {
        continue;
      }
      active = {
        interruptId,
        title: typeof event.data.title === "string" ? event.data.title : "Approval required",
        question:
          typeof event.data.question === "string"
            ? event.data.question
            : typeof event.data.prompt === "string"
              ? event.data.prompt
              : typeof event.data.message === "string"
                ? event.data.message
                : "Review the proposed plan before this run continues.",
      };
      continue;
    }

    if (
      event.name === "decision.recorded" &&
      active &&
      event.data.interruptId === active.interruptId &&
      (event.data.decision === "approve" || event.data.decision === "reject")
    ) {
      active = undefined;
    }

    if (
      event.name === "run.completed" &&
      isTerminalStatus(normalizeTaskStatus(event.data.status))
    ) {
      active = undefined;
    }
  }

  return active;
}

export function statusAfterEvent(current: TaskStatus, event: TaskEvent): TaskStatus {
  switch (event.name) {
    case "task.created":
      return "queued";
    case "run.started":
    case "content.delta":
    case "plan.proposed":
      return "running";
    case "interrupt.requested":
      return "waiting-approval";
    case "decision.recorded":
      return (event.data.decision === "approve" || event.data.decision === "reject") &&
        typeof event.data.interruptId === "string"
        ? "running"
        : current;
    case "run.completed": {
      const normalized = normalizeTaskStatus(event.data.status);
      return isTerminalStatus(normalized) ? normalized : "unknown";
    }
    default:
      return current;
  }
}

export function isTerminalStatus(status: TaskStatus): boolean {
  return (
    status === "completed" || status === "rejected" || status === "failed" || status === "cancelled"
  );
}

export function reduceEventsIntoDetail(task: TaskDetail, events: readonly TaskEvent[]): TaskDetail {
  return events.reduce<TaskDetail>((current, event) => {
    const eventResult = event.name === "run.completed" ? getCompletionResultText(event) : undefined;
    return {
      ...current,
      status: statusAfterEvent(current.status, event),
      result: eventResult ?? current.result,
    };
  }, task);
}
