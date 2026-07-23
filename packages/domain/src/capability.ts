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

export type CapabilityEvidenceClass =
  (typeof CAPABILITY_EVIDENCE_CLASSES)[number];

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

export type CapabilityEvidenceValue =
  | boolean
  | string
  | number
  | null
  | readonly CapabilityEvidenceValue[]
  | Readonly<Record<string, CapabilityEvidenceValue>>;

export type CapabilityEvidenceSnapshot<T extends CapabilityEvidenceValue> =
  T extends null | boolean | string | number
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

export interface AvailableCapabilityEvidence<T extends CapabilityEvidenceValue>
  extends CapabilityEvidenceMetadata {
  readonly state: "available";
  readonly value: CapabilityEvidenceSnapshot<T>;
  readonly observedAt: Rfc3339Instant;
}

export interface UnavailableCapabilityEvidence
  extends CapabilityEvidenceMetadata {
  readonly state: Exclude<CapabilityState, "available">;
  readonly safeReason: CapabilitySafeReason;
  readonly observedAt: Rfc3339Instant;
}

export type CapabilityEvidence<T extends CapabilityEvidenceValue> =
  | AvailableCapabilityEvidence<T>
  | UnavailableCapabilityEvidence;

export interface AvailableCapabilitySummary
  extends CapabilityEvidenceMetadata {
  readonly state: "available";
  readonly observedAt: Rfc3339Instant;
}

export interface UnavailableCapabilitySummary
  extends CapabilityEvidenceMetadata {
  readonly state: Exclude<CapabilityState, "available">;
  readonly safeReason: CapabilitySafeReason;
  readonly observedAt: Rfc3339Instant;
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

const RFC3339_INSTANT =
  /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,3}))?(Z|([+-])(\d{2}):(\d{2}))$/;

function isLeapYear(year: number): boolean {
  return year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
}

function daysInMonth(year: number, month: number): number {
  const days = [31, isLeapYear(year) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  return days[month - 1] ?? 0;
}

export function rfc3339Instant(value: string): Rfc3339Instant {
  const match = RFC3339_INSTANT.exec(value);
  if (match === null) {
    throw new TypeError(
      "Capability observation time must be an RFC3339 instant.",
    );
  }

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
    throw new TypeError(
      "Capability observation time must be a valid RFC3339 instant.",
    );
  }

  const milliseconds = Number(fractionText.padEnd(3, "0"));
  const utc = new Date(0);
  utc.setUTCFullYear(year, month - 1, day);
  utc.setUTCHours(hour, minute, second, milliseconds);
  if (zone !== "Z") {
    const offset =
      (offsetHour * 60 + offsetMinute) *
      60_000 *
      (offsetSign === "+" ? 1 : -1);
    utc.setTime(utc.getTime() - offset);
  }

  const normalized = utc.toISOString();
  if (!/^\d{4}-/.test(normalized)) {
    throw new TypeError(
      "Capability observation time is outside the supported RFC3339 range.",
    );
  }
  return normalized as Rfc3339Instant;
}

function snapshotCapabilityValue<T extends CapabilityEvidenceValue>(
  value: T,
  seen = new Set<object>(),
): CapabilityEvidenceSnapshot<T> {
  if (typeof value === "number" && !Number.isFinite(value)) {
    throw new TypeError("Capability evidence numbers must be finite.");
  }
  if (value === null || typeof value !== "object") {
    return value as CapabilityEvidenceSnapshot<T>;
  }
  if (seen.has(value)) {
    throw new TypeError("Capability evidence values must not contain cycles.");
  }
  seen.add(value);

  if (Array.isArray(value)) {
    const snapshot = value.map((entry) =>
      snapshotCapabilityValue(entry, seen),
    );
    seen.delete(value);
    return Object.freeze(snapshot) as CapabilityEvidenceSnapshot<T>;
  }

  const prototype = Object.getPrototypeOf(value);
  if (prototype !== Object.prototype && prototype !== null) {
    throw new TypeError(
      "Capability evidence objects must be plain records.",
    );
  }
  const snapshot = Object.fromEntries(
    Object.entries(value).map(([key, entry]) => [
      key,
      snapshotCapabilityValue(entry, seen),
    ]),
  );
  seen.delete(value);
  return Object.freeze(snapshot) as CapabilityEvidenceSnapshot<T>;
}

export function availableCapability<T extends CapabilityEvidenceValue>(
  value: T,
  metadata: CapabilityEvidenceMetadata,
): AvailableCapabilityEvidence<T> {
  return Object.freeze({
    state: "available",
    value: snapshotCapabilityValue(value),
    observedAt: rfc3339Instant(metadata.observedAt),
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
    observedAt: rfc3339Instant(metadata.observedAt),
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

export function isCapabilityAvailable<T extends CapabilityEvidenceValue>(
  evidence: CapabilityEvidence<T>,
): evidence is AvailableCapabilityEvidence<T> {
  return evidence.state === "available";
}

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
