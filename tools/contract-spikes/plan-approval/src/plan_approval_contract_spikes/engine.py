from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from typing import Callable

from .contract import (
    Authority,
    Boundary,
    Decision,
    DecisionType,
    PlanProposal,
    PlanStatus,
)
from .errors import ContractViolation
from .store import AppendOnlyCheckpointStore


class PlanApprovalEngine:
    """Plan-specific offline state machine.

    Provider batching, stale-delivery behavior, and resume wire syntax are
    deliberately absent. The engine starts only after an upstream normalized
    decision has been validated.
    """

    def __init__(
        self,
        store: AppendOnlyCheckpointStore,
        *,
        task_boundary: Boundary,
        is_current_authority: Callable[[Authority], bool] = lambda _: True,
        respond_permitted: bool = False,
    ):
        task_boundary.validate()
        self.store = store
        self.task_boundary = task_boundary
        self.is_current_authority = is_current_authority
        self.respond_permitted = respond_permitted

    def _events(self):
        return self.store.load()

    def _runtime_binding(self) -> dict[str, object]:
        material = json.loads(json.dumps({
            "task_boundary": asdict(self.task_boundary),
            "respond_permitted": self.respond_permitted,
        }))
        digest = hashlib.sha256(
            json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return {"material": material, "sha256": digest}

    def _assert_runtime_binding(self) -> None:
        events = self._events()
        if not events:
            return
        if events[0].payload.get("runtime_binding") != self._runtime_binding():
            raise ContractViolation("runtime task/review config drifted from the proposal")

    @property
    def current_plan(self) -> PlanProposal | None:
        plan = None
        for event in self._events():
            if event.event_type in {"plan_proposed", "plan_revised", "plan_restarted"}:
                plan = PlanProposal.from_dict(event.payload["plan"])
        return plan

    @property
    def status(self) -> PlanStatus | None:
        status = None
        for event in self._events():
            if "status" in event.payload:
                status = PlanStatus(event.payload["status"])
        return status

    @property
    def side_effect_count(self) -> int:
        return sum(event.event_type == "protected_effect_released" for event in self._events())

    def propose(self, plan: PlanProposal) -> None:
        if self.current_plan is not None:
            raise ContractViolation("initial proposal already exists")
        plan.validate()
        if plan.revision != 1:
            raise ContractViolation("initial proposal must be revision 1")
        if not plan.boundary.is_within(self.task_boundary):
            raise ContractViolation("plan exceeds the original task boundary")
        if not self.is_current_authority(plan.authority):
            raise ContractViolation("proposal authority is not current")
        self.store.append(
            "plan_proposed",
            {
                "plan": plan.to_dict(),
                "runtime_binding": self._runtime_binding(),
                "status": PlanStatus.AWAITING_DECISION,
            },
        )

    def record_decision(self, decision: Decision) -> str:
        decision.validate_shape()
        self._assert_runtime_binding()
        plan = self.current_plan
        if plan is None:
            raise ContractViolation("no plan exists")
        if decision.plan_id != plan.plan_id or decision.revision != plan.revision:
            raise ContractViolation("decision targets a stale or different plan revision")
        if decision.authority != plan.authority:
            raise ContractViolation("decision authority does not match the plan request")
        if not self.is_current_authority(decision.authority):
            raise ContractViolation("decision authority is no longer current")
        if not decision.observed_boundary.is_within(plan.boundary):
            raise ContractViolation("decision attempts to widen reviewed authority")
        if not decision.observed_boundary.is_within(self.task_boundary):
            raise ContractViolation("decision attempts to widen original task authority")

        previous = [
            event
            for event in self._events()
            if event.event_type == "decision_recorded"
            and event.payload["decision_id"] == decision.decision_id
        ]
        if previous:
            fingerprints = {
                event.payload.get("decision_fingerprint") for event in previous
            }
            if fingerprints != {decision.fingerprint()}:
                raise ContractViolation("decision id was replayed with altered content")
            return "duplicate_suppressed"
        if self.status is not PlanStatus.AWAITING_DECISION:
            raise ContractViolation("current plan is not awaiting a decision")

        if decision.decision_type is DecisionType.EDIT:
            revised = decision.edited_plan
            assert revised is not None
            revised.validate()
            if revised.immutable_identity() != plan.immutable_identity():
                raise ContractViolation("edit changed immutable plan identity or versions")
            if revised.revision != plan.revision + 1:
                raise ContractViolation("edit must create exactly the next plan revision")
            if not revised.boundary.is_within(plan.boundary):
                raise ContractViolation("edit cannot widen the reviewed plan boundary")
            if not revised.boundary.is_within(self.task_boundary):
                raise ContractViolation("edit cannot widen original task authority")
            self.store.append(
                "decision_recorded",
                {
                    "decision_id": decision.decision_id,
                    "decision_fingerprint": decision.fingerprint(),
                    "decision_type": decision.decision_type,
                    "plan_id": plan.plan_id,
                    "revision": plan.revision,
                    "authority": asdict(decision.authority),
                    "status": PlanStatus.AWAITING_REVISION,
                },
            )
            self.store.append(
                "plan_revised",
                {"plan": revised.to_dict(), "status": PlanStatus.AWAITING_DECISION},
            )
            return "revised"

        if decision.decision_type is DecisionType.APPROVE:
            new_status = PlanStatus.APPROVED
        elif decision.decision_type is DecisionType.REJECT:
            new_status = PlanStatus.REJECTED
        elif decision.decision_type is DecisionType.RESPOND:
            if not self.respond_permitted:
                raise ContractViolation("respond is not permitted by this plan review config")
            new_status = PlanStatus.AWAITING_REVISION
        else:  # pragma: no cover - enum exhaustiveness
            raise ContractViolation("unsupported normalized decision")

        self.store.append(
            "decision_recorded",
            {
                "decision_id": decision.decision_id,
                "decision_fingerprint": decision.fingerprint(),
                "decision_type": decision.decision_type,
                "plan_id": plan.plan_id,
                "revision": plan.revision,
                "authority": asdict(decision.authority),
                "message": decision.message,
                "status": new_status,
            },
        )
        return new_status

    def submit_revision(self, revised: PlanProposal) -> None:
        """Persist a new plan after a permitted response requested revision."""

        self._assert_runtime_binding()
        plan = self.current_plan
        if plan is None or self.status is not PlanStatus.AWAITING_REVISION:
            raise ContractViolation("a new revision was not requested")
        revised.validate()
        if revised.immutable_identity() != plan.immutable_identity():
            raise ContractViolation("revision changed immutable plan identity or versions")
        if revised.revision != plan.revision + 1:
            raise ContractViolation("revision must advance exactly once")
        if not revised.boundary.is_within(plan.boundary):
            raise ContractViolation("revision cannot widen the reviewed plan boundary")
        if not revised.boundary.is_within(self.task_boundary):
            raise ContractViolation("revision cannot widen original task authority")
        if not self.is_current_authority(revised.authority):
            raise ContractViolation("revision authority is not current")
        self.store.append(
            "plan_revised",
            {"plan": revised.to_dict(), "status": PlanStatus.AWAITING_DECISION},
        )

    def abandon_locally(self, actor_id: str) -> None:
        """Record local UI abandonment without inventing a HITL decision/resume."""

        if not actor_id:
            raise ContractViolation("abandonment actor is required")
        self._assert_runtime_binding()
        self.store.append(
            "local_abandonment",
            {
                "actor_id": actor_id,
                "provider_resume_emitted": False,
                "status": self.status,
            },
        )

    def restart_after_rejection(self, plan: PlanProposal) -> None:
        """Start a new request explicitly while preserving the rejected audit."""

        self._assert_runtime_binding()
        previous = self.current_plan
        if previous is None or self.status is not PlanStatus.REJECTED:
            raise ContractViolation("explicit restart requires a rejected plan")
        plan.validate()
        if plan.revision != 1:
            raise ContractViolation("a restarted plan begins at revision 1")
        if plan.plan_id == previous.plan_id or plan.authority.run_id == previous.authority.run_id:
            raise ContractViolation("restart requires new plan and run identity")
        if plan.authority.request_id == previous.authority.request_id:
            raise ContractViolation("restart requires a new request identity")
        if (
            plan.authority.workspace_id != previous.authority.workspace_id
            or plan.authority.task_id != previous.authority.task_id
            or plan.authority.actor_id != previous.authority.actor_id
        ):
            raise ContractViolation("restart must remain bound to the original task authority")
        if not plan.boundary.is_within(self.task_boundary):
            raise ContractViolation("restarted plan exceeds the original task boundary")
        if not self.is_current_authority(plan.authority):
            raise ContractViolation("restart authority is not current")
        self.store.append(
            "plan_restarted",
            {"plan": plan.to_dict(), "status": PlanStatus.AWAITING_DECISION},
        )

    def reconnect(self) -> dict[str, object]:
        """Read durable state only; reconnect never resumes or creates effects."""

        self._assert_runtime_binding()
        plan = self.current_plan
        return {
            "plan_id": plan.plan_id if plan else None,
            "revision": plan.revision if plan else None,
            "status": self.status,
            "side_effect_count": self.side_effect_count,
        }

    def resume(self, *, authority: Authority, resume_id: str) -> str:
        """Release protected work after a persisted current approval.

        `resume_id` is a local idempotency key. It is not provider resume syntax.
        """

        if not resume_id:
            raise ContractViolation("resume id is required")
        self._assert_runtime_binding()
        plan = self.current_plan
        if plan is None or self.status not in {PlanStatus.APPROVED, PlanStatus.EXECUTING}:
            raise ContractViolation("direct resume is blocked without persisted approval")
        if authority != plan.authority or not self.is_current_authority(authority):
            raise ContractViolation("resume authority is invalid or expired")

        matching = [
            event
            for event in self._events()
            if event.event_type == "protected_effect_released"
            and event.payload["resume_id"] == resume_id
        ]
        if matching:
            return "duplicate_suppressed"
        if self.side_effect_count:
            raise ContractViolation("a different resume already released protected work")
        self.store.append(
            "protected_effect_released",
            {
                "resume_id": resume_id,
                "plan_id": plan.plan_id,
                "revision": plan.revision,
                "authority": asdict(authority),
                "status": PlanStatus.EXECUTING,
            },
        )
        return "released"
