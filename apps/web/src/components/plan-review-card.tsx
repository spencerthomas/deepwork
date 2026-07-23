"use client";

import { useEffect, useId, useRef, useState } from "react";

import {
  PLAN_STEP_MAX_COUNT,
  PLAN_STEP_MAX_LENGTH,
  type ActiveInterrupt,
  type PlanUpdateInput,
  type ProposedPlan,
} from "../lib/task-types";
import { unicodeLength, validatePlanSteps } from "../lib/task-normalizers";

interface PlanReviewCardProps {
  activeInterrupt?: ActiveInterrupt;
  error?: string;
  onUpdate: (input: PlanUpdateInput) => Promise<boolean>;
  plan: ProposedPlan;
  returnFocusId: string;
  saving: boolean;
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "The plan could not be validated.";
}

interface FocusTarget {
  focus(): void;
}

export function focusAfterRender(
  getTarget: () => FocusTarget | null,
  schedule: (callback: () => void) => void = (callback) => {
    globalThis.requestAnimationFrame(callback);
  },
): void {
  schedule(() => getTarget()?.focus());
}

export function PlanReviewCard({
  activeInterrupt,
  error,
  onUpdate,
  plan,
  returnFocusId,
  saving,
}: PlanReviewCardProps) {
  const [editing, setEditing] = useState(false);
  const [steps, setSteps] = useState<string[]>(plan.steps);
  const [validationError, setValidationError] = useState<string>();
  const firstStepRef = useRef<HTMLTextAreaElement | null>(null);
  const headingId = useId();
  const canEdit =
    activeInterrupt !== undefined && activeInterrupt.planRevision === plan.revision && !saving;

  useEffect(() => {
    if (editing) {
      focusAfterRender(() => firstStepRef.current);
    }
  }, [editing]);

  function focusReviewStatus() {
    focusAfterRender(() => document.getElementById(returnFocusId));
  }

  async function save() {
    if (!activeInterrupt) {
      return;
    }
    try {
      const validated = validatePlanSteps(steps);
      setValidationError(undefined);
      const saved = await onUpdate({
        interruptId: activeInterrupt.interruptId,
        expectedRevision: plan.revision,
        steps: validated,
      });
      if (saved) {
        setEditing(false);
        focusReviewStatus();
      }
    } catch (caught) {
      setValidationError(errorMessage(caught));
    }
  }

  return (
    <section className="plan-review-card" aria-labelledby={headingId}>
      <header className="plan-review-heading">
        <div>
          <p className="eyebrow">Review before execution</p>
          <h3 id={headingId}>{plan.title}</h3>
        </div>
        <span>Revision {plan.revision}</span>
      </header>

      {editing ? (
        <div className="plan-editor">
          <p className="plan-editor-help">
            Reorder by editing the numbered steps. Changes are saved only against this exact plan
            revision and approval request.
          </p>
          <ol>
            {steps.map((step, index) => {
              const inputId = `${headingId}-step-${index}`;
              return (
                <li key={inputId}>
                  <label htmlFor={inputId}>Step {index + 1}</label>
                  <textarea
                    ref={index === 0 ? firstStepRef : undefined}
                    id={inputId}
                    rows={2}
                    value={step}
                    disabled={saving}
                    onChange={(event) => {
                      const value = event.target.value;
                      if (unicodeLength(value) <= PLAN_STEP_MAX_LENGTH) {
                        setSteps((current) =>
                          current.map((item, itemIndex) => (itemIndex === index ? value : item)),
                        );
                      }
                    }}
                    aria-describedby={`${inputId}-limit`}
                  />
                  <div className="plan-step-controls">
                    <span id={`${inputId}-limit`} className="character-count">
                      {unicodeLength(step).toLocaleString("en-US")} /{" "}
                      {PLAN_STEP_MAX_LENGTH.toLocaleString("en-US")}
                    </span>
                    <button
                      className="text-button"
                      type="button"
                      disabled={saving || steps.length === 1}
                      onClick={() =>
                        setSteps((current) => current.filter((_, itemIndex) => itemIndex !== index))
                      }
                    >
                      Remove step
                    </button>
                  </div>
                </li>
              );
            })}
          </ol>
          {steps.length < PLAN_STEP_MAX_COUNT ? (
            <button
              className="secondary-button compact-button"
              type="button"
              disabled={saving}
              onClick={() => setSteps((current) => [...current, ""])}
            >
              Add step
            </button>
          ) : null}
          {validationError || error ? (
            <p className="decision-error" role="alert">
              {validationError ?? error}
            </p>
          ) : null}
          <div className="plan-editor-actions">
            <button
              className="secondary-button"
              type="button"
              disabled={saving}
              onClick={() => {
                setSteps(plan.steps);
                setEditing(false);
                setValidationError(undefined);
                focusReviewStatus();
              }}
            >
              Cancel
            </button>
            <button
              className="primary-button"
              type="button"
              disabled={saving}
              onClick={() => void save()}
            >
              {saving ? "Saving…" : "Save revised plan"}
            </button>
          </div>
        </div>
      ) : (
        <>
          <ol className="review-plan-steps">
            {plan.steps.map((step, index) => (
              <li key={`${index}:${step}`}>
                <span aria-hidden="true">{index + 1}</span>
                <p>{step}</p>
              </li>
            ))}
          </ol>
          <div className="plan-review-footer">
            <span>
              {plan.evidenceRefs.length > 0
                ? `${plan.evidenceRefs.length} evidence reference${plan.evidenceRefs.length === 1 ? "" : "s"}`
                : "No evidence references"}
            </span>
            {canEdit ? (
              <button className="secondary-button" type="button" onClick={() => setEditing(true)}>
                Edit plan
              </button>
            ) : (
              <span className="plan-readonly">
                {activeInterrupt ? "Waiting for the current plan revision" : "Read-only"}
              </span>
            )}
          </div>
          {error ? (
            <p className="decision-error" role="alert">
              {error}
            </p>
          ) : null}
        </>
      )}
    </section>
  );
}
