"use client";

import { Check, MessageSquareReply, ShieldQuestion, X } from "lucide-react";
import { useState } from "react";

import { unicodeLength, validateDecisionComment } from "@/lib/task-normalizers";
import type { ActiveInterrupt, DecisionInput } from "@/lib/task-types";
import { DECISION_COMMENT_MAX_LENGTH } from "@/lib/task-types";
import { cn } from "@/lib/utils";

interface ApprovalCardProps {
  interrupt: ActiveInterrupt;
  submitting: boolean;
  submittedDecision?: DecisionInput["decision"];
  error?: string;
  onDecide: (input: DecisionInput) => Promise<void>;
}

/**
 * The HITL decision card. Only the verbs the interrupt itself advertises are
 * rendered; respond requires a comment, matching the API contract.
 */
export function ApprovalCard({
  interrupt,
  submitting,
  submittedDecision,
  error,
  onDecide,
}: ApprovalCardProps) {
  const [comment, setComment] = useState("");
  const [validationError, setValidationError] = useState<string>();
  const disabled = submitting || submittedDecision !== undefined;
  const overLimit = unicodeLength(comment) > DECISION_COMMENT_MAX_LENGTH;
  const shownError = validationError ?? error;
  const countId = `comment-count-${interrupt.interruptId}`;
  const errorId = `decision-error-${interrupt.interruptId}`;
  const commentDescribedBy = [countId, shownError !== undefined ? errorId : null]
    .filter((id): id is string => id !== null)
    .join(" ");

  async function decide(decision: DecisionInput["decision"]) {
    const trimmed = comment.trim() === "" ? undefined : comment;
    if (decision === "respond" && trimmed === undefined) {
      setValidationError("A response needs a comment so the agent knows how to revise the plan.");
      return;
    }
    if (trimmed !== undefined) {
      try {
        validateDecisionComment(trimmed);
      } catch (issue) {
        setValidationError(issue instanceof Error ? issue.message : "The comment is invalid.");
        return;
      }
    }
    setValidationError(undefined);
    await onDecide({
      interruptId: interrupt.interruptId,
      decision,
      ...(trimmed !== undefined ? { comment: trimmed } : {}),
    });
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-status-review/40 bg-status-review-bg">
      <div className="flex items-start gap-2.5 px-4 py-3">
        <ShieldQuestion className="mt-0.5 size-4 shrink-0 text-status-review" />
        <div className="min-w-0 flex-1">
          <p className="label-caps text-status-review">Needs review</p>
          <p className="mt-1 text-sm font-medium text-foreground">{interrupt.title}</p>
          <p className="mt-1 text-sm leading-relaxed text-foreground/80">{interrupt.question}</p>
          <p className="mt-1 font-mono text-[11px] text-muted-foreground">
            {interrupt.interruptId}
          </p>
        </div>
      </div>

      {interrupt.decisions.length === 0 ? (
        <div className="border-t border-status-review/30 px-4 py-3">
          <p className="text-[13px] text-muted-foreground">
            This interruption offers no decisions. Wait for the run to continue or reload the task.
          </p>
        </div>
      ) : (
        <div className="border-t border-status-review/30 bg-card/60 px-4 py-3">
          <label
            htmlFor={`comment-${interrupt.interruptId}`}
            className="mb-1.5 block text-[11px] font-semibold uppercase tracking-wide text-muted-foreground"
          >
            Comment{" "}
            <span className="font-normal normal-case">
              (required for respond, optional otherwise — never echoed back)
            </span>
          </label>
          <textarea
            id={`comment-${interrupt.interruptId}`}
            value={comment}
            rows={2}
            disabled={disabled}
            maxLength={DECISION_COMMENT_MAX_LENGTH * 2}
            placeholder="Add context for your decision…"
            aria-invalid={validationError !== undefined || overLimit}
            aria-describedby={commentDescribedBy}
            onChange={(event) => {
              setComment(event.target.value);
              setValidationError(undefined);
            }}
            className="w-full resize-y rounded-lg border border-input bg-background px-2.5 py-1.5 text-sm outline-none focus-visible:border-ring disabled:opacity-60"
          />
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {interrupt.decisions.includes("approve") && (
              <button
                type="button"
                disabled={disabled}
                onClick={() => void decide("approve")}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg bg-brand px-3 py-1.5 text-[13px] font-medium text-brand-foreground transition-colors hover:bg-brand/90",
                  disabled && "pointer-events-none opacity-60",
                )}
              >
                <Check className="size-3.5" />
                {submittedDecision === "approve" ? "Approving…" : "Approve"}
              </button>
            )}
            {interrupt.decisions.includes("reject") && (
              <button
                type="button"
                disabled={disabled}
                onClick={() => void decide("reject")}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-1.5 text-[13px] font-medium text-foreground/80 transition-colors hover:bg-accent",
                  disabled && "pointer-events-none opacity-60",
                )}
              >
                <X className="size-3.5" />
                {submittedDecision === "reject" ? "Rejecting…" : "Reject"}
              </button>
            )}
            {interrupt.decisions.includes("respond") && (
              <button
                type="button"
                disabled={disabled}
                onClick={() => void decide("respond")}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-1.5 text-[13px] font-medium text-foreground/80 transition-colors hover:bg-accent",
                  disabled && "pointer-events-none opacity-60",
                )}
              >
                <MessageSquareReply className="size-3.5" />
                {submittedDecision === "respond" ? "Sending…" : "Respond"}
              </button>
            )}
            <span
              id={countId}
              className={cn(
                "ml-auto text-[11px] tabular-nums",
                overLimit ? "text-status-failed" : "text-muted-foreground",
              )}
            >
              {unicodeLength(comment).toLocaleString()} /{" "}
              {DECISION_COMMENT_MAX_LENGTH.toLocaleString()}
            </span>
          </div>
          {submittedDecision !== undefined && (
            <p className="mt-2 text-[13px] text-muted-foreground" role="status">
              Decision sent — waiting for confirmation…
            </p>
          )}
        </div>
      )}

      {shownError !== undefined && (
        <div
          id={errorId}
          className="border-t border-status-failed/30 bg-status-failed-bg px-4 py-2.5"
          role="alert"
        >
          <p className="text-[13px] text-status-failed">{shownError}</p>
        </div>
      )}
    </div>
  );
}
