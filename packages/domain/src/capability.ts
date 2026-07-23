export const CAPABILITY_STATES = [
  "available",
  "unavailable",
  "gated",
  "permission-denied",
  "unknown",
] as const;

export type CapabilityState = (typeof CAPABILITY_STATES)[number];

export const CAPABILITY_EVIDENCE_CLASSES = [
  "documented",
  "live-contract",
  "fixture",
] as const;

export type CapabilityEvidenceClass =
  (typeof CAPABILITY_EVIDENCE_CLASSES)[number];

export const CAPABILITY_SAFE_REASONS = [
  "contract-not-verified",
  "not-supported",
  "permission-required",
  "source-unavailable",
  "adapter-disabled",
] as const;

export type CapabilitySafeReason = (typeof CAPABILITY_SAFE_REASONS)[number];

export interface CapabilityEvidenceMetadata {
  readonly observedAt: string;
  readonly adapterVersion: string;
  readonly contractVersion: string;
  readonly evidenceClass: CapabilityEvidenceClass;
}

export interface AvailableCapabilityEvidence<T>
  extends CapabilityEvidenceMetadata {
  readonly state: "available";
  readonly value: T;
}

export interface UnavailableCapabilityEvidence
  extends CapabilityEvidenceMetadata {
  readonly state: Exclude<CapabilityState, "available">;
  readonly safeReason: CapabilitySafeReason;
}

export type CapabilityEvidence<T> =
  | AvailableCapabilityEvidence<T>
  | UnavailableCapabilityEvidence;

export interface AvailableCapabilitySummary
  extends CapabilityEvidenceMetadata {
  readonly state: "available";
}

export interface UnavailableCapabilitySummary
  extends CapabilityEvidenceMetadata {
  readonly state: Exclude<CapabilityState, "available">;
  readonly safeReason: CapabilitySafeReason;
}

export type CapabilitySummary =
  | AvailableCapabilitySummary
  | UnavailableCapabilitySummary;

function requireMetadata(value: string, label: string): string {
  if (value.length === 0 || value.trim() !== value) {
    throw new TypeError(`${label} must be a non-empty, trimmed value.`);
  }

  return value;
}

function requireObservation(value: string): string {
  if (!Number.isFinite(Date.parse(value))) {
    throw new TypeError("Capability observation time must be an ISO timestamp.");
  }

  return value;
}

export function availableCapability<T>(
  value: T,
  metadata: CapabilityEvidenceMetadata,
): AvailableCapabilityEvidence<T> {
  return Object.freeze({
    state: "available",
    value,
    observedAt: requireObservation(metadata.observedAt),
    adapterVersion: requireMetadata(
      metadata.adapterVersion,
      "Adapter version",
    ),
    contractVersion: requireMetadata(
      metadata.contractVersion,
      "Contract version",
    ),
    evidenceClass: metadata.evidenceClass,
  });
}

export function unavailableCapability(
  state: Exclude<CapabilityState, "available">,
  safeReason: CapabilitySafeReason,
  metadata: CapabilityEvidenceMetadata,
): UnavailableCapabilityEvidence {
  return Object.freeze({
    state,
    safeReason,
    observedAt: requireObservation(metadata.observedAt),
    adapterVersion: requireMetadata(
      metadata.adapterVersion,
      "Adapter version",
    ),
    contractVersion: requireMetadata(
      metadata.contractVersion,
      "Contract version",
    ),
    evidenceClass: metadata.evidenceClass,
  });
}

export function isCapabilityAvailable<T>(
  evidence: CapabilityEvidence<T>,
): evidence is AvailableCapabilityEvidence<T> {
  return evidence.state === "available";
}

export function capabilitySummary<T>(
  evidence: CapabilityEvidence<T>,
): CapabilitySummary {
  if ("safeReason" in evidence) {
    return Object.freeze({
      state: evidence.state,
      safeReason: evidence.safeReason,
      observedAt: evidence.observedAt,
      adapterVersion: evidence.adapterVersion,
      contractVersion: evidence.contractVersion,
      evidenceClass: evidence.evidenceClass,
    });
  }

  return Object.freeze({
    state: evidence.state,
    observedAt: evidence.observedAt,
    adapterVersion: evidence.adapterVersion,
    contractVersion: evidence.contractVersion,
    evidenceClass: evidence.evidenceClass,
  });
}
