import { taskClient } from "./task-client";

/**
 * One recurring run (a LangGraph Cron) registered on the configured task
 * source. Deep Work owns no schedule storage of its own — this always
 * reflects `/api/v1/schedules`, never a local copy. Read-only: a schedule-
 * triggered run does not yet appear in the task inbox, so no create/update/
 * delete surface exists here yet.
 */
export interface ScheduleSummary {
  scheduleId: string;
  agentId: string;
  cronExpression: string;
  timezone?: string;
  endTime?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ScheduleListResult {
  /** False when no real task source is configured — an honest "no registry", not "zero schedules". */
  available: boolean;
  items: ScheduleSummary[];
}

export interface ScheduleClient {
  listSchedules(signal?: AbortSignal): Promise<ScheduleListResult>;
}

async function readBody(response: Response): Promise<unknown> {
  const text = await response.text();
  if (text === "") {
    return undefined;
  }
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function toScheduleSummary(value: unknown): ScheduleSummary {
  if (!value || typeof value !== "object") {
    throw new Error("The API returned a malformed schedule.");
  }
  const record = value as Record<string, unknown>;
  return {
    scheduleId: String(record.scheduleId),
    agentId: String(record.agentId),
    cronExpression: String(record.cronExpression),
    timezone: typeof record.timezone === "string" ? record.timezone : undefined,
    endTime: typeof record.endTime === "string" ? record.endTime : undefined,
    createdAt: String(record.createdAt),
    updatedAt: String(record.updatedAt),
  };
}

function createHttpScheduleClient(apiBaseUrl: string): ScheduleClient {
  const schedulesUrl = `${apiBaseUrl.replace(/\/+$/, "")}/api/v1/schedules`;

  return {
    async listSchedules(signal?: AbortSignal): Promise<ScheduleListResult> {
      let response: Response;
      try {
        response = await fetch(schedulesUrl, { credentials: "include", signal });
      } catch {
        throw new Error(
          "Deep Work could not reach the API. Check that it is running and allows this browser origin.",
        );
      }
      const body = await readBody(response);
      if (!response.ok) {
        const message =
          body && typeof body === "object" && typeof Reflect.get(body, "message") === "string"
            ? (Reflect.get(body, "message") as string)
            : `The API returned HTTP ${response.status}.`;
        throw new Error(message);
      }
      const record = body as { available: boolean; items: unknown[] };
      return { available: record.available, items: record.items.map(toScheduleSummary) };
    },
  };
}

/** Fixture mode has no backend and therefore no schedule registry to query. */
function createFixtureScheduleClient(): ScheduleClient {
  return {
    async listSchedules(): Promise<ScheduleListResult> {
      return { available: false, items: [] };
    },
  };
}

export const scheduleClient: ScheduleClient =
  taskClient.mode === "fixture"
    ? createFixtureScheduleClient()
    : createHttpScheduleClient(taskClient.apiBaseUrl);
