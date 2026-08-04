import {
  CAPABILITY_STATES,
  type AvailableCapabilitySummary,
  type CapabilityState,
  type UnavailableCapabilitySummary,
} from "./capability.js";

export const SOURCE_PROBE_STATES = CAPABILITY_STATES;

export type SourceProbeState = CapabilityState;

interface SourceCapabilityIdentity {
  readonly name: string;
}

export type SourceCapabilityObservation = SourceCapabilityIdentity &
  (AvailableCapabilitySummary | UnavailableCapabilitySummary);

export interface SourceProbeResult {
  readonly kind: "langsmith_deployment";
  readonly state: SourceProbeState;
  readonly assistantId: string | null;
  readonly graphId: string | null;
  readonly reason: string;
  readonly saveAllowed: false;
  readonly capabilities: readonly SourceCapabilityObservation[];
}
