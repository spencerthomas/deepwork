"use client";

import { Check, ClipboardList, MessageSquare, ShieldQuestion, X } from "lucide-react";
import type { ComponentType } from "react";
import { useId, useState } from "react";

import { ContractError, unicodeLength, validateDecisionComment } from "../../lib/task-normalizers";
import type { ActiveInterrupt, DecisionInput, ProposedPlan } from "../../lib/task-types";
import { DECISION_COMMENT_MAX_LENGTH } from "../../lib/task-types";
import { cn } from "../../lib/utils";

import type { DecisionVerb } from "./approvals-model";
import { orderedDecisions, planPreview } from "./approvals-model";

interface VerbMeta {
  icon: ComponentType<{ className?: string }>;
  label: string;
  pendingLabel: string;
  primary?: boolean;
}

const VERB_META: Record<DecisionVerb, VerbMeta> = {
  approve: { icon: Check, label: "Approve", pendingLabel: "Approving…", primary: true },
  reject: { icon: X, label: "Reject", pendingLabel: "Rejecting…" },
  respond: { icon: MessageSquare, label: "Respond", pendingLabel: "Sending response…" },
};

export function decisionButtonLabel(verb: DecisionVerb, pending: boolean): string {
  return pending ? VERB_META[verb].pendingLabel : VERB_META[verb].label;
}

interface ApprovalDecisionPanelProps {
  interrupt: ActiveInterrupt;
  /** Returns an error message on failure, undefined on success. */
  onDecide: (input: DecisionInput) => Promise<string | undefined>;
  onResolved: (decision: DecisionVerb) => void;
  plan?: ProposedPlan;
}

/**
 * The interactive heart of one approvals row: the agent's question, a summary
 * of the proposed plan, an optional note (required for "respond"), and one
 * button per decision verb the interrupt itself advertises.
 */
