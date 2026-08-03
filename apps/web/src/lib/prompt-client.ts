import { taskClient } from "./task-client";
import { isRecord } from "./task-normalizers";

export interface PromptState {
  value: string;
  isDefault: boolean;
}

export interface PromptClient {
  getPrompt(signal?: AbortSignal): Promise<PromptState>;
  updatePrompt(systemPrompt: string | null, signal?: AbortSignal): Promise<PromptState>;
}

function toPromptState(value: unknown): PromptState {
  if (!isRecord(value)) {
    throw new Error("The API returned a malformed system prompt.");
  }
  const systemPrompt = value["systemPrompt"];
  const isDefault = value["isDefault"];
  if (
    (typeof systemPrompt !== "string" && systemPrompt !== null) ||
    typeof isDefault !== "boolean"
  ) {
    throw new Error("The API returned a malformed system prompt.");
  }
  return { value: systemPrompt ?? "", isDefault };
}

async function request(url: string, init: RequestInit): Promise<PromptState> {
  let response: Response;
  try {
    response = await fetch(url, { ...init, credentials: "include" });
  } catch {
    throw new Error(
      "Deep Work could not reach the API. Check that it is running and allows this browser origin.",
    );
  }
  if (!response.ok) {
    throw new Error(`The API returned HTTP ${response.status}.`);
  }
  return toPromptState(await response.json());
}

export function createHttpPromptClient(apiBaseUrl: string): PromptClient {
  const promptUrl = `${apiBaseUrl.replace(/\/+$/, "")}/api/v1/settings/prompt`;
  return {
    getPrompt(signal?: AbortSignal): Promise<PromptState> {
      return request(promptUrl, { method: "GET", signal });
    },

    updatePrompt(systemPrompt: string | null, signal?: AbortSignal): Promise<PromptState> {
      return request(promptUrl, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ systemPrompt }),
        signal,
      });
    },
  };
}

function createFixturePromptClient(): PromptClient {
  const unavailable = (): never => {
    throw new Error("The system prompt is not available in demo mode.");
  };
  return { getPrompt: unavailable, updatePrompt: unavailable };
}

export const promptClient: PromptClient =
  taskClient.mode === "fixture"
    ? createFixturePromptClient()
    : createHttpPromptClient(taskClient.apiBaseUrl);
