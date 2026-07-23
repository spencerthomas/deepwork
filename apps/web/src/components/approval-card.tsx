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

export function ApprovalCard({
  error,
  interrupt,
  onDecide,
  submittedDecision,
  submitting,
}: ApprovalCardProps) {
  const [comment, setComment] = useState("");
  const commentLength = unicodeLength(comment);
  const commentId = useId();
  const disabled = submitting || submittedDecision !== undefined;

  async function decide(decision: DecisionInput["decision"]) {
    await onDecide({
      interruptId: interrupt.interruptId,
      decision,
      ...(comment.trim() ? { comment: comment.trim() } : {}),
    });
  }

  return (
    <aside className="approval-card" aria-labelledby="approval-heading">
      <div className="approval-icon" aria-hidden="true">
        !
      </div>
      <div className="approval-content">
        <p className="eyebrow">Human decision</p>
        <h3 id="approval-heading">{interrupt.title}</h3>
        <p>{interrupt.question}</p>

        <label htmlFor={commentId}>Optional note</label>
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
          placeholder="Add context for the run…"
          aria-describedby={`${commentId}-limit`}
        />
        <span id={`${commentId}-limit`} className="character-count">
          {commentLength.toLocaleString("en-US")} /{" "}
          {DECISION_COMMENT_MAX_LENGTH.toLocaleString("en-US")}
        </span>

        {error ? (
          <p className="decision-error" role="alert">
            {error}
          </p>
        ) : null}
        {submittedDecision ? (
          <p className="decision-pending" role="status">
            {submittedDecision === "approve" ? "Approval" : "Rejection"} accepted by the API.
            Waiting for the streamed decision record…
          </p>
        ) : null}

        <div className="approval-actions">
          <button
            className="secondary-button danger-button"
            type="button"
            disabled={disabled}
            onClick={() => void decide("reject")}
          >
            Reject
          </button>
          <button
            className="primary-button"
            type="button"
            disabled={disabled}
            onClick={() => void decide("approve")}
          >
            {submitting ? (
              <>
                <span className="button-spinner" aria-hidden="true" />
                Sending…
              </>
            ) : (
              "Approve and continue"
            )}
          </button>
        </div>
      </div>
    </aside>
  );
}
