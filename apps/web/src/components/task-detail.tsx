import type { RefObject } from "react";

import { ApprovalCard } from "./approval-card";
import { ConnectionState } from "./connection-state";
import { EvidencePanel } from "./evidence-panel";
import { PlanReviewCard } from "./plan-review-card";
import { RunTimeline } from "./run-timeline";
import { StatusPill } from "./status-pill";
import type {
  ActiveInterrupt,
  ConnectionState as StreamConnectionState,
  DecisionInput,
  EvidenceRecord,
  PlanUpdateInput,
  ProposedPlan,
  TaskDetail as TaskDetailType,
  TaskEvent,
  TaskSummary,
} from "../lib/task-types";

interface TaskDetailProps {
  actionError?: string;
  activeInterrupt?: ActiveInterrupt;
  connectionState: StreamConnectionState;
  detail?: TaskDetailType;
  detailError?: string;
  detailRef: RefObject<HTMLElement | null>;
  events: readonly TaskEvent[];
  onDecide: (input: DecisionInput) => Promise<void>;
  onUpdatePlan: (input: PlanUpdateInput) => Promise<boolean>;
  plan?: ProposedPlan;
  planError?: string;
  evidence: readonly EvidenceRecord[];
  selected?: TaskSummary;
  streamError?: string;
  submittedDecision?: DecisionInput["decision"];
  submittingDecision: boolean;
  updatingPlan: boolean;
}

export function TaskDetail({
  actionError,
  activeInterrupt,
  connectionState,
  detail,
  detailError,
  detailRef,
  events,
  evidence,
  onDecide,
  onUpdatePlan,
  plan,
  planError,
  selected,
  streamError,
  submittedDecision,
  submittingDecision,
  updatingPlan,
}: TaskDetailProps) {
  const task = detail ?? selected;

  if (!task) {
    return (
      <section className="task-detail empty-detail" aria-labelledby="empty-heading">
        <div className="empty-detail-art" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <p className="eyebrow">Ready when you are</p>
        <h2 id="empty-heading">Your run will unfold here</h2>
        <p>
          Create a task above to watch its events arrive, review any approval request, and see the
          terminal result.
        </p>
      </section>
    );
  }

  const terminal =
    task.status === "completed" ||
    task.status === "rejected" ||
    task.status === "failed" ||
    task.status === "cancelled";

  return (
    <section
      className="task-detail"
      ref={detailRef}
      tabIndex={-1}
      aria-labelledby="task-detail-heading"
    >
      <header className="task-detail-header">
        <div>
          <p className="eyebrow">Selected task</p>
          <h2 id="task-detail-heading">{task.title}</h2>
          <div className="task-identifiers">
            <span>Task {task.taskId}</span>
            {task.runId ? <span>Run {task.runId}</span> : null}
          </div>
        </div>
        <div className="task-detail-status">
          <StatusPill status={task.status} />
          <ConnectionState state={connectionState} />
        </div>
      </header>

      {detailError ? (
        <div className="detail-notice" role="alert">
          <strong>Task details are temporarily unavailable.</strong>
          <span>{detailError} The live event stream is still being attempted.</span>
        </div>
      ) : null}
      {streamError ? (
        <div
          className="detail-notice reconnect-notice"
          role={connectionState === "reconnecting" ? "status" : "alert"}
        >
          <strong>
            {connectionState === "reconnecting" ? "Stream interrupted" : "Stream warning"}
          </strong>
          <span>{streamError}</span>
        </div>
      ) : null}

      {plan ? (
        <PlanReviewCard
          key={`${activeInterrupt?.interruptId ?? "readonly"}:${plan.revision}`}
          plan={plan}
          activeInterrupt={activeInterrupt}
          saving={updatingPlan}
          error={planError}
          onUpdate={onUpdatePlan}
        />
      ) : null}

      {activeInterrupt && !terminal ? (
        <ApprovalCard
          key={activeInterrupt.interruptId}
          interrupt={activeInterrupt}
          onDecide={onDecide}
          submitting={submittingDecision}
          submittedDecision={submittedDecision}
          error={actionError}
        />
      ) : null}

      <div className="run-section-heading">
        <div>
          <p className="eyebrow">Live activity</p>
          <h2>Run timeline</h2>
        </div>
        <span>{events.length} events</span>
      </div>

      <RunTimeline events={events} />

      <EvidencePanel evidence={evidence} />

      {terminal ? (
        <div className={`terminal-card terminal-${task.status}`} role="status" aria-live="polite">
          <span className="terminal-icon" aria-hidden="true">
            {task.status === "completed" ? "✓" : "×"}
          </span>
          <div>
            <strong>
              {task.status === "completed"
                ? "Run completed"
                : task.status === "rejected"
                  ? "Run rejected"
                  : "Run stopped"}
            </strong>
            <p>
              {detail?.result ??
                (task.status === "completed"
                  ? "The task reached a successful terminal event."
                  : "The task reached a terminal state without a successful result.")}
            </p>
          </div>
        </div>
      ) : null}
    </section>
  );
}
