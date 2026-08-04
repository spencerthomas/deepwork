import { CAPABILITY_STATES, type CapabilityState } from "./capability.js";

export const SOURCE_PROBE_STATES = CAPABILITY_STATES;

export type SourceProbeState = CapabilityState;

export interface SourceCapabilityObservation {
  readonly name: string;
  readonly state: SourceProbeState;
  readonly reason: string;
}

export interface SourceProbeResult {
  readonly kind: "langsmith_deployment";
  readonly state: SourceProbeState;
  readonly assistantId: string | null;
  readonly graphId: string | null;
  readonly reason: string;
  readonly saveAllowed: false;
  readonly capabilities: readonly SourceCapabilityObservation[];
}
