"use client";

import { Check, Code2, Pencil, ShieldQuestion, X } from "lucide-react";
import { useRef, useState } from "react";

import { ContractError, validateDecisionBatchInput } from "../../lib/task-normalizers";
import type {
  ActiveInterrupt,
  DecisionBatchInput,
  HitlDecisionType,
  OrderedDecision,
  ProposedPlan,
} from "../../lib/task-types";
import { cn } from "../../lib/utils";

interface OrderedApprovalBatchProps {
  error?: string;
  interrupt: ActiveInterrupt;
  onResolved?: (decisions: readonly OrderedDecision[]) => void;
  onSubmitError?: (message: string) => void;
  /** Returns a user-facing error on failure. */
  onSubmit: (input: DecisionBatchInput) => Promise<string | undefined>;
  plan?: ProposedPlan;
  submitting?: boolean;
}

function newIdempotencyKey(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `approval-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

const DECISION_LABELS: Record<HitlDecisionType, string> = {
  approve: "Approve",
  edit: "Edit",
  reject: "Reject",
  respond: "Respond",
};

/** React identity for state that belongs to one immutable reviewed batch version. */
export function orderedApprovalIdentity(interrupt: ActiveInterrupt): string {
  return JSON.stringify([interrupt.interruptId, interrupt.version ?? null]);
}

/**
 * One review form for a positional HITL batch. Repeated action names remain
 * separate rows, and every choice is checked against the config at that same
 * index before the vector can leave the browser.
 */
export function OrderedApprovalBatch({
  error: externalError,
  interrupt,
  onResolved,
  onSubmitError,
  onSubmit,
  plan,
  submitting = false,
}: OrderedApprovalBatchProps) {
  const actions = interrupt.actionRequests ?? [];
  const configs = interrupt.reviewConfigs ?? [];
  const [choices, setChoices] = useState<Array<HitlDecisionType | undefined>>(() =>
    configs.map(() => undefined),
  );
  const [drafts, setDrafts] = useState(() =>
    actions.map((action) => JSON.stringify(action.args, null, 2)),
  );
  const [messages, setMessages] = useState(() => actions.map(() => ""));
  const [localError, setLocalError] = useState<string>();
  const [pending, setPending] = useState(false);
  const submissionRef = useRef(false);
  const idempotencyRef = useRef(newIdempotencyKey());
  const disabled = submitting || pending;

  function invalidateSubmission() {
    idempotencyRef.current = newIdempotencyKey();
    setLocalError(undefined);
  }

  function buildDecisions(types = choices): OrderedDecision[] {
    return types.map((type, index) => {
      if (!type) throw new ContractError(`Choose a decision for action ${index + 1}.`);
      if (type === "approve") return { type };
      const message = messages[index]?.trim();
      if (type === "reject") return { type, ...(message ? { message } : {}) };
      if (type === "respond") return { type, message: message ?? "" };
      let args: unknown;
      try {
        args = JSON.parse(drafts[index] ?? "");
      } catch {
        throw new ContractError(`Edited action ${index + 1} must contain valid JSON arguments.`);
      }
      if (!args || typeof args !== "object" || Array.isArray(args)) {
        throw new ContractError(`Edited action ${index + 1} arguments must be a JSON object.`);
      }
      return {
        type: "edit",
        editedAction: { name: actions[index]?.name ?? "", args: args as never },
      };
    });
  }

  async function submit(types = choices) {
    if (submissionRef.current) return;
    let input: DecisionBatchInput;
    try {
      input = validateDecisionBatchInput(interrupt, {
        interruptId: interrupt.interruptId,
        expectedVersion: interrupt.version ?? "",
        idempotencyKey: idempotencyRef.current,
        decisions: buildDecisions(types),
      });
    } catch (issue) {
      setLocalError(issue instanceof Error ? issue.message : "The ordered decisions are invalid.");
      return;
    }
    submissionRef.current = true;
    setPending(true);
    setLocalError(undefined);
    try {
      const failure = await onSubmit(input);
      if (failure && onSubmitError) onSubmitError(failure);
      else if (failure) setLocalError(failure);
      else onResolved?.(input.decisions);
    } finally {
      submissionRef.current = false;
      setPending(false);
    }
  }

  return (
    <section
      className="overflow-hidden rounded-2xl border border-status-review/40 bg-status-review-bg"
      aria-label="Ordered approval batch"
    >
      <div className="flex items-start gap-2.5 px-4 py-3">
        <ShieldQuestion className="mt-0.5 size-4 shrink-0 text-status-review" />
        <div className="min-w-0 flex-1">
          <p className="label-caps text-status-review">Needs review · {actions.length} actions</p>
          <h3 className="mt-1 text-sm font-medium text-foreground">{interrupt.title}</h3>
          <p className="mt-1 text-sm leading-relaxed text-foreground/80">{interrupt.question}</p>
          <p className="mt-1 font-mono text-[11px] text-muted-foreground">
            {interrupt.version ? `approval version ${interrupt.version}` : interrupt.interruptId}
          </p>
        </div>
      </div>

      {plan && (
        <div className="border-t border-status-review/30 bg-card/35 px-4 py-2.5">
          <p className="text-xs font-medium text-foreground">{plan.title}</p>
          <p className="mt-0.5 text-[11px] text-muted-foreground">
            Plan revision {plan.revision} · review every action below in execution order.
          </p>
        </div>
      )}

      <ol className="divide-y divide-border border-y border-status-review/30 bg-card/60">
        {actions.map((action, index) => {
          const allowed = configs[index]?.allowedDecisions ?? [];
          const choice = choices[index];
          return (
            <li key={`${index}-${action.name}`} className="px-4 py-3">
              <div className="flex items-start gap-3">
                <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-accent font-mono text-[11px] font-semibold text-foreground">
                  {index + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <code className="text-xs font-semibold text-crisp">{action.name}</code>
                    {action.description && (
                      <span className="text-xs text-muted-foreground">{action.description}</span>
                    )}
                  </div>
                  <p className="mt-1 break-words text-[13px] leading-relaxed text-foreground/80">
                    {typeof action.args.text === "string"
                      ? action.args.text
                      : JSON.stringify(action.args)}
                  </p>
                  <div
                    className="mt-2 flex flex-wrap gap-1.5"
                    role="group"
                    aria-label={`Decision for action ${index + 1}`}
                  >
                    {allowed.map((type) => (
                      <button
                        key={type}
                        type="button"
                        disabled={disabled}
                        aria-pressed={choice === type}
                        onClick={() => {
                          setChoices((current) =>
                            current.map((item, itemIndex) => (itemIndex === index ? type : item)),
                          );
                          invalidateSubmission();
                        }}
                        className={cn(
                          "rounded-lg border px-2.5 py-1 text-xs font-medium transition-colors",
                          choice === type
                            ? "border-brand bg-card text-foreground shadow-sm ring-1 ring-brand/40"
                            : "border-border bg-card text-muted-foreground hover:bg-accent",
                        )}
                      >
                        {DECISION_LABELS[type]}
                      </button>
                    ))}
                  </div>
                  {choice === "edit" && (
                    <div className="mt-2 space-y-2">
                      {action.name === "execute_plan_step" &&
                      typeof action.args.position === "number" &&
                      typeof action.args.text === "string" ? (
                        <>
                          <label className="block text-xs font-medium text-muted-foreground">
                            Position for action {index + 1}
                            <input
                              value={action.args.position}
                              readOnly
                              aria-readonly="true"
                              className="mt-1 w-20 rounded-lg border border-input bg-muted px-2.5 py-2 font-mono text-xs text-muted-foreground"
                            />
                          </label>
                          <label className="block text-xs font-medium text-muted-foreground">
                            Edited step text for action {index + 1} · {action.name}
                            <textarea
                              rows={3}
                              value={(() => {
                                try {
                                  const parsed = JSON.parse(drafts[index] ?? "{}") as {
                                    text?: unknown;
                                  };
                                  return typeof parsed.text === "string" ? parsed.text : "";
                                } catch {
                                  return "";
                                }
                              })()}
                              disabled={disabled}
                              onChange={(event) => {
                                const text = event.target.value;
                                setDrafts((current) =>
                                  current.map((item, itemIndex) =>
                                    itemIndex === index
                                      ? JSON.stringify({ position: index + 1, text }, null, 2)
                                      : item,
                                  ),
                                );
                                invalidateSubmission();
                              }}
                              className="mt-1 w-full resize-y rounded-lg border border-input bg-background px-2.5 py-2 text-sm outline-none focus-visible:border-ring"
                            />
                          </label>
                        </>
                      ) : (
                        <label className="block text-xs font-medium text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Code2 className="size-3" /> Advanced JSON for action {index + 1} ·{" "}
                            {action.name}
                          </span>
                          <textarea
                            rows={6}
                            value={drafts[index]}
                            disabled={disabled}
                            onChange={(event) => {
                              setDrafts((current) =>
                                current.map((item, itemIndex) =>
                                  itemIndex === index ? event.target.value : item,
                                ),
                              );
                              invalidateSubmission();
                            }}
                            className="mt-1 min-h-40 w-full resize-y rounded-lg border border-input bg-background px-2.5 py-2 font-mono text-xs outline-none focus-visible:border-ring"
                          />
                        </label>
                      )}
                    </div>
                  )}
                  {(choice === "reject" || choice === "respond") && (
                    <label className="mt-2 block text-xs font-medium text-muted-foreground">
                      {choice === "respond" ? "Response" : "Optional reason"} for action {index + 1}
                      · {action.name}
                      <textarea
                        rows={2}
                        value={messages[index]}
                        disabled={disabled}
                        onChange={(event) => {
                          setMessages((current) =>
                            current.map((item, itemIndex) =>
                              itemIndex === index ? event.target.value : item,
                            ),
                          );
                          invalidateSubmission();
                        }}
                        className="mt-1 w-full resize-y rounded-lg border border-input bg-background px-2.5 py-2 text-sm outline-none focus-visible:border-ring"
                      />
                    </label>
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ol>

      <div className="px-4 py-3">
        <p className="text-xs text-muted-foreground">
          Batch summary: {choices.filter((choice) => choice === "approve").length} approve ·{" "}
          {choices.filter((choice) => choice === "edit").length} edit ·{" "}
          {choices.filter((choice) => choice === "reject").length} reject ·{" "}
          {choices.filter((choice) => choice === "respond").length} respond
          {choices.some((choice) => choice === undefined) && (
            <> · {choices.filter((choice) => choice === undefined).length} not reviewed</>
          )}
        </p>
        {(localError ?? externalError) && (
          <p role="alert" className="mt-2 text-[13px] font-medium text-status-failed">
            {localError ?? externalError}
          </p>
        )}
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            disabled={disabled || choices.some((choice) => choice === undefined)}
            onClick={() => void submit()}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-1.5 text-[13px] font-medium text-foreground hover:bg-accent disabled:opacity-60"
          >
            {choices.includes("edit") ? (
              <Pencil className="size-3.5" />
            ) : choices.includes("reject") ? (
              <X className="size-3.5" />
            ) : (
              <Check className="size-3.5" />
            )}
            Submit reviewed batch
          </button>
        </div>
      </div>
    </section>
  );
}
