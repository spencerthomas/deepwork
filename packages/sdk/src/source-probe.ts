import {
  CAPABILITY_EVIDENCE_CLASSES,
  CAPABILITY_SAFE_REASONS,
  SOURCE_PROBE_STATES,
  availableCapability,
  capabilitySummary,
  unavailableCapability,
  unicodeCodePointLength,
  type CapabilityEvidenceClass,
  type CapabilitySafeReason,
  type SourceCapabilityObservation,
  type SourceProbeResult,
  type SourceProbeState,
} from "@deepwork/domain";

import type { OperationOptions } from "./ports.js";
import { contractError, type SdkError, type SdkResult } from "./result.js";

export const SOURCE_PROBE_PROBLEM_CODES = Object.freeze([
  "unauthorized",
  "request_invalid",
  "source_target_unavailable",
  "source_probe_unavailable",
  "source_endpoint_invalid",
] as const);

export type SourceProbeProblemCode = (typeof SOURCE_PROBE_PROBLEM_CODES)[number];

export interface SourceProbeTransport {
  check(
    request: Readonly<{
      kind: "langsmith_deployment";
      sourceTargetId: "classic-default";
      assistantId: string;
    }>,
    options?: OperationOptions,
  ): Promise<unknown>;
}

export interface SourceProbeService {
  check(
    candidate: Readonly<{ assistantId: string }>,
    options?: OperationOptions,
  ): Promise<SdkResult<SourceProbeResult>>;
}

export class SourceProbeTransportProblemError extends Error {
  readonly status: 401 | 404 | 422 | 503;
  readonly code: SourceProbeProblemCode;

  constructor(status: number, code: string) {
    const accepted =
      (status === 401 && code === "unauthorized") ||
      (status === 404 && code === "source_target_unavailable") ||
      (status === 422 && (code === "request_invalid" || code === "source_endpoint_invalid")) ||
      (status === 503 && code === "source_probe_unavailable");
    if (!accepted) {
      throw new TypeError("Source probe problem status/code pair is not accepted.");
    }
    super("Accepted source probe transport problem.");
    this.name = "SourceProbeTransportProblemError";
    this.status = status as 401 | 404 | 422 | 503;
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

function boundedString(value: unknown, maximum: number): value is string {
  return typeof value === "string" && value.length > 0 && unicodeCodePointLength(value) <= maximum;
}

function boundedNullableString(value: unknown, maximum: number): value is string | null {
  return value === null || boundedString(value, maximum);
}

function mapCapability(value: unknown): SourceCapabilityObservation | undefined {
  if (!isRecord(value) || typeof value.state !== "string" || !isState(value.state)) {
    return undefined;
  }
  const available = value.state === "available";
  const keys = [
    "name",
    "state",
    "observedAt",
    "adapterVersion",
    "contractVersion",
    "evidenceClass",
    ...(available ? [] : ["safeReason"]),
  ];
  if (
    !hasExactKeys(value, keys) ||
    !boundedString(value.name, 64) ||
    !boundedString(value.observedAt, 64) ||
    !boundedString(value.adapterVersion, 64) ||
    !boundedString(value.contractVersion, 64) ||
    typeof value.evidenceClass !== "string" ||
    !(CAPABILITY_EVIDENCE_CLASSES as readonly string[]).includes(value.evidenceClass)
  ) {
    return undefined;
  }
  const metadata = {
    observedAt: value.observedAt,
    adapterVersion: value.adapterVersion,
    contractVersion: value.contractVersion,
    evidenceClass: value.evidenceClass as CapabilityEvidenceClass,
  };
  try {
    const summary = available
      ? capabilitySummary(availableCapability(true, metadata))
      : typeof value.safeReason === "string" &&
          (CAPABILITY_SAFE_REASONS as readonly string[]).includes(value.safeReason)
        ? capabilitySummary(
            unavailableCapability(
              value.state as Exclude<SourceProbeState, "available">,
              value.safeReason as CapabilitySafeReason,
              metadata,
            ),
          )
        : undefined;
    return summary ? Object.freeze({ name: value.name, ...summary }) : undefined;
  } catch {
    return undefined;
  }
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
    !boundedNullableString(value.assistantId, 256) ||
    !boundedNullableString(value.graphId, 256) ||
    !boundedString(value.reason, 128) ||
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
    if (error.status === 401) {
      return Object.freeze({
        category: "permission-denied",
        safeMessage: "Authentication is required before checking this source.",
        retryable: false,
      });
    }
    return Object.freeze({
      category:
        error.status === 404
          ? "permission-denied"
          : error.status === 422
            ? "contract"
            : "capability-unavailable",
      safeMessage:
        error.code === "source_target_unavailable"
          ? "This source is not available in the current workspace."
          : error.code === "source_endpoint_invalid"
            ? "The deployment URL is not an allowed hosted HTTPS endpoint."
            : error.code === "request_invalid"
              ? "The source check request is invalid."
              : "No server-held source credential is configured for connection checks.",
      retryable: false,
    });
  }
  return Object.freeze({
    category: "unknown",
    safeMessage: "Deep Work could not reach the API to check this source.",
    retryable: false,
  });
}

export function createSourceProbeService(transport: SourceProbeTransport): SourceProbeService {
  return Object.freeze({
    async check(candidate: Readonly<{ assistantId: string }>, options?: OperationOptions) {
      const assistantId = candidate.assistantId.trim();
      if (!/^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$/.test(assistantId)) {
        return Object.freeze({
          ok: false,
          error: contractError("A valid assistant ID is required."),
        });
      }
      try {
        return mapSourceProbeResult(
          await transport.check(
            Object.freeze({
              kind: "langsmith_deployment",
              sourceTargetId: "classic-default",
              assistantId,
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
