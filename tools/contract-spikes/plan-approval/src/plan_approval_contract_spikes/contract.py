from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
import hashlib
import json
from typing import Any, Mapping

from .errors import ContractViolation


class DecisionType(StrEnum):
    """Normalized values owned by SPIKE-HITL-001, consumed without transport."""

    APPROVE = "approve"
    EDIT = "edit"
    REJECT = "reject"
    RESPOND = "respond"


class PlanStatus(StrEnum):
    AWAITING_DECISION = "awaiting_decision"
    AWAITING_REVISION = "awaiting_revision"
    APPROVED = "approved"
    REJECTED = "rejected"
    LOCALLY_ABANDONED = "locally_abandoned"
    EXECUTING = "executing"


@dataclass(frozen=True)
class Authority:
    actor_id: str
    workspace_id: str
    task_id: str
    run_id: str
    request_id: str

    def validate(self) -> None:
        if not all(asdict(self).values()):
            raise ContractViolation("authority fields must be non-empty")


@dataclass(frozen=True)
class Boundary:
    permissions: tuple[str, ...]
    side_effects: tuple[str, ...]

    def validate(self) -> None:
        if len(set(self.permissions)) != len(self.permissions):
            raise ContractViolation("permissions must be unique")
        if len(set(self.side_effects)) != len(self.side_effects):
            raise ContractViolation("side effects must be unique")
        if any(not item for item in (*self.permissions, *self.side_effects)):
            raise ContractViolation("boundary values must be non-empty")

    def is_within(self, other: Boundary) -> bool:
        return set(self.permissions) <= set(other.permissions) and set(
            self.side_effects
        ) <= set(other.side_effects)


@dataclass(frozen=True)
class PlanStep:
    step_id: str
    text: str
    protected_effects: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.step_id or not self.text.strip():
            raise ContractViolation("plan steps require stable IDs and visible text")
        if len(set(self.protected_effects)) != len(self.protected_effects):
            raise ContractViolation("protected effects must be unique")


@dataclass(frozen=True)
class PlanProposal:
    plan_id: str
    schema_version: str
    template_id: str
    template_version: str
    config_version: str
    created_at: str
    authority: Authority
    revision: int
    steps: tuple[PlanStep, ...]
    boundary: Boundary
    supersedes_revision: int | None = None

    def validate(self) -> None:
        self.authority.validate()
        self.boundary.validate()
        if not all(
            (
                self.plan_id,
                self.schema_version,
                self.template_id,
                self.template_version,
                self.config_version,
                self.created_at,
            )
        ):
            raise ContractViolation("plan identity and version fields must be non-empty")
        if self.revision < 1:
            raise ContractViolation("plan revision must be positive")
        if not self.steps:
            raise ContractViolation("a real plan requires at least one ordered step")
        step_ids = [step.step_id for step in self.steps]
        if len(set(step_ids)) != len(step_ids):
            raise ContractViolation("step IDs must be unique within a revision")
        for step in self.steps:
            step.validate()
            if not set(step.protected_effects) <= set(self.boundary.side_effects):
                raise ContractViolation(
                    "step effects must remain inside the declared side-effect boundary"
                )
        if self.revision == 1 and self.supersedes_revision is not None:
            raise ContractViolation("revision 1 cannot supersede another revision")
        if self.revision > 1 and self.supersedes_revision != self.revision - 1:
            raise ContractViolation("a revised plan must supersede the prior revision")

    def immutable_identity(self) -> tuple[Any, ...]:
        return (
            self.plan_id,
            self.schema_version,
            self.template_id,
            self.template_version,
            self.config_version,
            self.created_at,
            self.authority,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> PlanProposal:
        authority = Authority(**value["authority"])
        boundary = Boundary(
            permissions=tuple(value["boundary"]["permissions"]),
            side_effects=tuple(value["boundary"]["side_effects"]),
        )
        steps = tuple(
            PlanStep(
                step_id=step["step_id"],
                text=step["text"],
                protected_effects=tuple(step.get("protected_effects", ())),
            )
            for step in value["steps"]
        )
        return cls(
            plan_id=value["plan_id"],
            schema_version=value["schema_version"],
            template_id=value["template_id"],
            template_version=value["template_version"],
            config_version=value["config_version"],
            created_at=value["created_at"],
            authority=authority,
            revision=value["revision"],
            steps=steps,
            boundary=boundary,
            supersedes_revision=value.get("supersedes_revision"),
        )


@dataclass(frozen=True)
class Decision:
    """A normalized, upstream-validated decision bound to one plan revision.

    `upstream_validated` attests only that the owning HITL adapter validated its
    generic vector/count/order/freshness contract. This harness neither performs
    that validation nor constructs provider resume syntax.
    """

    decision_id: str
    decision_type: DecisionType
    authority: Authority
    plan_id: str
    revision: int
    observed_boundary: Boundary
    upstream_validated: bool
    edited_plan: PlanProposal | None = None
    message: str | None = None

    def validate_shape(self) -> None:
        self.authority.validate()
        self.observed_boundary.validate()
        if not self.decision_id or not self.plan_id or self.revision < 1:
            raise ContractViolation("decision identity must be complete")
        if not self.upstream_validated:
            raise ContractViolation("normalized HITL validation evidence is required")
        if self.decision_type is DecisionType.EDIT and self.edited_plan is None:
            raise ContractViolation("edit requires a complete revised plan")
        if self.decision_type is not DecisionType.EDIT and self.edited_plan is not None:
            raise ContractViolation("only edit may carry a revised plan")
        if self.decision_type is DecisionType.RESPOND and not (self.message or "").strip():
            raise ContractViolation("respond requires a non-empty message")

    def fingerprint(self) -> str:
        """Return a stable digest so an idempotency key cannot mask altered input."""

        encoded = json.dumps(
            asdict(self), sort_keys=True, separators=(",", ":")
        ).encode()
        return hashlib.sha256(encoded).hexdigest()
