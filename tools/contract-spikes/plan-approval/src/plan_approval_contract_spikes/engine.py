from __future__ import annotations

from dataclasses import asdict, dataclass
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


@dataclass(frozen=True)
class _ReducedState:
    plan: PlanProposal | None = None
    status: PlanStatus | None = None
    current_approval: bool = False
    side_effect_count: int = 0


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

    @staticmethod
    def _require_status(event, expected: PlanStatus) -> None:
        if event.payload.get("status") != expected:
            raise ContractViolation(
                f"{event.event_type} carries an invalid state transition"
            )

    def _reduce(self) -> _ReducedState:
        """Derive state from a closed event schema, never arbitrary status fields."""

        plan: PlanProposal | None = None
        status: PlanStatus | None = None
        current_approval = False
        side_effect_count = 0

        for event in self._events():
            if event.event_type == "plan_proposed":
                if plan is not None or status is not None:
                    raise ContractViolation("initial proposal must be the first event")
                self._require_status(event, PlanStatus.AWAITING_DECISION)
                plan = PlanProposal.from_dict(event.payload["plan"])
                plan.validate()
                if plan.revision != 1:
                    raise ContractViolation("initial stored proposal must be revision 1")
                status = PlanStatus.AWAITING_DECISION
                current_approval = False
            elif event.event_type == "decision_recorded":
                if plan is None or status is not PlanStatus.AWAITING_DECISION:
                    raise ContractViolation("stored decision is out of sequence")
                if (
                    event.payload.get("plan_id") != plan.plan_id
                    or event.payload.get("revision") != plan.revision
                    or event.payload.get("authority") != asdict(plan.authority)
                    or not event.payload.get("decision_id")
                    or not event.payload.get("decision_fingerprint")
                ):
                    raise ContractViolation("stored decision is not bound to the current plan")
                decision_type = DecisionType(event.payload.get("decision_type"))
                if decision_type is DecisionType.APPROVE:
                    expected = PlanStatus.APPROVED
                    current_approval = True
                elif decision_type in {DecisionType.EDIT, DecisionType.RESPOND}:
                    if (
                        decision_type is DecisionType.RESPOND
                        and not self.respond_permitted
                    ):
                        raise ContractViolation("stored response is not permitted")
                    expected = PlanStatus.AWAITING_REVISION
                    current_approval = False
                elif decision_type is DecisionType.REJECT:
                    expected = PlanStatus.REJECTED
                    current_approval = False
                else:  # pragma: no cover - enum exhaustiveness
                    raise ContractViolation("stored decision type is invalid")
                self._require_status(event, expected)
                status = expected
            elif event.event_type == "plan_revised":
                if plan is None or status is not PlanStatus.AWAITING_REVISION:
                    raise ContractViolation("stored plan revision is out of sequence")
                self._require_status(event, PlanStatus.AWAITING_DECISION)
                revised = PlanProposal.from_dict(event.payload["plan"])
                revised.validate()
                if revised.immutable_identity() != plan.immutable_identity():
                    raise ContractViolation("stored revision changed immutable plan identity")
                if revised.revision != plan.revision + 1:
                    raise ContractViolation("stored revision skipped a revision")
                if not revised.boundary.is_within(plan.boundary):
                    raise ContractViolation("stored revision widened the plan boundary")
                plan = revised
                status = PlanStatus.AWAITING_DECISION
                current_approval = False
            elif event.event_type == "plan_restarted":
                if plan is None or status is not PlanStatus.REJECTED:
                    raise ContractViolation("stored restart is out of sequence")
                self._require_status(event, PlanStatus.AWAITING_DECISION)
                restarted = PlanProposal.from_dict(event.payload["plan"])
                restarted.validate()
                if (
                    restarted.revision != 1
                    or restarted.plan_id == plan.plan_id
                    or restarted.authority.run_id == plan.authority.run_id
                    or restarted.authority.request_id == plan.authority.request_id
                    or restarted.authority.workspace_id != plan.authority.workspace_id
                    or restarted.authority.task_id != plan.authority.task_id
                    or restarted.authority.actor_id != plan.authority.actor_id
                    or not restarted.boundary.is_within(self.task_boundary)
                ):
                    raise ContractViolation("stored restart identity or boundary is invalid")
                plan = restarted
                status = PlanStatus.AWAITING_DECISION
                current_approval = False
            elif event.event_type == "local_abandonment":
                if plan is None or status not in {
                    PlanStatus.AWAITING_DECISION,
                    PlanStatus.AWAITING_REVISION,
                }:
                    raise ContractViolation("stored local abandonment is out of sequence")
                self._require_status(event, PlanStatus.LOCALLY_ABANDONED)
                if (
                    event.payload.get("actor_id") != plan.authority.actor_id
                    or event.payload.get("provider_resume_emitted") is not False
                ):
                    raise ContractViolation("stored local abandonment is not actor bound")
                status = PlanStatus.LOCALLY_ABANDONED
                current_approval = False
            elif event.event_type == "protected_effect_released":
                if (
                    plan is None
                    or status is not PlanStatus.APPROVED
                    or not current_approval
                    or side_effect_count
                ):
                    raise ContractViolation("stored protected release lacks current approval")
                self._require_status(event, PlanStatus.EXECUTING)
                if (
                    event.payload.get("plan_id") != plan.plan_id
                    or event.payload.get("revision") != plan.revision
                    or event.payload.get("authority") != asdict(plan.authority)
                    or not event.payload.get("resume_id")
                ):
                    raise ContractViolation("stored protected release is not plan bound")
                status = PlanStatus.EXECUTING
                side_effect_count = 1
            else:
                raise ContractViolation(
                    f"unrecognized plan-approval event: {event.event_type}"
                )

        return _ReducedState(
            plan=plan,
            status=status,
            current_approval=current_approval,
            side_effect_count=side_effect_count,
        )

    @property
    def current_plan(self) -> PlanProposal | None:
        return self._reduce().plan

    @property
    def status(self) -> PlanStatus | None:
        return self._reduce().status

    @property
    def side_effect_count(self) -> int:
        return self._reduce().side_effect_count

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
        if decision.observed_boundary != plan.boundary:
            raise ContractViolation("decision boundary does not match the current plan")
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

    def abandon_locally(self, actor_id: str) -> str:
        """Record local UI abandonment without inventing a HITL decision/resume."""

        if not actor_id:
            raise ContractViolation("abandonment actor is required")
        self._assert_runtime_binding()
        state = self._reduce()
        plan = state.plan
        if plan is None:
            raise ContractViolation("no plan exists")
        if actor_id != plan.authority.actor_id:
            raise ContractViolation("abandonment actor does not own the plan request")
        if not self.is_current_authority(plan.authority):
            raise ContractViolation("abandonment actor authority is no longer current")
        if state.status is PlanStatus.LOCALLY_ABANDONED:
            return "duplicate_suppressed"
        if state.status not in {
            PlanStatus.AWAITING_DECISION,
            PlanStatus.AWAITING_REVISION,
        }:
            raise ContractViolation("current plan cannot be locally abandoned")
        self.store.append(
            "local_abandonment",
            {
                "actor_id": actor_id,
                "provider_resume_emitted": False,
                "status": PlanStatus.LOCALLY_ABANDONED,
            },
        )
        return "locally_abandoned"

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
        state = self._reduce()
        plan = state.plan
        if (
            plan is None
            or state.status not in {PlanStatus.APPROVED, PlanStatus.EXECUTING}
            or not state.current_approval
        ):
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
        if state.side_effect_count:
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
