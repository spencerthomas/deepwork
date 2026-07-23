export const CAPABILITY_STATES = Object.freeze([
  "available",
  "unavailable",
  "gated",
  "permission-denied",
  "unknown",
] as const);

export type CapabilityState = (typeof CAPABILITY_STATES)[number];

export const CAPABILITY_EVIDENCE_CLASSES = Object.freeze([
  "documented",
  "live-contract",
  "fixture",
] as const);

export type CapabilityEvidenceClass = (typeof CAPABILITY_EVIDENCE_CLASSES)[number];

export const CAPABILITY_SAFE_REASONS = Object.freeze([
  "contract-not-verified",
  "not-supported",
  "permission-required",
  "source-unavailable",
  "adapter-disabled",
] as const);

export type CapabilitySafeReason = (typeof CAPABILITY_SAFE_REASONS)[number];

declare const rfc3339InstantBrand: unique symbol;

export type Rfc3339Instant = string & {
  readonly [rfc3339InstantBrand]: "Rfc3339Instant";
};

export interface CapabilityEvidenceObject {
  readonly [key: string]: CapabilityEvidenceValue;
}

export type CapabilityEvidenceValue =
  | boolean
  | string
  | number
  | null
  | readonly CapabilityEvidenceValue[]
  | CapabilityEvidenceObject;

export type CapabilityEvidenceSnapshot<T extends CapabilityEvidenceValue> = T extends
  | null
  | boolean
  | string
  | number
  ? T
  : T extends readonly (infer Item extends CapabilityEvidenceValue)[]
    ? readonly CapabilityEvidenceSnapshot<Item>[]
    : T extends Readonly<Record<string, CapabilityEvidenceValue>>
      ? {
          readonly [Key in keyof T]: T[Key] extends CapabilityEvidenceValue
            ? CapabilityEvidenceSnapshot<T[Key]>
            : never;
        }
      : never;

export interface CapabilityEvidenceMetadata {
  readonly observedAt: string;
  readonly adapterVersion: string;
  readonly contractVersion: string;
  readonly evidenceClass: CapabilityEvidenceClass;
}

export interface AvailableCapabilityEvidence<
  T extends CapabilityEvidenceValue,
> extends CapabilityEvidenceMetadata {
  readonly state: "available";
  readonly value: CapabilityEvidenceSnapshot<T>;
  readonly observedAt: Rfc3339Instant;
}

export interface UnavailableCapabilityEvidence extends CapabilityEvidenceMetadata {
  readonly state: Exclude<CapabilityState, "available">;
  readonly safeReason: CapabilitySafeReason;
  readonly observedAt: Rfc3339Instant;
}

export type CapabilityEvidence<T extends CapabilityEvidenceValue> =
  | AvailableCapabilityEvidence<T>
  | UnavailableCapabilityEvidence;

export interface AvailableCapabilitySummary extends CapabilityEvidenceMetadata {
  readonly state: "available";
  readonly observedAt: Rfc3339Instant;
}

export interface UnavailableCapabilitySummary extends CapabilityEvidenceMetadata {
  readonly state: Exclude<CapabilityState, "available">;
  readonly safeReason: CapabilitySafeReason;
  readonly observedAt: Rfc3339Instant;
}

export type CapabilitySummary = AvailableCapabilitySummary | UnavailableCapabilitySummary;

function requireMetadata(value: string, label: string): string {
  if (value.length === 0 || value.trim() !== value) {
    throw new TypeError(`${label} must be a non-empty, trimmed value.`);
  }

  return value;
}

function requireEvidenceClass(value: unknown): CapabilityEvidenceClass {
  if (
    typeof value !== "string" ||
    !(CAPABILITY_EVIDENCE_CLASSES as readonly string[]).includes(value)
  ) {
    throw new TypeError("Capability evidence class must be a declared evidence class.");
  }

  return value as CapabilityEvidenceClass;
}

const RFC3339_INSTANT =
  /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,3}))?(Z|([+-])(\d{2}):(\d{2}))$/;

function isLeapYear(year: number): boolean {
  return year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
}

