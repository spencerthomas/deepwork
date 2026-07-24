import {
  normalizeCancelResult,
  normalizeCreateTaskResult,
  normalizeDecisionResult,
  normalizePlanUpdateResult,
  normalizeTaskDetail,
  normalizeTaskList,
  validateDecisionInput,
  validatePlanSteps,
  validatePrompt,
} from "./task-normalizers";
import { subscribeToTaskEvents } from "./sse";
import type {
  CancelResult,
  CreateTaskResult,
  DecisionInput,
  DecisionResult,
  PlanUpdateInput,
  PlanUpdateResult,
  TaskClient,
  TaskDetail,
  TaskEventHandlers,
  TaskSummary,
} from "./task-types";

export const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const RECOVERABLE_PLAN_PROBLEM_CODES = new Set([
  "plan_revision_conflict",
  "interrupt_stale",
  "interrupt_mismatch",
]);
const RECOVERABLE_DECISION_PROBLEM_CODES = new Set([
  "interrupt_stale",
  "interrupt_mismatch",
  "decision_conflict",
]);

class TaskApiError extends Error {
  readonly code?: string;

  constructor(message: string, code?: string) {
    super(message);
    this.name = "TaskApiError";
    this.code = code;
  }
}

export function isRecoverablePlanProblem(error: unknown): boolean {
  return (
    error instanceof TaskApiError &&
    error.code !== undefined &&
    RECOVERABLE_PLAN_PROBLEM_CODES.has(error.code)
  );
}

export function isRecoverableDecisionProblem(error: unknown): boolean {
  return (
    error instanceof TaskApiError &&
    error.code !== undefined &&
    RECOVERABLE_DECISION_PROBLEM_CODES.has(error.code)
  );
}

function normalizeBaseUrl(value: string | undefined): string {
  const candidate = value?.trim() || DEFAULT_API_BASE_URL;
  return candidate.replace(/\/+$/, "");
}

async function readResponseBody(response: Response): Promise<unknown> {
  const text = await response.text();
  if (text === "") {
    return undefined;
  }
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    try {
      return JSON.parse(text);
    } catch {
      throw new Error("The API returned malformed JSON.");
    }
  }
  return text;
}

function errorMessage(status: number, body: unknown): string {
  if (typeof body === "string" && body.trim() !== "") {
    return body;
  }
  if (body && typeof body === "object") {
    const detail = Reflect.get(body, "detail");
    if (typeof detail === "string" && detail.trim() !== "") {
      return detail;
    }
    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => {
          if (!item || typeof item !== "object") {
            return undefined;
          }
          const message = Reflect.get(item, "msg");
          return typeof message === "string" && message.trim() !== "" ? message : undefined;
        })
        .filter((message): message is string => message !== undefined);
      if (messages.length > 0) {
        return messages.join(" ");
      }
    }
    const message = Reflect.get(body, "message");
    if (typeof message === "string" && message.trim() !== "") {
      return message;
    }
  }
  return `The API returned HTTP ${status}.`;
}

function errorCode(body: unknown): string | undefined {
  if (!body || typeof body !== "object") {
    return undefined;
  }
  const code = Reflect.get(body, "code");
  return typeof code === "string" && code.trim() !== "" ? code : undefined;
}

async function request(url: string, init: RequestInit, expectedStatus: number): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch {
    throw new Error(
      "Deep Work could not reach the API. Check that it is running and allows this browser origin.",
    );
  }

  const body = await readResponseBody(response);
  if (response.status !== expectedStatus) {
    throw new TaskApiError(errorMessage(response.status, body), errorCode(body));
  }
  return body;
}

export function createHttpTaskClient(configuredBaseUrl?: string): TaskClient {
  const apiBaseUrl = normalizeBaseUrl(configuredBaseUrl);
  const taskUrl = `${apiBaseUrl}/api/v1/tasks`;

  return {
    mode: "api",
    apiBaseUrl,

    async listTasks(signal?: AbortSignal): Promise<TaskSummary[]> {
      const body = await request(taskUrl, { method: "GET", signal }, 200);
      return normalizeTaskList(body);
    },

    async getTask(taskId: string, signal?: AbortSignal): Promise<TaskDetail> {
      const body = await request(
        `${taskUrl}/${encodeURIComponent(taskId)}`,
        { method: "GET", signal },
        200,
      );
      return normalizeTaskDetail(body);
    },

    async createTask(prompt: string, signal?: AbortSignal): Promise<CreateTaskResult> {
      const normalizedPrompt = validatePrompt(prompt);
      const body = await request(
        taskUrl,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ prompt: normalizedPrompt }),
          signal,
        },
        202,
      );
      return normalizeCreateTaskResult(body);
    },

    async decide(
      taskId: string,
      input: DecisionInput,
      signal?: AbortSignal,
    ): Promise<DecisionResult> {
      const decision = validateDecisionInput(input);
      const body = await request(
        `${taskUrl}/${encodeURIComponent(taskId)}/decisions`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            ...decision,
            ...(decision.comment ? { comment: decision.comment } : {}),
          }),
          signal,
        },
        202,
      );
      const receipt = normalizeDecisionResult(body);
      if (
        receipt.taskId !== taskId ||
        receipt.interruptId !== decision.interruptId ||
        receipt.decision !== decision.decision
      ) {
        throw new Error("The decision receipt did not match the requested task and interrupt.");
      }
      return receipt;
    },

    async cancelTask(taskId: string, signal?: AbortSignal): Promise<CancelResult> {
      const body = await request(
        `${taskUrl}/${encodeURIComponent(taskId)}/cancel`,
        { method: "POST", signal },
        202,
      );
      const receipt = normalizeCancelResult(body);
      if (receipt.taskId !== taskId) {
        throw new Error("The cancel receipt did not match the requested task.");
      }
      return receipt;
    },

    async updatePlan(
      taskId: string,
      input: PlanUpdateInput,
      signal?: AbortSignal,
    ): Promise<PlanUpdateResult> {
      if (!Number.isInteger(input.expectedRevision) || input.expectedRevision < 1) {
        throw new Error("The plan revision must be a positive integer.");
      }
      const steps = validatePlanSteps(input.steps);
      const body = await request(
        `${taskUrl}/${encodeURIComponent(taskId)}/plan`,
        {
          method: "PATCH",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ ...input, steps }),
          signal,
        },
        200,
      );
      const receipt = normalizePlanUpdateResult(body);
      if (
        receipt.taskId !== taskId ||
        receipt.interruptId !== input.interruptId ||
        receipt.plan.revision !== input.expectedRevision + 1
      ) {
        throw new Error("The plan update receipt did not match the requested task and revision.");
      }
      return receipt;
    },

    subscribe(taskId: string, handlers: TaskEventHandlers): () => void {
      return subscribeToTaskEvents(`${taskUrl}/${encodeURIComponent(taskId)}/events`, handlers);
    },
  };
}
