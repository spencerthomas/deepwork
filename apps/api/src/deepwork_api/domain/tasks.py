"""Pure task, run, event, interrupt, and decision values."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from deepwork_api.domain.auth import (
    DEFAULT_ACTOR_ID,
    DEFAULT_TENANT_ID,
    DEFAULT_WORKSPACE_ID,
    SecurityContext,
)

EventDataValue = str | int | bool | tuple[str, ...] | None
EventData = tuple[tuple[str, EventDataValue], ...]
MAX_TASK_OBJECTIVE_LENGTH = 8_000
MAX_PLAN_STEPS = 8
MAX_PLAN_STEP_LENGTH = 1_000
MAX_PLAN_REVISION = 2_147_483_647
MAX_TASK_RESULT_FORMATTING_OVERHEAD = 2_048
MAX_TASK_RESULT_LENGTH = (
    MAX_TASK_OBJECTIVE_LENGTH
    + MAX_PLAN_STEPS * MAX_PLAN_STEP_LENGTH
    + MAX_TASK_RESULT_FORMATTING_OVERHEAD
)
CANCELLATION_SAFE_REASON = "The run was cancelled before it produced a result."


class TaskStatus(StrEnum):
    """Application-owned task/run state for the local fixture loop."""

    QUEUED = "queued"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        """Return whether no more events may be appended to the run."""

        return self in {self.COMPLETED, self.REJECTED, self.FAILED, self.CANCELLED}


class DecisionValue(StrEnum):
    """Supported decisions for the bounded approval interrupt."""

    APPROVE = "approve"
    REJECT = "reject"
    RESPOND = "respond"


class DecisionType(StrEnum):
    """One positional decision in an ordered HITL batch."""

    APPROVE = "approve"
    EDIT = "edit"
    REJECT = "reject"
    RESPOND = "respond"


def aggregate_batch_decision(decision_types: tuple[DecisionType, ...]) -> DecisionValue:
    """Project positional decisions onto the fixture runner's bounded outcome."""

    if not decision_types:
        raise ValueError("decision batch must not be empty")
    if DecisionType.REJECT in decision_types:
        return DecisionValue.REJECT
    return DecisionValue.APPROVE


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
    CODING_COMPLETED = "coding.completed"
    RUN_COMPLETED = "run.completed"


class TaskJourney(StrEnum):
    """Optional first-class journey selected at task creation."""

    CODING = "coding"


@dataclass(frozen=True, slots=True)
class CodingOutcome:
    """Client-safe exact-revision coding proof projected from retained events."""

    evidence_class: str
    repository_id: str
    repository: str
    base_branch: str
    base_sha: str
    head_sha: str
    environment: str
    environment_version: int
    snapshot_digest: str
    sandbox_state: str
    setup_status: str
    changed_files: tuple[str, ...]
    draft_pr_number: int
    draft_pr_status: str
    pr_create_attempts: int
    reconciled_after_timeout: bool
    checks: tuple[str, ...]
    merge_state: str


_GIT_SHA_PATTERN = re.compile(r"^[a-f0-9]{40}$")
_SNAPSHOT_DIGEST_PATTERN = re.compile(r"^sha256:[a-f0-9]{16,64}$")


def coding_outcome_from_event_data(data: Mapping[str, EventDataValue]) -> CodingOutcome:
    """Validate the normalized credential-free coding event projection."""

    expected = {
        "evidenceClass",
        "repositoryId",
        "repository",
        "baseBranch",
        "baseSha",
        "headSha",
        "environment",
        "environmentVersion",
        "snapshotDigest",
        "sandboxState",
        "setupStatus",
        "changedFiles",
        "draftPrNumber",
        "draftPrStatus",
        "prCreateAttempts",
        "reconciledAfterTimeout",
        "checks",
        "mergeState",
    }
    if set(data) != expected:
        raise ValueError("coding outcome fields are invalid")

    def required_string(key: str, maximum: int = 200) -> str:
        value = data[key]
        if not isinstance(value, str) or not value.strip() or len(value) > maximum:
            raise ValueError(f"coding outcome {key} is invalid")
        return value

    def required_integer(key: str) -> int:
        value = data[key]
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ValueError(f"coding outcome {key} is invalid")
        return value

    def string_tuple(key: str, maximum: int) -> tuple[str, ...]:
        value = data[key]
        if (
            not isinstance(value, tuple)
            or not 1 <= len(value) <= maximum
            or any(not isinstance(item, str) or not item or len(item) > 200 for item in value)
        ):
            raise ValueError(f"coding outcome {key} is invalid")
        return value

    evidence_class = required_string("evidenceClass")
    repository_id = required_string("repositoryId")
    repository = required_string("repository")
    base_branch = required_string("baseBranch")
    base_sha = required_string("baseSha", 40)
    head_sha = required_string("headSha", 40)
    environment = required_string("environment")
    environment_version = required_integer("environmentVersion")
    snapshot_digest = required_string("snapshotDigest", 71)
    sandbox_state = required_string("sandboxState")
    setup_status = required_string("setupStatus")
    changed_files = string_tuple("changedFiles", 100)
    draft_pr_number = required_integer("draftPrNumber")
    draft_pr_status = required_string("draftPrStatus")
    pr_create_attempts = required_integer("prCreateAttempts")
    reconciled_after_timeout = data["reconciledAfterTimeout"]
    checks = string_tuple("checks", 50)
    merge_state = required_string("mergeState")
    if (
        evidence_class != "fixture"
        or repository_id != "fixture_repo_deepwork"
        or not _GIT_SHA_PATTERN.fullmatch(base_sha)
        or not _GIT_SHA_PATTERN.fullmatch(head_sha)
        or base_sha == head_sha
        or not _SNAPSHOT_DIGEST_PATTERN.fullmatch(snapshot_digest)
        or sandbox_state != "cleaned"
        or setup_status != "passed"
        or draft_pr_status != "draft"
        or not isinstance(reconciled_after_timeout, bool)
        or merge_state != "unavailable"
    ):
        raise ValueError("coding outcome state is invalid")
    return CodingOutcome(
        evidence_class=evidence_class,
        repository_id=repository_id,
        repository=repository,
        base_branch=base_branch,
        base_sha=base_sha,
        head_sha=head_sha,
        environment=environment,
        environment_version=environment_version,
        snapshot_digest=snapshot_digest,
        sandbox_state=sandbox_state,
        setup_status=setup_status,
        changed_files=changed_files,
        draft_pr_number=draft_pr_number,
        draft_pr_status=draft_pr_status,
        pr_create_attempts=pr_create_attempts,
        reconciled_after_timeout=reconciled_after_timeout,
        checks=checks,
        merge_state=merge_state,
    )


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

    def __post_init__(self) -> None:
        """Keep every plan revision inside the shared signed 32-bit bound."""

        if (
            not isinstance(self.revision, int)
            or isinstance(self.revision, bool)
            or not 1 <= self.revision <= MAX_PLAN_REVISION
        ):
            message = "plan revision is outside the shared bound"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """Inspectable evidence with explicit local-fixture provenance."""

    evidence_id: str
    task_id: str
    run_id: str
    kind: EvidenceKind
    summary: str
    source: EvidenceSource
    verified: bool


