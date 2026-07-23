/**
 * Pure derivation of the /agents fleet cards from real runtime data.
 *
 * Honesty rules (docs/DESIGN.md): only the two real agents appear, states come
 * from reported capabilities, and a missing/failed status yields "unknown" —
 * never a fabricated active state.
 */

import { CAPABILITY_NAMES, capabilityState, type DemoStatus } from "./demo-status";

export type AgentCardState = "active" | "inactive" | "gated" | "unknown";

export interface AgentCardModel {
  id: string;
  name: string;
  description: string;
  /** Capability whose reported state drives this card. */
  capabilityName: string;
  state: AgentCardState;
  stateLabel: string;
  /** Present only when the agent is actually configurable here. */
  configureHref?: string;
  /** Shown next to the disabled affordance when the agent is not selectable. */
  gatedExplanation?: string;
}

const LOCAL_STATE: Record<"available" | "unavailable" | "unknown", [AgentCardState, string]> = {
  available: ["active", "Active"],
  unavailable: ["inactive", "Unavailable"],
  unknown: ["unknown", "Unknown"],
};

export function deriveAgentCards(status: DemoStatus | undefined): AgentCardModel[] {
  const localCapability = capabilityState(status, CAPABILITY_NAMES.localTaskLoop);
  const [localState, localLabel] = LOCAL_STATE[localCapability];

  const sourcesCapability = capabilityState(status, CAPABILITY_NAMES.sources);
  const sourcesUnknown = sourcesCapability === "unknown";

  return [
    {
      id: "local",
      name: "Local deterministic runner",
      description:
        "Plans, pauses for approval, and produces an evidence-backed brief. Runs embedded in the local API.",
      capabilityName: CAPABILITY_NAMES.localTaskLoop,
      state: localState,
      stateLabel: localLabel,
      configureHref: "/agents/local",
    },
    {
      id: "classic-langsmith",
      name: "Classic LangSmith deployment",
      description:
        "Requires an explicitly configured Agent Server and reviewed evidence. Not selectable in the local product.",
      capabilityName: CAPABILITY_NAMES.sources,
      state: sourcesUnknown ? "unknown" : "gated",
      stateLabel: sourcesUnknown ? "Unknown" : "Gated",
      gatedExplanation: sourcesUnknown
        ? "The runtime did not report the sources capability, so this deployment stays gated."
        : "The sources capability is unavailable in the local runtime, so nothing can be configured here.",
    },
  ];
}

export function activeAgentCount(cards: readonly AgentCardModel[]): number {
  return cards.filter((card) => card.state === "active").length;
}
