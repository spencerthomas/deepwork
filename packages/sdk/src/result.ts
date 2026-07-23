import type {
  CapabilitySafeReason,
  CapabilityState,
  UnavailableCapabilitySummary,
} from "@deepwork/domain";

export const SDK_ERROR_CATEGORIES = Object.freeze([
  "capability-unavailable",
  "permission-denied",
  "offline",
  "cancelled",
  "contract",
  "upstream",
  "unknown",
] as const);

export type SdkErrorCategory = (typeof SDK_ERROR_CATEGORIES)[number];

export interface SdkError {
  readonly category: SdkErrorCategory;
  readonly safeMessage: string;
  readonly retryable: boolean;
  readonly capability?: UnavailableCapabilitySummary;
}

export type SdkResult<T> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: SdkError };

export function capabilityUnavailableError(
  capability: UnavailableCapabilitySummary,
): SdkError {
  return Object.freeze({
    category:
      capability.state === "permission-denied"
        ? "permission-denied"
        : "capability-unavailable",
    safeMessage: unavailableMessage(
      capability.state,
      capability.safeReason,
    ),
    retryable: capability.safeReason === "source-unavailable",
    capability,
  });
}

function unavailableMessage(
  state: CapabilityState,
  reason: CapabilitySafeReason | undefined,
): string {
  if (state === "permission-denied" || reason === "permission-required") {
    return "This action requires additional permission.";
  }
  if (state === "unknown" || reason === "contract-not-verified") {
    return "This capability has not been verified.";
  }
  if (reason === "source-unavailable") {
    return "The source is currently unavailable.";
  }

  return "This capability is unavailable.";
}
