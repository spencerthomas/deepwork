"""Pure task, run, event, interrupt, and decision values."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

EventDataValue = str | int | bool | tuple[str, ...] | None
EventData = tuple[tuple[str, EventDataValue], ...]
MAX_TASK_OBJECTIVE_LENGTH = 8_000
MAX_PLAN_STEPS = 8
MAX_PLAN_STEP_LENGTH = 1_000
MAX_TASK_RESULT_FORMATTING_OVERHEAD = 2_048
MAX_TASK_RESULT_LENGTH = (
    MAX_TASK_OBJECTIVE_LENGTH
    + MAX_PLAN_STEPS * MAX_PLAN_STEP_LENGTH
    + MAX_TASK_RESULT_FORMATTING_OVERHEAD
)


class TaskStatus(StrEnum):
    """Application-owned task/run state for the local fixture loop."""

    QUEUED = "queued"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"

    @property
    def is_terminal(self) -> bool:
        """Return whether no more events may be appended to the run."""

        return self in {self.COMPLETED, self.REJECTED, self.FAILED}


class DecisionValue(StrEnum):
    """Supported decisions for the bounded approval interrupt."""

    APPROVE = "approve"
    REJECT = "reject"
    RESPOND = "respond"


class TaskEventName(StrEnum):
    """Normalized event names exposed by the application stream."""

    TASK_CREATED = "task.created"
    RUN_STARTED = "run.started"
    CONTENT_DELTA = "content.delta"
    PLAN_PROPOSED = "plan.proposed"
    PLAN_UPDATED = "plan.updated"
    EVIDENCE_RECORDED = "evidence.recorded"
    INTERRUPT_REQUESTED = "interrupt.requested"
    DECISION_RECORDED = "decision.recorded"
    RUN_COMPLETED = "run.completed"


class EvidenceKind(StrEnum):
    """Bounded evidence kind for the credential-free local runner."""

    FIXTURE = "fixture"


class EvidenceSource(StrEnum):
    """Truthful provenance for locally generated evidence."""

    LOCAL_RUNNER = "deterministic-local-runner"
    REVIEWER_RESPONSE = "reviewer-response"


@dataclass(frozen=True, slots=True)
class TaskEvent:
    """One replayable normalized event."""

    event_id: int
    name: TaskEventName
    data: EventData


@dataclass(frozen=True, slots=True)
class ProposedPlan:
    """Current editable local plan associated with a pending interrupt."""

    revision: int
    title: str
    steps: tuple[str, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """Inspectable evidence with explicit local-fixture provenance."""

    evidence_id: str
    kind: EvidenceKind
    summary: str
    source: EvidenceSource
    verified: bool


@dataclass(frozen=True, slots=True)
class TaskSnapshot:
    """Immutable application view of one local task."""

    task_id: str
    run_id: str
    title: str
    objective: str
    status: TaskStatus
    last_event_id: int
    pending_interrupt_id: str | None
    proposed_plan: ProposedPlan | None
    evidence: tuple[EvidenceRecord, ...]
    result: str | None


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    """Accepted decision result, including idempotent replay state."""

    task_id: str
    run_id: str
    interrupt_id: str
    decision: DecisionValue
    duplicate: bool


@dataclass(frozen=True, slots=True)
class PlanUpdateRecord:
    """Accepted plan edit for the exact pending interrupt and revision."""

    task_id: str
    run_id: str
    interrupt_id: str
    plan: ProposedPlan


class TaskDomainError(Exception):
    """Base error mapped safely at the transport boundary."""


class TaskNotFoundError(TaskDomainError):
    """The task is absent or cannot be disclosed."""


class InvalidEventCursorError(TaskDomainError):
    """The requested replay cursor is outside the task event history."""


class InterruptMismatchError(TaskDomainError):
    """The supplied interrupt does not match the pending task interrupt."""


class StaleInterruptError(TaskDomainError):
    """The supplied interrupt is no longer actionable."""


class DecisionConflictError(TaskDomainError):
    """A different decision was already recorded for the interrupt."""


class PlanUnavailableError(TaskDomainError):
    """The task has no editable proposed plan."""


class PlanRevisionConflictError(TaskDomainError):
    """The supplied plan revision is stale or otherwise conflicting."""