export function ApprovalDecisionPanel({
  interrupt,
  onDecide,
  onResolved,
  plan,
}: ApprovalDecisionPanelProps) {
  const [comment, setComment] = useState("");
  const [pendingVerb, setPendingVerb] = useState<DecisionVerb>();
  const [error, setError] = useState<string>();
  const commentId = useId();

  const verbs = orderedDecisions(interrupt);
  const supportsRespond = verbs.includes("respond");
  const submitting = pendingVerb !== undefined;
  const preview = plan ? planPreview(plan) : undefined;

  async function submit(verb: DecisionVerb) {
    let normalizedComment: string | undefined;
    try {
      normalizedComment = validateDecisionComment(comment);
    } catch (validationError) {
      setError(
        validationError instanceof ContractError
          ? validationError.message
          : "The note could not be validated.",
      );
      return;
    }
    if (verb === "respond" && normalizedComment === undefined) {
      setError("A response is required when answering the agent’s request.");
      return;
    }

    setPendingVerb(verb);
    setError(undefined);
    const failure = await onDecide({
      interruptId: interrupt.interruptId,
      decision: verb,
      ...(normalizedComment === undefined ? {} : { comment: normalizedComment }),
    });
    setPendingVerb(undefined);
    if (failure !== undefined) {
      setError(failure);
    } else {
      setComment("");
      onResolved(verb);
    }
  }

  return (
    <div className="rounded-2xl border border-status-review/35 bg-status-review-bg/60 p-3.5">
      <div className="flex flex-wrap items-center gap-2">
        <ShieldQuestion className="size-4 text-status-review" />
        <span className="text-[11px] font-semibold uppercase tracking-wide text-status-review">
          Needs review
        </span>
        {interrupt.planRevision !== undefined && (
          <span className="ml-auto rounded-full bg-accent px-2 py-0.5 font-mono text-[11px] text-muted-foreground">
            plan rev {interrupt.planRevision}
          </span>
        )}
      </div>

      <p className="mt-2 text-sm font-medium text-crisp">{interrupt.title}</p>
      <p className="mt-1 text-[13px] leading-relaxed text-muted-foreground">{interrupt.question}</p>

      {plan && preview ? (
        <div className="mt-3 rounded-xl border border-border bg-card/70 p-3">
          <div className="flex flex-wrap items-center gap-2">
            <ClipboardList className="size-3.5 shrink-0 text-muted-foreground" />
            <span className="min-w-0 truncate text-xs font-medium text-crisp">{plan.title}</span>
            <span className="ml-auto rounded-full bg-accent px-2 py-0.5 font-mono text-[11px] text-muted-foreground">
              rev {plan.revision}
            </span>
          </div>
          <ol className="mt-2 space-y-1 font-mono text-xs leading-relaxed text-foreground/90">
            {preview.steps.map((step, index) => (
              <li key={`${index}-${step}`} className="truncate">
                {index + 1}. {step}
              </li>
            ))}
          </ol>
          {preview.remaining > 0 && (
            <p className="mt-1.5 font-mono text-[11px] text-muted-foreground">
              +{preview.remaining} more {preview.remaining === 1 ? "step" : "steps"} on the task
              page
            </p>
          )}
          {interrupt.planRevision !== undefined && interrupt.planRevision !== plan.revision && (
            <p className="mt-1.5 text-[11px] text-muted-foreground">
              This request references plan revision {interrupt.planRevision}; revision{" "}
              {plan.revision} is shown.
            </p>
          )}
        </div>
      ) : (
        <p className="mt-2 text-xs text-muted-foreground">
          The API returned no proposed plan for this interruption — open the task for full context.
        </p>
      )}

      <div className="mt-3">
        <label htmlFor={commentId} className="text-xs font-medium text-muted-foreground">
          {supportsRespond ? "Response or note" : "Optional note"}
        </label>
        <textarea
          id={commentId}
          rows={2}
          value={comment}
          disabled={submitting}
          onChange={(changeEvent) => {
            if (unicodeLength(changeEvent.target.value) <= DECISION_COMMENT_MAX_LENGTH) {
              setComment(changeEvent.target.value);
            }
          }}
          placeholder={
            supportsRespond
              ? "Answer the agent’s question, or add context…"
              : "Add context for this decision…"
          }
          aria-describedby={`${commentId}-help`}
          className="mt-1 w-full resize-y rounded-xl border border-input bg-card px-3 py-2 text-[13px] text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-2 focus:ring-ring/30 disabled:opacity-60"
        />
        <div className="flex items-baseline justify-between gap-2">
          <span id={`${commentId}-help`} className="text-[11px] text-muted-foreground">
            {supportsRespond
              ? "Required to respond; optional with approval or rejection."
              : "Optional; sent along with your decision."}
          </span>
          <span className="font-mono text-[11px] tabular-nums text-muted-foreground">
            {unicodeLength(comment).toLocaleString("en-US")}/
            {DECISION_COMMENT_MAX_LENGTH.toLocaleString("en-US")}
          </span>
        </div>
      </div>

      {error !== undefined && (
        <p role="alert" className="mt-2 text-[13px] font-medium text-status-failed">
          {error}
        </p>
      )}
      {pendingVerb !== undefined && (
        <p role="status" aria-live="polite" className="sr-only">
          {decisionButtonLabel(pendingVerb, true)}
        </p>
      )}

      {verbs.length === 0 ? (
        <p role="alert" className="mt-3 text-[13px] font-medium text-status-failed">
          This interruption did not advertise any decision, so no action was invented. Open the task
          for details.
        </p>
      ) : (
        <div className="mt-3 flex flex-wrap gap-2">
          {verbs.map((verb) => {
            const meta = VERB_META[verb];
            const Icon = meta.icon;
            const respondBlocked = verb === "respond" && comment.trim() === "";
            return (
              <button
                key={verb}
                type="button"
                disabled={submitting || respondBlocked}
                onClick={() => void submit(verb)}
                title={respondBlocked ? "Write a response first" : undefined}
                className={cn(
                  "flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-[13px] font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-55",
                  meta.primary
                    ? "bg-brand text-brand-foreground hover:bg-brand/90"
                    : "border border-border bg-card text-foreground hover:bg-accent",
                )}
              >
                <Icon className="size-3.5" />
                {decisionButtonLabel(verb, pendingVerb === verb)}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
