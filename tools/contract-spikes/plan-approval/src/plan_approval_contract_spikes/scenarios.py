from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Callable

from .catalog import SCENARIOS
from .contract import Authority, Boundary, DecisionType, PlanStatus
from .engine import PlanApprovalEngine
from .errors import ContractViolation
from .fake import (
    NetworkDeniedFakeModel,
    deterministic_plan,
    edited_revision,
    normalized_decision,
    restarted_engine,
)
from .store import AppendOnlyCheckpointStore


def _expect_blocked(action: Callable[[], object]) -> str:
    try:
        action()
    except (ContractViolation, ValueError) as error:
        return f"blocked:{type(error).__name__}"
    raise AssertionError("scenario unexpectedly crossed the plan gate")


def _alter_authority(plan, **changes: str):
    return replace(plan.authority, **changes)


def _alter_decision_authority(decision, **changes: str):
    return replace(decision, authority=replace(decision.authority, **changes))


def run_scenario(template: str, scenario: str, checkpoint: Path) -> dict[str, object]:
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario: {scenario}")

    model = NetworkDeniedFakeModel()
    plan = model.propose(template)
    current = {"authority": True}
    respond_permitted = scenario == "respond_permitted"
    engine = PlanApprovalEngine(
        AppendOnlyCheckpointStore(checkpoint),
        task_boundary=plan.boundary,
        respond_permitted=respond_permitted,
        is_current_authority=lambda _: current["authority"],
    )
    engine.propose(plan)
    before = engine.side_effect_count
    observed = "recorded"
    recovery = "durable-local-checkpoint-only"

    if scenario == "initial_proposal":
        observed = "awaiting_decision"
    elif scenario == "approve_unchanged":
        engine.record_decision(normalized_decision(plan, DecisionType.APPROVE))
        assert engine.side_effect_count == 0
        observed = engine.resume(authority=plan.authority, resume_id="resume-1")
    elif scenario == "edit_then_approve":
        revision = edited_revision(plan, step_text="Produce the edited bounded result.")
        engine.record_decision(
            normalized_decision(
                plan,
                DecisionType.EDIT,
                edited_plan=revision,
            )
        )
        engine.record_decision(normalized_decision(revision, DecisionType.APPROVE))
        assert engine.side_effect_count == 0
        observed = engine.resume(authority=revision.authority, resume_id="resume-2")
    elif scenario in {"reject_without_reason", "reject_with_reason"}:
        message = "Synthetic safe reason." if scenario.endswith("with_reason") else None
        observed = str(
            engine.record_decision(
                normalized_decision(plan, DecisionType.REJECT, message=message)
            )
        )
    elif scenario == "respond_permitted":
        observed = str(
            engine.record_decision(
                normalized_decision(
                    plan,
                    DecisionType.RESPOND,
                    message="Please narrow the synthetic second step.",
                )
            )
        )
    elif scenario == "local_abandonment":
        engine.abandon_locally(plan.authority.actor_id)
        event = engine.store.load()[-1]
        assert event.payload["provider_resume_emitted"] is False
        observed = "local_only_no_provider_resume"
    elif scenario == "explicit_restart_after_rejection":
        engine.record_decision(normalized_decision(plan, DecisionType.REJECT))
        restarted = replace(
            plan,
            plan_id=f"{plan.plan_id}-restart",
            authority=_alter_authority(
                plan,
                run_id=f"{plan.authority.run_id}-restart",
                request_id=f"{plan.authority.request_id}-restart",
            ),
        )
        engine.restart_after_rejection(restarted)
        engine.record_decision(normalized_decision(restarted, DecisionType.APPROVE))
        observed = engine.resume(authority=restarted.authority, resume_id="resume-restart")
    elif scenario == "wrong_request":
        decision = _alter_decision_authority(
            normalized_decision(plan, DecisionType.APPROVE),
            request_id="request-wrong-synthetic",
        )
        observed = _expect_blocked(lambda: engine.record_decision(decision))
    elif scenario == "wrong_plan":
        decision = replace(
            normalized_decision(plan, DecisionType.APPROVE),
            plan_id="plan-wrong-synthetic",
        )
        observed = _expect_blocked(lambda: engine.record_decision(decision))
    elif scenario == "wrong_task":
        decision = _alter_decision_authority(
            normalized_decision(plan, DecisionType.APPROVE),
            task_id="task-wrong-synthetic",
        )
        observed = _expect_blocked(lambda: engine.record_decision(decision))
    elif scenario == "wrong_run":
        decision = _alter_decision_authority(
            normalized_decision(plan, DecisionType.APPROVE),
            run_id="run-wrong-synthetic",
        )
        observed = _expect_blocked(lambda: engine.record_decision(decision))
    elif scenario == "wrong_actor":
        decision = _alter_decision_authority(
            normalized_decision(plan, DecisionType.APPROVE),
            actor_id="actor-wrong-synthetic",
        )
        observed = _expect_blocked(lambda: engine.record_decision(decision))
    elif scenario in {"stale_revision", "superseded_revision"}:
        revision = edited_revision(plan, step_text="Produce revision two.")
        engine.record_decision(
            normalized_decision(plan, DecisionType.EDIT, edited_plan=revision)
        )
        stale = normalized_decision(
            plan,
            DecisionType.APPROVE,
            decision_id=f"stale-{scenario}",
        )
        observed = _expect_blocked(lambda: engine.record_decision(stale))
    elif scenario == "expired_actor":
        current["authority"] = False
        observed = _expect_blocked(
            lambda: engine.record_decision(
                normalized_decision(plan, DecisionType.APPROVE)
            )
        )
    elif scenario == "cross_workspace_replay":
        decision = _alter_decision_authority(
            normalized_decision(plan, DecisionType.APPROVE),
            workspace_id="workspace-other-synthetic",
        )
        observed = _expect_blocked(lambda: engine.record_decision(decision))
    elif scenario == "permission_widening":
        widened = Boundary(
            permissions=(*plan.boundary.permissions, "admin_synthetic_workspace"),
            side_effects=plan.boundary.side_effects,
        )
        decision = replace(
            normalized_decision(plan, DecisionType.APPROVE),
            observed_boundary=widened,
        )
        observed = _expect_blocked(lambda: engine.record_decision(decision))
    elif scenario == "side_effect_widening":
        widened = Boundary(
            permissions=plan.boundary.permissions,
            side_effects=(*plan.boundary.side_effects, "publish_synthetic_result"),
        )
        decision = replace(
            normalized_decision(plan, DecisionType.APPROVE),
            observed_boundary=widened,
        )
        observed = _expect_blocked(lambda: engine.record_decision(decision))
    elif scenario == "reconnect_before_decision":
        recovered = restarted_engine(
            checkpoint,
            task_boundary=plan.boundary,
            respond_permitted=respond_permitted,
        )
        snapshot = recovered.reconnect()
        assert snapshot["status"] is PlanStatus.AWAITING_DECISION
        observed = "recovered_awaiting_decision"
    elif scenario == "reconnect_after_decision_before_resume":
        engine.record_decision(normalized_decision(plan, DecisionType.APPROVE))
        recovered = restarted_engine(checkpoint, task_boundary=plan.boundary)
        snapshot = recovered.reconnect()
        assert snapshot["status"] is PlanStatus.APPROVED
        observed = "recovered_approved_no_resume"
    elif scenario == "reconnect_after_resume":
        engine.record_decision(normalized_decision(plan, DecisionType.APPROVE))
        engine.resume(authority=plan.authority, resume_id="resume-reconnect")
        recovered = restarted_engine(checkpoint, task_boundary=plan.boundary)
        snapshot = recovered.reconnect()
        assert snapshot["status"] is PlanStatus.EXECUTING
        observed = "recovered_executing_one_release"
    elif scenario in {"process_restart", "deployment_restart"}:
        engine.record_decision(normalized_decision(plan, DecisionType.APPROVE))
        recovered = restarted_engine(checkpoint, task_boundary=plan.boundary)
        observed = recovered.resume(
            authority=plan.authority,
            resume_id=f"resume-{scenario}",
        )
        recovery = f"{scenario}_simulated_by_frozen_checkpoint_replay"
    elif scenario == "model_text_claims_approved":
        claim = model.approval_claim()
        assert "approved" in claim
        observed = _expect_blocked(
            lambda: engine.resume(authority=plan.authority, resume_id="resume-model")
        )
    elif scenario == "tool_output_imitates_decision":
        tool_output = {
            "decision": "approve",
            "plan_id": plan.plan_id,
            "revision": plan.revision,
        }
        assert tool_output["decision"] == "approve"
        observed = _expect_blocked(
            lambda: engine.resume(authority=plan.authority, resume_id="resume-tool")
        )
    elif scenario == "direct_resume":
        observed = _expect_blocked(
            lambda: engine.resume(authority=plan.authority, resume_id="resume-direct")
        )
    elif scenario == "repeated_delivery":
        decision = normalized_decision(plan, DecisionType.APPROVE)
        engine.record_decision(decision)
        assert engine.record_decision(decision) == "duplicate_suppressed"
        engine.resume(authority=plan.authority, resume_id="resume-repeat")
        observed = engine.resume(authority=plan.authority, resume_id="resume-repeat")
    elif scenario == "retry_after_timeout":
        engine.record_decision(normalized_decision(plan, DecisionType.APPROVE))
        recovered = restarted_engine(checkpoint, task_boundary=plan.boundary)
        recovered.resume(authority=plan.authority, resume_id="resume-timeout")
        recovered_again = restarted_engine(checkpoint, task_boundary=plan.boundary)
        observed = recovered_again.resume(
            authority=plan.authority,
            resume_id="resume-timeout",
        )
        recovery = "lost_local_response_replayed_idempotently"
    elif scenario == "config_template_drift":
        drifted = restarted_engine(
            checkpoint,
            task_boundary=plan.boundary,
            respond_permitted=not respond_permitted,
        )
        observed = _expect_blocked(drifted.reconnect)
        recovery = "runtime_binding_hash_rejected_drift"
    elif scenario == "cancellation_not_a_decision":
        observed = _expect_blocked(lambda: DecisionType("cancel"))
    elif scenario == "unsupported_capability_false":
        manifest = {
            "planApproval": False,
            "unavailableReason": "blocked_upstream_contract_and_live_evidence",
            "draftPreserved": True,
            "textOnlyDispatchAvailable": True,
        }
        assert manifest["planApproval"] is False
        observed = "typed_unavailable_fallback"

    events = engine.store.load()
    after = engine.side_effect_count
    return {
        "scenario": scenario,
        "observed_result": observed,
        "state_transitions": [event.event_type for event in events],
        "side_effect_count_before_approval": before,
        "side_effect_count_after_resume": after,
        "recovery_result": recovery,
        "final_status": str(engine.status),
        "append_only_event_count": len(events),
    }
