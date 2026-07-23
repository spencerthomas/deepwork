/**
 * Pure derivation of the /agents fleet cards from real runtime data.
 *
 * Honesty rules (docs/DESIGN.md): only the two real agents appear, states come
 * from reported capabilities, and a missing/failed status yields "unknown" —
 * never a fabricated active state.
 */

import { CAPABILITY_NAMES, capabilityState, type DemoStatus } from "./demo-status";
import type { ClientMode } from "./task-types";

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

export interface AgentRuntimeCopy {
  name: string;
  description: string;
  fleetDescription: string;
  contractDescription: string;
  executionTitle: string;
  executionDetail: string;
  contractFooter: string;
}

const LOCAL_STATE: Record<"available" | "unavailable" | "unknown", [AgentCardState, string]> = {
  available: ["active", "Active"],
  unavailable: ["inactive", "Unavailable"],
  unknown: ["unknown", "Unknown"],
};

/**
 * Describe only what the selected browser adapter establishes. API mode never
 * identifies the server-side runner or provider configuration.
 */
export function agentRuntimeCopy(mode: ClientMode): AgentRuntimeCopy {
  if (mode === "fixture") {
    return {
      name: "In-browser fixture runner",
      description:
        "Plans, pauses for approval, and produces an evidence-backed brief inside the deterministic in-browser fixture adapter.",
      fleetDescription:
        "The execution capabilities this browser can verify. Fixture mode uses deterministic in-browser data with no external providers.",
      contractDescription:
        "The behavior contract of the in-browser fixture adapter. It is fixed, not configurable.",
      executionTitle: "Executes fixture steps deterministically",
      executionDetail:
        "Work stays in the credential-free in-browser fixture adapter. No network or external providers are involved.",
      contractFooter: "read-only fixture contract · runs in this browser",
    };
  }

  return {
    name: "API task runner",
    description:
      "Tasks are sent through the configured API. Its backend runner and provider configuration are unknown to this client.",
    fleetDescription:
      "Execution capabilities reported to this browser. API mode does not identify the server-side runner or provider configuration.",
    contractDescription:
      "The behavior contract exposed by the task API. Its backend implementation is not configurable here.",
    executionTitle: "Uses the reported API behavior",
    executionDetail:
      "Tasks are sent through the configured API. The backend runner and provider configuration are unknown to this client.",
    contractFooter: "read-only client contract · backend runner unknown",
  };
}

export function deriveAgentCards(
  status: DemoStatus | undefined,
  mode: ClientMode,
): AgentCardModel[] {
  const localCapability = capabilityState(status, CAPABILITY_NAMES.localTaskLoop);
  const [localState, localLabel] = LOCAL_STATE[localCapability];
  const runtimeCopy = agentRuntimeCopy(mode);

  const sourcesCapability = capabilityState(status, CAPABILITY_NAMES.sources);
  const sourcesUnknown = sourcesCapability === "unknown";

  return [
    {
      id: "local",
      name: runtimeCopy.name,
      description: runtimeCopy.description,
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
        : status?.source === "fixture"
          ? "The in-browser fixture reports sources unavailable, so nothing can be configured here."
          : "The runtime reports sources unavailable, so nothing can be configured here.",
    },
  ];
}

export function activeAgentCount(cards: readonly AgentCardModel[]): number {
  return cards.filter((card) => card.state === "active").length;
}

/**
 * Honest label for the local runner's session task count. A failed task-list
 * fetch leaves the store's task list empty, so reporting `tasks.length` would
 * fabricate "0 tasks this session"; surface the failure instead, and pluralize
 * the count correctly.
 */
export function agentSessionTaskLabel(
  loadingTasks: boolean,
  taskCount: number,
  listError?: string,
): string {
  if (loadingTasks) {
    return "Loading tasks…";
  }
  if (listError !== undefined) {
    return "Task count unavailable";
  }
  return `${taskCount} ${taskCount === 1 ? "task" : "tasks"} this session`;
}