function daysInMonth(year: number, month: number): number {
  const days = [31, isLeapYear(year) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  return days[month - 1] ?? 0;
}

function requireRfc3339Instant(value: string): RegExpExecArray {
  const match = RFC3339_INSTANT.exec(value);
  if (match === null) {
    throw new TypeError("Capability observation time must be an RFC3339 instant.");
  }

  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const hour = Number(match[4]);
  const minute = Number(match[5]);
  const second = Number(match[6]);
  const offsetHour = Number(match[10] ?? 0);
  const offsetMinute = Number(match[11] ?? 0);

  if (
    year === 0 ||
    month < 1 ||
    month > 12 ||
    day < 1 ||
    day > daysInMonth(year, month) ||
    hour > 23 ||
    minute > 59 ||
    second > 59 ||
    offsetHour > 23 ||
    offsetMinute > 59
  ) {
    throw new TypeError("Capability observation time must be a valid RFC3339 instant.");
  }

  return match;
}

export function rfc3339Instant(value: string): Rfc3339Instant {
  const match = requireRfc3339Instant(value);
  const [
    ,
    yearText,
    monthText,
    dayText,
    hourText,
    minuteText,
    secondText,
    fractionText = "",
    zone,
    offsetSign,
    offsetHourText,
    offsetMinuteText,
  ] = match;
  const year = Number(yearText);
  const month = Number(monthText);
  const day = Number(dayText);
  const hour = Number(hourText);
  const minute = Number(minuteText);
  const second = Number(secondText);
  const offsetHour = Number(offsetHourText ?? 0);
  const offsetMinute = Number(offsetMinuteText ?? 0);
  const milliseconds = Number(fractionText.padEnd(3, "0"));
  const utc = new Date(0);
  utc.setUTCFullYear(year, month - 1, day);
  utc.setUTCHours(hour, minute, second, milliseconds);
  if (zone !== "Z") {
    const offset = (offsetHour * 60 + offsetMinute) * 60_000 * (offsetSign === "+" ? 1 : -1);
    utc.setTime(utc.getTime() - offset);
  }

  const normalized = utc.toISOString();
  requireRfc3339Instant(normalized);
  return normalized as Rfc3339Instant;
}

function snapshotCapabilityValue<T extends CapabilityEvidenceValue>(
  value: T,
  seen = new Set<object>(),
): CapabilityEvidenceSnapshot<T> {
  const valueType = typeof value;
  if (value === null || valueType === "boolean" || valueType === "string") {
    return value as CapabilityEvidenceSnapshot<T>;
  }
  if (valueType === "number") {
    if (!Number.isFinite(value)) {
      throw new TypeError("Capability evidence numbers must be finite.");
    }
    return value as CapabilityEvidenceSnapshot<T>;
  }
  if (valueType !== "object") {
    throw new TypeError("Capability evidence values must be JSON-compatible data.");
  }
  const objectValue = value as CapabilityEvidenceObject | readonly CapabilityEvidenceValue[];
  if (seen.has(objectValue)) {
    throw new TypeError("Capability evidence values must not contain cycles.");
  }
  seen.add(objectValue);

  if (Array.isArray(objectValue)) {
    const snapshot = Array.from(objectValue, (entry) => snapshotCapabilityValue(entry, seen));
    seen.delete(objectValue);
    return Object.freeze(snapshot) as CapabilityEvidenceSnapshot<T>;
  }

  const recordValue = objectValue as CapabilityEvidenceObject;
  const prototype = Object.getPrototypeOf(recordValue);
  if (prototype !== Object.prototype && prototype !== null) {
    throw new TypeError("Capability evidence objects must be plain records.");
  }
  const descriptors = Object.getOwnPropertyDescriptors(recordValue);
  for (const [key, descriptor] of Object.entries(descriptors)) {
    if (!descriptor.enumerable || !("value" in descriptor)) {
      throw new TypeError(`Capability evidence property ${key} must be enumerable data.`);
    }
  }
  if (Object.getOwnPropertySymbols(recordValue).length > 0) {
    throw new TypeError("Capability evidence objects must not contain symbol keys.");
  }
  const snapshot = Object.fromEntries(
    Object.entries(recordValue).map(([key, entry]) => [key, snapshotCapabilityValue(entry, seen)]),
  );
  seen.delete(recordValue);
  return Object.freeze(snapshot) as CapabilityEvidenceSnapshot<T>;
}

const SAFE_REASONS_BY_STATE = Object.freeze({
  unavailable: Object.freeze(["not-supported", "source-unavailable", "adapter-disabled"] as const),
  gated: Object.freeze(["permission-required", "adapter-disabled"] as const),
  "permission-denied": Object.freeze(["permission-required"] as const),
  unknown: Object.freeze(["contract-not-verified"] as const),
});

function requireCoherentUnavailableReason(
  state: Exclude<CapabilityState, "available">,
  safeReason: CapabilitySafeReason,
): void {
  const allowed = SAFE_REASONS_BY_STATE[state] as readonly CapabilitySafeReason[];
  if (!allowed.includes(safeReason)) {
    throw new TypeError(`Capability state ${state} cannot use safe reason ${safeReason}.`);
  }
}

/*
 * The following constructors are the only place evidence becomes trusted domain
 * state. Keep runtime validation even though TypeScript excludes unsupported
 * values for normal callers.
 */
export function availableCapability<T extends CapabilityEvidenceValue>(
  value: T,
  metadata: CapabilityEvidenceMetadata,
): AvailableCapabilityEvidence<T> {
  return Object.freeze({
    state: "available",
    value: snapshotCapabilityValue(value),
    observedAt: rfc3339Instant(metadata.observedAt),
    adapterVersion: requireMetadata(metadata.adapterVersion, "Adapter version"),
    contractVersion: requireMetadata(metadata.contractVersion, "Contract version"),
    evidenceClass: requireEvidenceClass(metadata.evidenceClass),
  });
}

export function unavailableCapability(
  state: Exclude<CapabilityState, "available">,
  safeReason: CapabilitySafeReason,
  metadata: CapabilityEvidenceMetadata,
): UnavailableCapabilityEvidence {
  requireCoherentUnavailableReason(state, safeReason);
  return Object.freeze({
    state,
    safeReason,
    observedAt: rfc3339Instant(metadata.observedAt),
    adapterVersion: requireMetadata(metadata.adapterVersion, "Adapter version"),
    contractVersion: requireMetadata(metadata.contractVersion, "Contract version"),
    evidenceClass: requireEvidenceClass(metadata.evidenceClass),
  });
}

export function isCapabilityAvailable<T extends CapabilityEvidenceValue>(
  evidence: CapabilityEvidence<T>,
): evidence is AvailableCapabilityEvidence<T> {
  return evidence.state === "available";
}

export function capabilitySummary<T extends CapabilityEvidenceValue>(
  evidence: AvailableCapabilityEvidence<T>,
): AvailableCapabilitySummary;
export function capabilitySummary(
  evidence: UnavailableCapabilityEvidence,
): UnavailableCapabilitySummary;
export function capabilitySummary<T extends CapabilityEvidenceValue>(
  evidence: CapabilityEvidence<T>,
): CapabilitySummary;
export function capabilitySummary<T extends CapabilityEvidenceValue>(
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
