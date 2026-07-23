"use client";

import { ListChecks, PencilLine, Plus, Trash2, X } from "lucide-react";
import { useId, useState } from "react";

import { unicodeLength, validatePlanSteps } from "@/lib/task-normalizers";
import type { ActiveInterrupt, PlanUpdateInput, ProposedPlan } from "@/lib/task-types";
import { PLAN_STEP_MAX_COUNT, PLAN_STEP_MAX_LENGTH } from "@/lib/task-types";
import { cn } from "@/lib/utils";

interface PlanCardProps {
  plan: ProposedPlan;
  activeInterrupt?: ActiveInterrupt;
  error?: string;
  saving: boolean;
  onUpdate: (input: PlanUpdateInput) => Promise<boolean>;
}

/**
 * The proposed plan, editable only while the matching interrupt is pending at
 * the plan's exact revision — the same guard the API enforces.
 */
export function PlanCard({ plan, activeInterrupt, error, saving, onUpdate }: PlanCardProps) {
  const canEdit =
    activeInterrupt !== undefined && activeInterrupt.planRevision === plan.revision && !saving;
  const [editing, setEditing] = useState(false);
  const [steps, setSteps] = useState<string[]>([...plan.steps]);
  const [validationError, setValidationError] = useState<string>();
  const fieldId = useId();
  const errorId = `${fieldId}-error`;
  const shownError = validationError ?? error;

  function startEdit() {
    setSteps([...plan.steps]);
    setValidationError(undefined);
    setEditing(true);
  }

  async function save() {
    if (!activeInterrupt) return;
    try {
      validatePlanSteps(steps);
    } catch (issue) {
      setValidationError(issue instanceof Error ? issue.message : "The plan steps are invalid.");
      return;
    }
    setValidationError(undefined);
    const ok = await onUpdate({
      interruptId: activeInterrupt.interruptId,
      expectedRevision: plan.revision,
      steps,
    });
    if (ok) {
      setEditing(false);
    }
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-card">
      <div className="flex items-center gap-2.5 border-b border-border px-3.5 py-2.5">
        <ListChecks className="size-4 text-brand" />
        <span className="text-[13px] font-medium text-crisp">{plan.title || "Proposed plan"}</span>
        <span className="rounded-full bg-brand/10 px-2 py-0.5 font-mono text-[11px] text-brand">
          rev {plan.revision}
        </span>
        {canEdit && !editing && (
          <button
            type="button"
            onClick={startEdit}
            className="ml-auto flex items-center gap-1.5 rounded-lg border border-border px-2.5 py-1 text-[12px] font-medium text-foreground/80 transition-colors hover:bg-accent"
          >
            <PencilLine className="size-3.5" /> Edit plan
          </button>
        )}
        {editing && (
          <button
            type="button"
            onClick={() => setEditing(false)}
            className="ml-auto flex items-center gap-1.5 rounded-lg border border-border px-2.5 py-1 text-[12px] text-muted-foreground transition-colors hover:bg-accent"
          >
            <X className="size-3.5" /> Cancel
          </button>
        )}
      </div>

      {!editing ? (
        <ol className="space-y-1.5 px-4 py-3">
          {plan.steps.map((step, index) => (
            <li
              key={`${plan.revision}-${String(index)}`}
              className="flex gap-2.5 text-sm leading-relaxed"
            >
              <span className="mt-0.5 font-mono text-[11px] tabular-nums text-muted-foreground">
                {index + 1}.
              </span>
              <span className="text-foreground/90">{step}</span>
            </li>
          ))}
        </ol>
      ) : (
        <div className="space-y-2 px-4 py-3">
          {steps.map((step, index) => {
            // Length is measured the same way validatePlanSteps measures it — on
            // the raw value — so the visible/accessible state matches acceptance.
            const stepOverLimit = unicodeLength(step) > PLAN_STEP_MAX_LENGTH;
            const stepCountId = `${fieldId}-step-${String(index)}-count`;
            const stepDescribedBy =
              [stepOverLimit ? stepCountId : null, shownError !== undefined ? errorId : null]
                .filter((id): id is string => id !== null)
                .join(" ") || undefined;
            return (
              <div key={String(index)} className="flex items-start gap-2">
                <span className="mt-2.5 font-mono text-[11px] tabular-nums text-muted-foreground">
                  {index + 1}.
                </span>
                <div className="min-w-0 flex-1">
                  <textarea
                    value={step}
                    rows={2}
                    maxLength={PLAN_STEP_MAX_LENGTH * 2}
                    aria-label={`Plan step ${String(index + 1)}`}
                    aria-invalid={stepOverLimit}
                    aria-describedby={stepDescribedBy}
                    onChange={(event) =>
                      setSteps((current) =>
                        current.map((value, i) => (i === index ? event.target.value : value)),
                      )
                    }
                    className={cn(
                      "w-full resize-y rounded-lg border bg-background px-2.5 py-1.5 text-sm outline-none focus-visible:border-ring",
                      stepOverLimit ? "border-status-failed" : "border-input",
                    )}
                  />
                  {stepOverLimit && (
                    <p
                      id={stepCountId}
                      className="mt-1 text-[11px] tabular-nums text-status-failed"
                    >
                      {unicodeLength(step).toLocaleString()} /{" "}
                      {PLAN_STEP_MAX_LENGTH.toLocaleString()}
                    </p>
                  )}
                </div>
                <button
                  type="button"
                  aria-label={`Remove step ${String(index + 1)}`}
                  disabled={steps.length <= 1}
                  onClick={() => setSteps((current) => current.filter((_, i) => i !== index))}
                  className="mt-1.5 flex size-7 shrink-0 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:pointer-events-none disabled:opacity-40"
                >
                  <Trash2 className="size-3.5" />
                </button>
              </div>
            );
          })}
          <div className="flex items-center gap-2 pt-1">
            <button
              type="button"
              disabled={steps.length >= PLAN_STEP_MAX_COUNT}
              onClick={() => setSteps((current) => [...current, ""])}
              className="flex items-center gap-1 rounded-lg border border-border px-2.5 py-1 text-[12px] text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:pointer-events-none disabled:opacity-40"
            >
              <Plus className="size-3.5" /> Add step
            </button>
            <span className="text-[11px] tabular-nums text-muted-foreground">
              {steps.length} / {PLAN_STEP_MAX_COUNT} steps
            </span>
            <button
              type="button"
              disabled={saving}
              onClick={() => void save()}
              className={cn(
                "ml-auto rounded-lg bg-brand px-3 py-1.5 text-[12px] font-medium text-brand-foreground transition-colors hover:bg-brand/90",
                saving && "pointer-events-none opacity-60",
              )}
            >
              {saving ? "Saving…" : "Save plan"}
            </button>
          </div>
        </div>
      )}

      {plan.evidenceRefs.length > 0 && !editing && (
        <div className="border-t border-border px-4 py-2">
          <p className="font-mono text-[11px] text-muted-foreground">
            evidence: {plan.evidenceRefs.join(", ")}
          </p>
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
