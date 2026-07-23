"use client";

import { useId, useState } from "react";

import { unicodeLength } from "../lib/task-normalizers";
import {
  DECISION_COMMENT_MAX_LENGTH,
  type ActiveInterrupt,
  type DecisionInput,
} from "../lib/task-types";

interface ApprovalCardProps {
  error?: string;
  interrupt: ActiveInterrupt;
  onDecide: (input: DecisionInput) => Promise<void>;
  submittedDecision?: DecisionInput["decision"];
  submitting: boolean;
}

export function decisionActionLabel(
  decision: DecisionInput["decision"],
  pendingAction: DecisionInput["decision"] | undefined,
  submitting: boolean,
): string {
  if (submitting && pendingAction === decision) {
    return decision === "approve"
      ? "Sending approval…"
      : decision === "reject"
        ? "Sending rejection…"
        : "Sending response…";
  }
  return decision === "approve"
    ? "Approve and continue"
    : decision === "reject"
      ? "Reject"
      : "Send response";
}

export function ApprovalCard({
  error,
  interrupt,
  onDecide,
  submittedDecision,
  submitting,
}: ApprovalCardProps) {
  const [comment, setComment] = useState("");
  const [pendingAction, setPendingAction] = useState<DecisionInput["decision"]>();
  const commentLength = unicodeLength(comment);
  const commentId = useId();
  const disabled = submitting || submittedDecision !== undefined;
  const supports = (decision: DecisionInput["decision"]) => interrupt.decisions.includes(decision);

  async function decide(decision: DecisionInput["decision"]) {
    setPendingAction(decision);
    try {
      await onDecide({
        interruptId: interrupt.interruptId,
        decision,
        ...(comment.trim() ? { comment: comment.trim() } : {}),
      });
    } finally {
      setPendingAction(undefined);
    }
  }

  const pendingLabel = pendingAction
    ? decisionActionLabel(pendingAction, pendingAction, submitting)
    : undefined;

  return (
    <aside className="approval-card" aria-labelledby="approval-heading">
      <div className="approval-icon" aria-hidden="true">
        !
      </div>
      <div className="approval-content">
        <p className="eyebrow">Human decision</p>
        <h3 id="approval-heading">{interrupt.title}</h3>
        <p>{interrupt.question}</p>

        <label htmlFor={commentId}>
          {supports("respond") ? "Note or response" : "Optional note"}
        </label>
        <textarea
          id={commentId}
          rows={2}
          value={comment}
          disabled={disabled}
          onChange={(event) => {
            if (unicodeLength(event.target.value) <= DECISION_COMMENT_MAX_LENGTH) {
              setComment(event.target.value);
            }
          }}
          placeholder={
            supports("respond")
              ? "Add review context, or answer the agent’s request…"
              : "Add context for the run…"
          }
          aria-describedby={`${commentId}-help ${commentId}-limit`}
        />
        <span id={`${commentId}-help`} className="decision-help">
          {supports("respond")
            ? "A response is required only when answering the agent. Notes sent with approval or rejection are optional and are never streamed back."
            : "This note is optional and is never streamed back."}
        </span>
        <span id={`${commentId}-limit`} className="character-count">
          {commentLength.toLocaleString("en-US")} /{" "}
          {DECISION_COMMENT_MAX_LENGTH.toLocaleString("en-US")}
        </span>

        {error ? (
          <p className="decision-error" role="alert">
            {error}
          </p>
        ) : null}
        {submitting && pendingLabel ? (
          <p className="decision-pending" role="status" aria-live="polite">
            {pendingLabel}
          </p>
        ) : null}
        {submittedDecision ? (
          <p className="decision-pending" role="status">
            {submittedDecision === "approve"
              ? "Approval"
              : submittedDecision === "reject"
                ? "Rejection"
                : "Response"}{" "}
            accepted by the API. Waiting for the streamed decision record…
          </p>
        ) : null}

        <div className="approval-actions">
          {interrupt.decisions.length === 0 ? (
            <p className="decision-error" role="alert">
              This request did not advertise a supported decision. No action was invented.
            </p>
          ) : null}
          {supports("reject") ? (
            <button
              className="secondary-button danger-button"
              type="button"
              disabled={disabled}
              onClick={() => void decide("reject")}
            >
              {decisionActionLabel("reject", pendingAction, submitting)}
            </button>
          ) : null}
          {supports("respond") ? (
            <button
              className="secondary-button"
              type="button"
              disabled={disabled || comment.trim() === ""}
              onClick={() => void decide("respond")}
            >
              {decisionActionLabel("respond", pendingAction, submitting)}
            </button>
          ) : null}
          {supports("approve") ? (
            <button
              className="primary-button"
              type="button"
              disabled={disabled}
              onClick={() => void decide("approve")}
            >
              {submitting && pendingAction === "approve" ? (
                <>
                  <span className="button-spinner" aria-hidden="true" />
                  {decisionActionLabel("approve", pendingAction, submitting)}
                </>
              ) : (
                decisionActionLabel("approve", pendingAction, submitting)
              )}
            </button>
          ) : null}
        </div>
      </div>
    </aside>
  );
}
