import type { ClientMode } from "../lib/task-types";

interface AppHeaderProps {
  apiBaseUrl: string;
  mode: ClientMode;
}

export function AppHeader({ apiBaseUrl, mode }: AppHeaderProps) {
  return (
    <>
      <header className="app-header">
        <a className="brand" href="#main-content" aria-label="Deep Work home">
          <span className="brand-mark" aria-hidden="true">
            <span />
          </span>
          <span className="brand-copy">
            <strong>Deep Work</strong>
            <span>Task runner</span>
          </span>
        </a>
        <div className={`api-target target-${mode}`} title={apiBaseUrl}>
          <span className="api-target-dot" aria-hidden="true" />
          <span>
            {mode === "fixture" ? "Deterministic local fixture" : `API target · ${apiBaseUrl}`}
          </span>
        </div>
      </header>
      {mode === "fixture" ? (
        <div className="fixture-banner" role="status">
          <strong>Fixture mode</strong>
          <span>
            Deterministic local execution. External providers are unavailable;
            no API or live-provider work is claimed.
          </span>
        </div>
      ) : (
        <div className="provider-disclosure" role="note">
          <strong>Local API transport</strong>
          <span>
            External providers are unavailable in this delivery. Stream health
            describes browser-to-local-API delivery only and never implies live
            provider execution.
          </span>
        </div>
      )}
    </>
  );
}
