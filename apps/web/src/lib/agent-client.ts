import { taskClient } from "./task-client";

/**
 * One agent registered on the configured task source (a LangGraph Assistant
 * sharing the deployed graph). Deep Work owns no agent storage of its own —
 * this always reflects `/api/v1/agents`, never a local copy.
 */
export interface AgentSummary {
  agentId: string;
  name: string;
  description?: string;
  systemPrompt?: string;
  isDefault: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface AgentListResult {
  /** False when no real task source is configured — an honest "no registry", not "zero agents". */
  available: boolean;
  items: AgentSummary[];
}

export interface AgentEditableInput {
  name: string;
  description?: string;
  systemPrompt?: string;
}

export interface AgentClient {
  listAgents(signal?: AbortSignal): Promise<AgentListResult>;
  createAgent(input: AgentEditableInput, signal?: AbortSignal): Promise<AgentSummary>;
  updateAgent(
    agentId: string,
    input: AgentEditableInput,
    signal?: AbortSignal,
  ): Promise<AgentSummary>;
  deleteAgent(agentId: string, signal?: AbortSignal): Promise<void>;
}

class AgentApiError extends Error {
  readonly code?: string;

  constructor(message: string, code?: string) {
    super(message);
    this.name = "AgentApiError";
    this.code = code;
  }
}

function errorMessage(status: number, body: unknown): string {
  if (body && typeof body === "object") {
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

async function request(url: string, init: RequestInit, expectedStatus: number): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(url, { ...init, credentials: "include" });
  } catch {
    throw new Error(
      "Deep Work could not reach the API. Check that it is running and allows this browser origin.",
    );
  }
  const body = await readBody(response);
  if (response.status !== expectedStatus) {
    throw new AgentApiError(errorMessage(response.status, body), errorCode(body));
  }
  return body;
}

function toAgentSummary(value: unknown): AgentSummary {
  if (!value || typeof value !== "object") {
    throw new Error("The API returned a malformed agent.");
  }
  const record = value as Record<string, unknown>;
  return {
    agentId: String(record.agentId),
    name: String(record.name),
    description: typeof record.description === "string" ? record.description : undefined,
    systemPrompt: typeof record.systemPrompt === "string" ? record.systemPrompt : undefined,
    isDefault: record.isDefault === true,
    createdAt: String(record.createdAt),
    updatedAt: String(record.updatedAt),
  };
}

function editableBody(input: AgentEditableInput): Record<string, unknown> {
  return {
    name: input.name,
    description: input.description?.trim() ? input.description.trim() : null,
    systemPrompt: input.systemPrompt?.trim() ? input.systemPrompt : null,
  };
}

function createHttpAgentClient(apiBaseUrl: string): AgentClient {
  const agentsUrl = `${apiBaseUrl.replace(/\/+$/, "")}/api/v1/agents`;

  return {
    async listAgents(signal?: AbortSignal): Promise<AgentListResult> {
      const body = await request(agentsUrl, { method: "GET", signal }, 200);
      const record = body as { available: boolean; items: unknown[] };
      return { available: record.available, items: record.items.map(toAgentSummary) };
    },

    async createAgent(input: AgentEditableInput, signal?: AbortSignal): Promise<AgentSummary> {
      const body = await request(
        agentsUrl,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(editableBody(input)),
          signal,
        },
        201,
      );
      return toAgentSummary(body);
    },

    async updateAgent(
      agentId: string,
      input: AgentEditableInput,
      signal?: AbortSignal,
    ): Promise<AgentSummary> {
      const body = await request(
        `${agentsUrl}/${encodeURIComponent(agentId)}`,
        {
          method: "PUT",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(editableBody(input)),
          signal,
        },
        200,
      );
      return toAgentSummary(body);
    },

    async deleteAgent(agentId: string, signal?: AbortSignal): Promise<void> {
      await request(
        `${agentsUrl}/${encodeURIComponent(agentId)}`,
        { method: "DELETE", signal },
        204,
      );
    },
  };
}

/** Fixture mode has no backend and therefore no agent registry to query. */
function createFixtureAgentClient(): AgentClient {
  const unavailable = (): never => {
    throw new Error("Agents are not available in demo mode.");
  };
  return {
    async listAgents(): Promise<AgentListResult> {
      return { available: false, items: [] };
    },
    createAgent: unavailable,
    updateAgent: unavailable,
    deleteAgent: unavailable,
  };
}

export const agentClient: AgentClient =
  taskClient.mode === "fixture"
    ? createFixtureAgentClient()
    : createHttpAgentClient(taskClient.apiBaseUrl);
