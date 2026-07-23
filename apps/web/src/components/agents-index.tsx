"use client";

import { AppHeader } from "./app-header";
import { taskClient } from "../lib/task-client";

/** Whether a source can run work in this local product, or is held behind a gate. */
export type AgentSourceState = "available" | "unavailable";

export interface AgentSource {
  id: string;
  name: string;
  runtime: string;
  state: AgentSourceState;
  detail: string;
}

/**
 * The honest capability posture of this local product: exactly the local
 * fixture runtime runs work; every external source is gated off until its
 * capability is proven. These mirror the fixed reality the API's demo status
 * reports and never advertise a fabricated connection.
 */
export const AGENT_SOURCES: readonly AgentSource[] = [
  {
    id: "local-fixture",
    name: "Local agent",
    runtime: "Deterministic local fixture",
    state: "available",
    detail:
      "Runs credential-free deterministic tasks in this session, including editable plans, ordered approvals, and streamed evidence. No model or provider credentials are used.",
  },
  {
    id: "classic-langsmith",
    name: "Classic LangSmith Deployment",
    runtime: "Public v1 runtime baseline",
    state: "unavailable",
    detail:
      "The supported public baseline for v1. Connecting a real deployment needs authenticated source configuration, which this local product does not enable.",
  },
  {
    id: "managed-deep-agents",
    name: "Managed Deep Agents",
    runtime: "Capability-gated adapter",
    state: "unavailable",
    detail:
      "A private-beta capability adapter. It stays unavailable until a capability spike proves an entitled account, so no fabricated connection is shown here.",
  },
  {
    id: "fleet",
    name: "Fleet",
    runtime: "Capability-gated adapter",
    state: "unavailable",
    detail:
      "Connect, read, and invoke support is enabled only where pinned live evidence proves the capability. It is unavailable in this local product.",
  },
];

/** The number of sources that can currently run work. */
export function countAvailableSources(sources: readonly AgentSource[]): number {
  return sources.filter((source) => source.state === "available").length;
}

const STATE_LABEL: Record<AgentSourceState, string> = {
  available: "Available",
  unavailable: "Unavailable",
};

export function AgentsIndex() {
  const available = countAvailableSources(AGENT_SOURCES);
  const countLabel = `${available} of ${AGENT_SOURCES.length} sources available`;

  return (
    <div className="app-shell">
      <AppHeader mode={taskClient.mode} apiBaseUrl={taskClient.apiBaseUrl} activePath="/agents" />
      <main id="main-content" className="main-content">
        <header className="page-header">
          <div>
            <p className="eyebrow">Workspace · local / product</p>
            <h1>Agents</h1>
            <p>
              The agent sources Deep Work can run work through, and their honest availability. A
              source that is not proven stays explicitly unavailable rather than appearing
              connected.
            </p>
          </div>
        </header>

        <section className="task-list-panel" aria-labelledby="agents-heading">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Runtime sources</p>
              <h2 id="agents-heading">Agent sources</h2>
            </div>
            <span className="task-count" aria-label={countLabel}>
              {available}/{AGENT_SOURCES.length}
            </span>
          </div>

          <p className="inbox-scope-note">
            External providers, authentication, and durable runtimes are unavailable in this local
            product. These states describe this session only.
          </p>

          <ul className="capability-list">
            {AGENT_SOURCES.map((source) => (
              <li className="capability-row" key={source.id}>
                <div className="capability-copy">
                  <span className="capability-title">
                    <strong>{source.name}</strong>
                    <span className="capability-runtime">{source.runtime}</span>
                  </span>
                  <p className="capability-detail">{source.detail}</p>
                </div>
                <span className={`capability-state is-${source.state}`}>
                  <span className="capability-state-dot" aria-hidden="true" />
                  {STATE_LABEL[source.state]}
                </span>
              </li>
            ))}
          </ul>
        </section>
      </main>
      <footer className="app-footer">
        <span>deepwork</span>
        <span>Human-supervised local task execution · external providers unavailable</span>
      </footer>
    </div>
  );
}
