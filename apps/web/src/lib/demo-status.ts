/**
 * Typed access to `GET {apiBaseUrl}/api/v1/demo/status`.
 *
 * Honesty rule (docs/DESIGN.md): capability states drive gated/unavailable UI,
 * so this module fails closed. Anything malformed normalizes to `undefined`
 * (callers show an error/unknown state) and an unrecognized capability state
 * is reported as "unknown", never as available.
 */

export type CapabilityState = "available" | "unavailable" | "unknown";

export interface DemoCapability {
  name: string;
  state: CapabilityState;
}

export interface DemoStatus {
  mode: string;
  evidenceClass: string;
  capabilities: DemoCapability[];
  safeReason: string;
  /** Where this status came from: the live API or the local fixture adapter. */
  source: "api" | "fixture";
}

/** Capability names the product surfaces reference. */
export const CAPABILITY_NAMES = {
  localTaskLoop: "local_task_loop",
  taskStream: "task_stream",
  authentication: "authentication",
  durableJobs: "durable_jobs",
  sources: "sources",
  externalProviders: "external_providers",
} as const;

function asRecord(value: unknown): Record<string, unknown> | undefined {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;
}

/** Read a required string that the API may spell in snake_case or camelCase. */
function readString(record: Record<string, unknown>, ...keys: string[]): string | undefined {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === "string" && value.length > 0) {
      return value;
    }
  }
  return undefined;
}

function normalizeCapabilityState(value: unknown): CapabilityState {
  return value === "available" || value === "unavailable" ? value : "unknown";
}

function normalizeCapability(value: unknown): DemoCapability | undefined {
  const record = asRecord(value);
  if (!record) {
    return undefined;
  }
  const name = readString(record, "name");
  if (name === undefined || typeof record["state"] !== "string") {
    return undefined;
  }
  return { name, state: normalizeCapabilityState(record["state"]) };
}

/**
 * Normalize a demo-status payload. Returns `undefined` on any shape violation
 * so callers surface an explicit unknown state instead of fabricated data.
 */
export function normalizeDemoStatus(
  payload: unknown,
  source: DemoStatus["source"] = "api",
): DemoStatus | undefined {
  const record = asRecord(payload);
  if (!record) {
    return undefined;
  }

  const mode = readString(record, "mode");
  const evidenceClass = readString(record, "evidence_class", "evidenceClass");
  const safeReason = readString(record, "safe_reason", "safeReason");
  const rawCapabilities = record["capabilities"];
  if (
    mode === undefined ||
    evidenceClass === undefined ||
    safeReason === undefined ||
    !Array.isArray(rawCapabilities)
  ) {
    return undefined;
  }

  const capabilities: DemoCapability[] = [];
  for (const entry of rawCapabilities) {
    const capability = normalizeCapability(entry);
    if (!capability) {
      return undefined;
    }
    capabilities.push(capability);
  }

  return { mode, evidenceClass, capabilities, safeReason, source };
}

/** Look up one capability's state, failing closed to "unknown". */
export function capabilityState(status: DemoStatus | undefined, name: string): CapabilityState {
  if (!status) {
    return "unknown";
  }
  return status.capabilities.find((capability) => capability.name === name)?.state ?? "unknown";
}

export const FIXTURE_SAFE_REASON =
  "Synthesized by the in-browser fixture adapter: credential-free local task and " +
  "SSE fixtures are available; external providers, authentication, and durability " +
  "are unavailable.";

/**
 * Fixture-mode equivalent of the API's demo status, synthesized locally so the
 * fixture client never issues network requests. Mirrors
 * apps/api/src/deepwork_api/adapters/fixture/status.py and is labeled fixture.
 */
export function fixtureDemoStatus(): DemoStatus {
  return {
    mode: "fixture",
    evidenceClass: "fixture",
    capabilities: [
      { name: CAPABILITY_NAMES.localTaskLoop, state: "available" },
      { name: CAPABILITY_NAMES.taskStream, state: "available" },
      { name: CAPABILITY_NAMES.authentication, state: "unavailable" },
      { name: CAPABILITY_NAMES.durableJobs, state: "unavailable" },
      { name: CAPABILITY_NAMES.sources, state: "unavailable" },
      { name: CAPABILITY_NAMES.externalProviders, state: "unavailable" },
    ],
    safeReason: FIXTURE_SAFE_REASON,
    source: "fixture",
  };
}

/**
 * Fetch and normalize the demo status. Never rejects: network failures,
 * non-2xx responses, and malformed bodies all resolve to `undefined`.
 */
export async function fetchDemoStatus(
  apiBaseUrl: string,
  signal?: AbortSignal,
): Promise<DemoStatus | undefined> {
  try {
    const base = apiBaseUrl.replace(/\/+$/, "");
    const response = await fetch(`${base}/api/v1/demo/status`, {
      headers: { accept: "application/json" },
      signal,
    });
    if (!response.ok) {
      return undefined;
    }
    return normalizeDemoStatus(await response.json(), "api");
  } catch {
    return undefined;
  }
}