@dataclass(frozen=True, slots=True)
class TaskSnapshot:
    """Immutable application view of one local task."""

    task_id: str
    run_id: str
    # Absent (None) only for tasks migrated from a pre-timestamp schema, whose
    # real creation instant was never recorded and must not be fabricated.
    created_at: str | None
    title: str
    objective: str
    status: TaskStatus
    last_event_id: int
    pending_interrupt_id: str | None
    proposed_plan: ProposedPlan | None
    evidence: tuple[EvidenceRecord, ...]
    result: str | None
    # Application-owned authorization metadata. These fields stay server-side:
    # task response and event contracts intentionally do not project them.
    tenant_id: str = DEFAULT_TENANT_ID
    workspace_id: str = DEFAULT_WORKSPACE_ID
    created_by_actor_id: str = DEFAULT_ACTOR_ID
    # The source assistant selected for this run. Older fixture tasks and
    # pre-agent-registry event histories legitimately have no retained value.
    agent_id: str | None = None
    # Absent for the original general-purpose task contract. Coding tasks bind a
    # reviewed fixture repository at creation and retain their exact-revision
    # outcome as a normalized event; no provider token or auth reference enters
    # this snapshot.
    journey: TaskJourney | None = None
    repository_id: str | None = None
    coding: CodingOutcome | None = None

    def __post_init__(self) -> None:
        SecurityContext(
            tenant_id=self.tenant_id,
            workspace_id=self.workspace_id,
            actor_id=self.created_by_actor_id,
        )


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    """Accepted decision result, including idempotent replay state."""

    task_id: str
    run_id: str
    interrupt_id: str
    decision: DecisionValue
    duplicate: bool


@dataclass(frozen=True, slots=True)
class DecisionBatchRecord:
    """Accepted ordered decision vector, including replay state."""

    task_id: str
    run_id: str
    interrupt_id: str
    version: str
    decision_types: tuple[DecisionType, ...]
    duplicate: bool


@dataclass(frozen=True, slots=True)
class OrderedDecision:
    """Transient validated input for one positional batch entry."""

    decision_type: DecisionType
    edited_action_name: str | None = None
    edited_position: int | None = None
    edited_text: str | None = None
    message: str | None = None


@dataclass(frozen=True, slots=True)
class PlanUpdateRecord:
    """Accepted plan edit for the exact pending interrupt and revision."""

    task_id: str
    run_id: str
    interrupt_id: str
    plan: ProposedPlan


@dataclass(frozen=True, slots=True)
class CancellationRecord:
    """Accepted cancellation receipt, including idempotent replay state."""

    task_id: str
    run_id: str
    duplicate: bool


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


class DecisionBatchVersionStaleError(TaskDomainError):
    """The caller reviewed a different version of the pending batch."""


class InvalidDecisionBatchError(TaskDomainError):
    """The ordered decision vector is incomplete, misaligned, or disallowed."""


class DecisionBatchUnsupportedError(TaskDomainError):
    """The configured task source cannot safely submit this decision batch."""


class TaskAlreadyResolvedError(TaskDomainError):
    """The task already reached a non-cancelled terminal state and cannot be cancelled."""


class TaskCancellationUnsupportedError(TaskDomainError):
    """The active task source cannot truthfully stop an executing run.

    Publishing a terminal cancelled state here would falsely report a run that
    keeps executing upstream as stopped, so the operation is refused instead.
    """


class PlanUnavailableError(TaskDomainError):
    """The task has no editable proposed plan."""


class PlanRevisionConflictError(TaskDomainError):
    """The supplied plan revision is stale or otherwise conflicting."""


class TaskSourceUnavailableError(TaskDomainError):
    """The configured task source cannot safely start the requested run."""


class TaskSourceContractError(TaskDomainError):
    """The configured task source broke its supported contract."""
