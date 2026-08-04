import {
  SOURCE_PROBE_STATES,
  type SourceCapabilityObservation,
  type SourceProbeResult,
  type SourceProbeState,
} from "@deepwork/domain";

import type { OperationOptions } from "./ports.js";
import { contractError, type SdkError, type SdkResult } from "./result.js";

export const SOURCE_PROBE_PROBLEM_CODES = Object.freeze([
  "source_probe_unavailable",
  "source_endpoint_invalid",
] as const);

export type SourceProbeProblemCode = (typeof SOURCE_PROBE_PROBLEM_CODES)[number];

export interface SourceProbeTransport {
  check(
    request: Readonly<{
      kind: "langsmith_deployment";
      deploymentUrl: string;
      assistantId: string;
    }>,
    options?: OperationOptions,
  ): Promise<unknown>;
}

export interface SourceProbeService {
  check(
    candidate: Readonly<{ endpoint: string; assistantId: string }>,
    options?: OperationOptions,
  ): Promise<SdkResult<SourceProbeResult>>;
}

export class SourceProbeTransportProblemError extends Error {
  readonly status: 422 | 503;
  readonly code: SourceProbeProblemCode;

  constructor(status: number, code: string) {
    const accepted =
      (status === 422 && code === "source_endpoint_invalid") ||
      (status === 503 && code === "source_probe_unavailable");
    if (!accepted) {
      throw new TypeError("Source probe problem status/code pair is not accepted.");
    }
    super("Accepted source probe transport problem.");
    this.name = "SourceProbeTransportProblemError";
    this.status = status as 422 | 503;
    this.code = code as SourceProbeProblemCode;
  }
}

export function sourceProbeTransportProblem(
  status: number,
  code: string,
): SourceProbeTransportProblemError {
  return new SourceProbeTransportProblemError(status, code);
}

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasExactKeys(value: Readonly<Record<string, unknown>>, keys: readonly string[]): boolean {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  return actual.length === expected.length && actual.every((key, index) => key === expected[index]);
}

function isState(value: unknown): value is SourceProbeState {
  return typeof value === "string" && (SOURCE_PROBE_STATES as readonly string[]).includes(value);
}

function nullableString(value: unknown): value is string | null {
  return typeof value === "string" || value === null;
}

function mapCapability(value: unknown): SourceCapabilityObservation | undefined {
  if (
    !isRecord(value) ||
    !hasExactKeys(value, ["name", "state", "reason"]) ||
    typeof value.name !== "string" ||
    value.name.length === 0 ||
    !isState(value.state) ||
    typeof value.reason !== "string" ||
    value.reason.length === 0
  ) {
    return undefined;
  }
  return Object.freeze({ name: value.name, state: value.state, reason: value.reason });
}

export function mapSourceProbeResult(value: unknown): SdkResult<SourceProbeResult> {
  if (
    !isRecord(value) ||
    !hasExactKeys(value, [
      "kind",
      "state",
      "assistantId",
      "graphId",
      "reason",
      "saveAllowed",
      "capabilities",
    ]) ||
    value.kind !== "langsmith_deployment" ||
    !isState(value.state) ||
    !nullableString(value.assistantId) ||
    !nullableString(value.graphId) ||
    typeof value.reason !== "string" ||
    value.reason.length === 0 ||
    value.saveAllowed !== false ||
    !Array.isArray(value.capabilities)
  ) {
    return Object.freeze({
      ok: false,
      error: contractError("The API returned a malformed source check."),
    });
  }
  const capabilities = value.capabilities.map(mapCapability);
  if (capabilities.some((capability) => capability === undefined)) {
    return Object.freeze({
      ok: false,
      error: contractError("The API returned a malformed source check."),
    });
  }
  return Object.freeze({
    ok: true,
    value: Object.freeze({
      kind: "langsmith_deployment",
      state: value.state,
      assistantId: value.assistantId,
      graphId: value.graphId,
      reason: value.reason,
      saveAllowed: false,
      capabilities: Object.freeze(capabilities as SourceCapabilityObservation[]),
    }),
  });
}

function sourceProbeFailure(error: unknown): SdkError {
  if (error instanceof SourceProbeTransportProblemError) {
    return Object.freeze({
      category: error.status === 422 ? "contract" : "capability-unavailable",
      safeMessage:
        error.code === "source_endpoint_invalid"
          ? "The deployment URL is not an allowed hosted HTTPS endpoint."
          : "No server-held source credential is configured for connection checks.",
      retryable: false,
    });
  }
  return Object.freeze({
    category: "unknown",
    safeMessage: "Deep Work could not reach the API to check this source.",
    retryable: true,
  });
}

export function createSourceProbeService(transport: SourceProbeTransport): SourceProbeService {
  return Object.freeze({
    async check(
      candidate: Readonly<{ endpoint: string; assistantId: string }>,
      options?: OperationOptions,
    ) {
      if (candidate.endpoint.trim().length === 0 || candidate.assistantId.trim().length === 0) {
        return Object.freeze({
          ok: false,
          error: contractError("A deployment URL and assistant ID are required."),
        });
      }
      try {
        return mapSourceProbeResult(
          await transport.check(
            Object.freeze({
              kind: "langsmith_deployment",
              deploymentUrl: candidate.endpoint,
              assistantId: candidate.assistantId,
            }),
            options,
          ),
        );
      } catch (error) {
        return Object.freeze({ ok: false, error: sourceProbeFailure(error) });
      }
    },
  });
}
