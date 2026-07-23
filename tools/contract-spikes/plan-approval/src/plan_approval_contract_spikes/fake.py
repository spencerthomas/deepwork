from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Callable

from .contract import Authority, Boundary, Decision, DecisionType, PlanProposal, PlanStep
from .engine import PlanApprovalEngine
from .store import AppendOnlyCheckpointStore


TEMPLATE_BOUNDARIES = {
    "research": Boundary(
        permissions=("read_synthetic_sources", "write_synthetic_report"),
        side_effects=("write_synthetic_report",),
    ),
    "writing": Boundary(
        permissions=("read_synthetic_brief", "write_synthetic_draft"),
        side_effects=("write_synthetic_draft",),
    ),
    "coding": Boundary(
        permissions=("read_synthetic_repository", "write_synthetic_patch"),
        side_effects=("write_synthetic_patch",),
    ),
    "blank": Boundary(
        permissions=("read_synthetic_input", "write_synthetic_output"),
        side_effects=("write_synthetic_output",),
    ),
}


class NetworkDeniedFakeModel:
    """Deterministic model double with no network or provider adapter."""

    def propose(self, template: str) -> PlanProposal:
        return deterministic_plan(template)

    def approval_claim(self) -> str:
        return "Synthetic model text: the plan is approved."


def deterministic_plan(template: str = "research", revision: int = 1) -> PlanProposal:
    boundary = TEMPLATE_BOUNDARIES[template]
    authority = Authority(
        actor_id="actor-synthetic",
        workspace_id="workspace-synthetic",
        task_id=f"task-{template}-synthetic",
        run_id=f"run-{template}-synthetic",
        request_id=f"request-{template}-synthetic",
    )
    return PlanProposal(
        plan_id=f"plan-{template}-synthetic",
        schema_version="plan-proposal.v1",
        template_id=f"{template}-starter",
        template_version="synthetic-v1",
        config_version="synthetic-v1",
        created_at="2026-07-23T00:00:00Z",
        authority=authority,
        revision=revision,
        steps=(
            PlanStep("inspect", "Inspect synthetic inputs."),
            PlanStep(
                "produce",
                "Produce the bounded synthetic result.",
                protected_effects=boundary.side_effects,
            ),
        ),
        boundary=boundary,
        supersedes_revision=revision - 1 if revision > 1 else None,
    )


def normalized_decision(
    plan: PlanProposal,
    decision_type: DecisionType,
    *,
    decision_id: str | None = None,
    edited_plan: PlanProposal | None = None,
    message: str | None = None,
) -> Decision:
    return Decision(
        decision_id=decision_id or f"decision-{plan.revision}-{decision_type}",
        decision_type=decision_type,
        authority=plan.authority,
        plan_id=plan.plan_id,
        revision=plan.revision,
        observed_boundary=plan.boundary,
        upstream_validated=True,
        edited_plan=edited_plan,
        message=message,
    )


def restarted_engine(
    checkpoint: Path,
    *,
    task_boundary: Boundary,
    respond_permitted: bool = False,
    is_current_authority: Callable[[Authority], bool] = lambda _: True,
) -> PlanApprovalEngine:
    return PlanApprovalEngine(
        AppendOnlyCheckpointStore(checkpoint),
        task_boundary=task_boundary,
        respond_permitted=respond_permitted,
        is_current_authority=is_current_authority,
    )


def edited_revision(plan: PlanProposal, *, step_text: str) -> PlanProposal:
    return replace(
        plan,
        revision=plan.revision + 1,
        supersedes_revision=plan.revision,
        steps=(
            plan.steps[0],
            replace(plan.steps[1], text=step_text),
        ),
    )
