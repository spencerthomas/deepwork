import { isRecord } from "./task-normalizers";

export type SourceProbeState =
  | "available"
  | "unavailable"
  | "gated"
  | "permission-denied"
  | "unknown";

export interface SourceCapabilityObservation {
  name: string;
  state: SourceProbeState;
  reason: string;
}

export interface SourceProbeResult {
  kind: "langsmith_deployment";
  state: SourceProbeState;
  assistantId: string | null;
  graphId: string | null;
  reason: string;
  saveAllowed: false;
  capabilities: SourceCapabilityObservation[];
}

const STATES: readonly SourceProbeState[] = [
  "available",
  "unavailable",
  "gated",
  "permission-denied",
  "unknown",
];

function isState(value: unknown): value is SourceProbeState {
  return typeof value === "string" && STATES.includes(value as SourceProbeState);
}

function nullableString(value: unknown): value is string | null {
  return typeof value === "string" || value === null;
}

function toResult(value: unknown): SourceProbeResult {
  if (!isRecord(value)) {
    throw new Error("The API returned a malformed source check.");
  }
  const capabilities = value["capabilities"];
  if (
    value["kind"] !== "langsmith_deployment" ||
    !isState(value["state"]) ||
    !nullableString(value["assistantId"]) ||
    !nullableString(value["graphId"]) ||
    typeof value["reason"] !== "string" ||
    value["saveAllowed"] !== false ||
    !Array.isArray(capabilities)
  ) {
    throw new Error("The API returned a malformed source check.");
  }
  const mapped = capabilities.map((capability): SourceCapabilityObservation => {
    if (
      !isRecord(capability) ||
      typeof capability["name"] !== "string" ||
      !isState(capability["state"]) ||
      typeof capability["reason"] !== "string"
    ) {
      throw new Error("The API returned a malformed source check.");
    }
    return {
      name: capability["name"],
      state: capability["state"],
      reason: capability["reason"],
    };
  });
  return {
    kind: "langsmith_deployment",
    state: value["state"],
    assistantId: value["assistantId"],
    graphId: value["graphId"],
    reason: value["reason"],
    saveAllowed: false,
    capabilities: mapped,
  };
}

function safeProblemMessage(value: unknown, status: number): string {
  if (isRecord(value) && typeof value["message"] === "string") {
    return value["message"];
  }
  return `The source check returned HTTP ${status}.`;
}

export async function probeClassicSource(
  apiBaseUrl: string,
  input: { endpoint: string; assistantId: string },
  signal?: AbortSignal,
): Promise<SourceProbeResult> {
  const url = `${apiBaseUrl.replace(/\/+$/, "")}/api/v1/sources/probes`;
  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      credentials: "include",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        kind: "langsmith_deployment",
        deploymentUrl: input.endpoint,
        assistantId: input.assistantId,
      }),
      signal,
    });
  } catch {
    throw new Error("Deep Work could not reach the API to check this source.");
  }
  if (!response.ok) {
    let problem: unknown;
    try {
      problem = await response.json();
    } catch {
      problem = null;
    }
    throw new Error(safeProblemMessage(problem, response.status));
  }
  return toResult(await response.json());
}
