import { taskClient } from "./task-client";

export type TaskTrace = { state: "available"; url: string } | { state: "unavailable" };

export interface TaskTraceClient {
  getTrace(taskId: string, signal?: AbortSignal): Promise<TaskTrace>;
}

function normalizeTrace(value: unknown): TaskTrace {
  if (!value || typeof value !== "object") {
    return { state: "unavailable" };
  }
  const state = Reflect.get(value, "state");
  const traceUrl = Reflect.get(value, "traceUrl");
  return state === "available" && typeof traceUrl === "string"
    ? { state: "available", url: traceUrl }
    : { state: "unavailable" };
}

export function createHttpTaskTraceClient(apiBaseUrl: string): TaskTraceClient {
  const tasksUrl = `${apiBaseUrl.replace(/\/+$/, "")}/api/v1/tasks`;
  return {
    async getTrace(taskId: string, signal?: AbortSignal): Promise<TaskTrace> {
      try {
        const response = await fetch(`${tasksUrl}/${encodeURIComponent(taskId)}/trace`, {
          credentials: "include",
          signal,
        });
        if (!response.ok) {
          return { state: "unavailable" };
        }
        return normalizeTrace(await response.json());
      } catch {
        return { state: "unavailable" };
      }
    },
  };
}

function createFixtureTaskTraceClient(): TaskTraceClient {
  return {
    async getTrace(): Promise<TaskTrace> {
      return { state: "unavailable" };
    },
  };
}

export const taskTraceClient: TaskTraceClient =
  taskClient.mode === "fixture"
    ? createFixtureTaskTraceClient()
    : createHttpTaskTraceClient(taskClient.apiBaseUrl);
