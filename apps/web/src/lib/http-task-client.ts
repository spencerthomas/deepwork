import {
  normalizeCreateTaskResult,
  normalizeTaskDetail,
  normalizeTaskList,
  validatePrompt,
} from "./task-normalizers";
import { subscribeToTaskEvents } from "./sse";
import type {
  CreateTaskResult,
  DecisionInput,
  TaskClient,
  TaskDetail,
  TaskEventHandlers,
  TaskSummary,
} from "./task-types";

export const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

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
    const message = Reflect.get(body, "message");
    if (typeof message === "string" && message.trim() !== "") {
      return message;
    }
  }
  return `The API returned HTTP ${status}.`;
}

async function request(
  url: string,
  init: RequestInit,
  expectedStatus: number,
): Promise<unknown> {
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
    throw new Error(errorMessage(response.status, body));
  }
  return body;
}

export function createHttpTaskClient(
  configuredBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL,
): TaskClient {
  const apiBaseUrl = normalizeBaseUrl(configuredBaseUrl);
  const taskUrl = `${apiBaseUrl}/api/v1/tasks`;

  return {
    mode: "api",
    apiBaseUrl,

    async listTasks(signal?: AbortSignal): Promise<TaskSummary[]> {
      const body = await request(taskUrl, { method: "GET", signal }, 200);
      return normalizeTaskList(body);
    },

    async getTask(
      taskId: string,
      signal?: AbortSignal,
    ): Promise<TaskDetail> {
      const body = await request(
        `${taskUrl}/${encodeURIComponent(taskId)}`,
        { method: "GET", signal },
        200,
      );
      return normalizeTaskDetail(body);
    },

    async createTask(
      prompt: string,
      signal?: AbortSignal,
    ): Promise<CreateTaskResult> {
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
    ): Promise<void> {
      await request(
        `${taskUrl}/${encodeURIComponent(taskId)}/decisions`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(input),
          signal,
        },
        202,
      );
    },

    subscribe(taskId: string, handlers: TaskEventHandlers): () => void {
      return subscribeToTaskEvents(
        `${taskUrl}/${encodeURIComponent(taskId)}/events`,
        handlers,
      );
    },
  };
}
