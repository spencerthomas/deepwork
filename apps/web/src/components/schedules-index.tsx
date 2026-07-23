"use client";

import { AppHeader } from "./app-header";
import { taskClient } from "../lib/task-client";

/** The honest reason scheduling cannot run in this local product. */
export const SCHEDULES_UNAVAILABLE_REASON =
  "Scheduling requires a connected source with a proven schedule capability. This local product has no such source, so scheduled runs cannot be created and none are shown.";

export function SchedulesIndex() {
  return (
    <div className="app-shell">
      <AppHeader
        mode={taskClient.mode}
        apiBaseUrl={taskClient.apiBaseUrl}
        activePath="/schedules"
      />
      <main id="main-content" className="main-content">
        <header className="page-header">
          <div>
            <p className="eyebrow">Workspace · local / product</p>
            <h1>Schedules</h1>
            <p>
              Recurring and deferred runs live here once a source that supports them is connected.
              Until then the destination stays honest about what it can do.
            </p>
          </div>
        </header>

        <section className="task-list-panel" aria-labelledby="schedules-heading">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Automated runs</p>
              <h2 id="schedules-heading">Scheduled runs</h2>
            </div>
            <span className="capability-state is-unavailable">
              <span className="capability-state-dot" aria-hidden="true" />
              Unavailable
            </span>
          </div>

          <div className="empty-list">
            <span className="empty-list-icon" aria-hidden="true">
              ◷
            </span>
            <strong>Scheduling is unavailable</strong>
            <p>{SCHEDULES_UNAVAILABLE_REASON}</p>
            <p>
              You can still run work now from <a href="/">Tasks</a>.
            </p>
          </div>
        </section>
      </main>
      <footer className="app-footer">
        <span>deepwork</span>
        <span>Human-supervised local task execution · external providers unavailable</span>
      </footer>
    </div>
  );
}
