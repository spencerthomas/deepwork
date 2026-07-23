"""Pydantic task, decision, and normalized event wire contracts."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from deepwork_api.domain import (
    MAX_PLAN_REVISION,
    MAX_PLAN_STEP_LENGTH,
    MAX_PLAN_STEPS,
    MAX_TASK_OBJECTIVE_LENGTH,
    MAX_TASK_RESULT_LENGTH,
    DecisionRecord,
    DecisionValue,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSource,
    PlanUpdateRecord,
    ProposedPlan,
    TaskEvent,
    TaskEventName,
    TaskSnapshot,
    TaskStatus,
)

TaskId = Annotated[str, StringConstraints(pattern=r"^task_[0-9]{8}$")]
# Run and interrupt identities may be application-generated fixture values or
# source-qualified identifiers minted by the configured local Agent Server.
# Both stay inside one bounded safe-identifier alphabet; task and evidence
# identities remain application-owned and strict.
_SOURCE_SAFE_IDENTIFIER = r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$"
RunId = Annotated[str, StringConstraints(pattern=_SOURCE_SAFE_IDENTIFIER)]
InterruptId = Annotated[str, StringConstraints(pattern=_SOURCE_SAFE_IDENTIFIER)]
EvidenceId = Annotated[
    str,
    StringConstraints(pattern=r"^evidence_[0-9]{8}(?:_[0-9]{2})?$"),
]
type TaskWireStatus = Literal[
    "queued",
    "running",
    "waiting-approval",
    "completed",
    "rejected",
    "failed",
]
type TaskEvidenceClass = Literal["fixture", "local-source"]


def _reject_unsafe_controls(value: str) -> str:
    # Reject C0 (< 0x20), DEL (0x7F), and C1 (0x80-0x9F) control characters,
    # keeping only tab/newline/carriage-return. This matches the endpoint
    # validator in adapters/sources/classic/source.py, which already rejects
    # DEL, so task input cannot carry control bytes the source layer forbids.
    if any(
        (ord(character) < 32 or 0x7F <= ord(character) <= 0x9F) and character not in "\t\n\r"
        for character in value
    ):
        raise ValueError("control characters are not allowed")
    return value


class _TaskWireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class TaskCreateRequest(_TaskWireModel):
    """Bounded local task creation request."""

    prompt: str = Field(min_length=1, max_length=MAX_TASK_OBJECTIVE_LENGTH)

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str) -> str:
        """Reject blank or control-bearing prompt input."""

        _reject_unsafe_controls(value)
        if not value.strip():
            raise ValueError("prompt must contain visible text")
        return value


class TaskAcceptedResponse(_TaskWireModel):
    """Queued task receipt returned before background work starts."""

    task_id: TaskId = Field(alias="taskId")
    run_id: RunId = Field(alias="runId")
    status: Literal["queued"] = "queued"

    @classmethod
    def from_domain(cls, task: TaskSnapshot) -> TaskAcceptedResponse:
        return cls(task_id=task.task_id, run_id=task.run_id)


class PendingInterruptResponse(_TaskWireModel):
    """One actionable local approval interrupt."""

    interrupt_id: InterruptId = Field(alias="interruptId")
    decisions: tuple[DecisionValue, ...] = (
        DecisionValue.APPROVE,
        DecisionValue.REJECT,
        DecisionValue.RESPOND,
    )
    plan_revision: int = Field(
        alias="planRevision",
        strict=True,
        ge=1,
        le=MAX_PLAN_REVISION,
    )


class ProposedPlanResponse(_TaskWireModel):
    """Current plan available for inspection and pre-execution editing."""

    revision: int = Field(strict=True, ge=1, le=MAX_PLAN_REVISION)
    title: str = Field(min_length=1, max_length=100)
    steps: tuple[str, ...] = Field(min_length=1, max_length=MAX_PLAN_STEPS)
    evidence_refs: tuple[EvidenceId, ...] = Field(alias="evidenceRefs")

    @classmethod
    def from_domain(cls, plan: ProposedPlan) -> ProposedPlanResponse:
        return cls(
            revision=plan.revision,
            title=plan.title,
            steps=plan.steps,
            evidence_refs=plan.evidence_refs,
        )


class EvidenceResponse(_TaskWireModel):
    """Inspectable source-qualified evidence."""

    evidence_id: EvidenceId = Field(alias="evidenceId")
    kind: EvidenceKind
    summary: str = Field(min_length=1, max_length=300)
    source: EvidenceSource
    verified: bool

    @classmethod
    def from_domain(cls, evidence: EvidenceRecord) -> EvidenceResponse:
        return cls(
            evidence_id=evidence.evidence_id,
            kind=evidence.kind,
            summary=evidence.summary,
            source=evidence.source,
            verified=evidence.verified,
        )


class TaskSummaryResponse(_TaskWireModel):
    """Safe task summary containing only the sanitized objective."""

    task_id: TaskId = Field(alias="taskId")
    run_id: RunId = Field(alias="runId")
    title: str = Field(min_length=1, max_length=80)
    objective: str = Field(min_length=1, max_length=MAX_TASK_OBJECTIVE_LENGTH)
    status: TaskWireStatus
    last_event_id: int = Field(alias="lastEventId", ge=1)

    @classmethod
    def from_domain(cls, task: TaskSnapshot) -> TaskSummaryResponse:
        return cls(
            task_id=task.task_id,
            run_id=task.run_id,
            title=task.title,
            objective=task.objective,
            status=_wire_status(task.status),
            last_event_id=task.last_event_id,
        )


class TaskListResponse(_TaskWireModel):
    """Deterministically ordered task collection."""

    items: tuple[TaskSummaryResponse, ...]


class TaskDetailResponse(TaskSummaryResponse):
    """Task summary plus the currently actionable interrupt."""

    pending_interrupt: PendingInterruptResponse | None = Field(alias="pendingInterrupt")
    proposed_plan: ProposedPlanResponse | None = Field(alias="proposedPlan")
    evidence: tuple[EvidenceResponse, ...]
    result: str | None = Field(default=None, max_length=MAX_TASK_RESULT_LENGTH)

    @classmethod
    def from_domain(cls, task: TaskSnapshot) -> TaskDetailResponse:
        pending = (
            PendingInterruptResponse(
                interrupt_id=task.pending_interrupt_id,
                plan_revision=task.proposed_plan.revision,
            )
            if task.pending_interrupt_id is not None and task.proposed_plan is not None
            else None
        )
        return cls(
            task_id=task.task_id,
            run_id=task.run_id,
            title=task.title,
            objective=task.objective,
            status=_wire_status(task.status),
            last_event_id=task.last_event_id,
            pending_interrupt=pending,
            proposed_plan=(
                ProposedPlanResponse.from_domain(task.proposed_plan)
                if task.proposed_plan is not None
                else None
            ),
            evidence=tuple(EvidenceResponse.from_domain(item) for item in task.evidence),
            result=task.result,
        )


class DecisionRequest(_TaskWireModel):
    """One complete decision for the exact pending interrupt."""

    interrupt_id: InterruptId = Field(alias="interruptId")
    decision: DecisionValue
    comment: str | None = Field(default=None, max_length=1_000)

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, value: str | None) -> str | None:
        """Reject unsafe controls without emitting comment content."""

        if value is not None:
            _reject_unsafe_controls(value)
        return value

    @model_validator(mode="after")
    def validate_response(self) -> DecisionRequest:
        """Require meaningful guidance only when resuming with respond."""

        if self.decision is DecisionValue.RESPOND and (
            self.comment is None or not self.comment.strip()
        ):
            raise ValueError("respond requires a non-blank comment")
        return self


class DecisionAcceptedResponse(_TaskWireModel):
    """Accepted or idempotently replayed decision receipt."""

    task_id: TaskId = Field(alias="taskId")
    run_id: RunId = Field(alias="runId")
    interrupt_id: InterruptId = Field(alias="interruptId")
    decision: DecisionValue
    status: Literal["accepted"] = "accepted"
    duplicate: bool

    @classmethod
    def from_domain(cls, record: DecisionRecord) -> DecisionAcceptedResponse:
        return cls(
            task_id=record.task_id,
            run_id=record.run_id,
            interrupt_id=record.interrupt_id,
            decision=record.decision,
            duplicate=record.duplicate,
        )


class PlanUpdateRequest(_TaskWireModel):
    """Edit the exact pending plan revision without silently truncating it."""

    interrupt_id: InterruptId = Field(alias="interruptId")
    expected_revision: int = Field(
        alias="expectedRevision",
        strict=True,
        ge=1,
        le=MAX_PLAN_REVISION,
    )
    steps: tuple[str, ...] = Field(min_length=1, max_length=MAX_PLAN_STEPS)

    @field_validator("steps")
    @classmethod
    def validate_steps(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for step in value:
            _reject_unsafe_controls(step)
            if not step.strip():
                raise ValueError("plan steps must contain visible text")
            if len(step) > MAX_PLAN_STEP_LENGTH:
                raise ValueError("plan step exceeds the shared request bound")
        return value


class PlanUpdateResponse(_TaskWireModel):
    """Accepted plan edit receipt."""

    task_id: TaskId = Field(alias="taskId")
    run_id: RunId = Field(alias="runId")
    interrupt_id: InterruptId = Field(alias="interruptId")
    plan: ProposedPlanResponse

    @classmethod
    def from_domain(cls, record: PlanUpdateRecord) -> PlanUpdateResponse:
        return cls(
            task_id=record.task_id,
            run_id=record.run_id,
            interrupt_id=record.interrupt_id,
            plan=ProposedPlanResponse.from_domain(record.plan),
        )


class ProblemResponse(_TaskWireModel):
    """Stable safe application problem."""

    code: str
    message: str


class TaskResultResponse(_TaskWireModel):
    """Completed prompt-specific local result."""

    task_id: TaskId = Field(alias="taskId")
    run_id: RunId = Field(alias="runId")
    status: Literal["completed"]
    result: str = Field(min_length=1, max_length=MAX_TASK_RESULT_LENGTH)

    @classmethod
    def from_domain(cls, task: TaskSnapshot) -> TaskResultResponse:
        # Guard emptiness, not just None: a completed task with an empty
        # result must map to the sanitized "unavailable" boundary error, never
        # a raw Pydantic min_length violation (an unhandled 500).
        if task.status is not TaskStatus.COMPLETED or not task.result:
            message = "task result is unavailable"
            raise ValueError(message)
        return cls(
            task_id=task.task_id,
            run_id=task.run_id,
            status="completed",
            result=task.result,
        )


class TaskCreatedEventData(_TaskWireModel):
    task_id: TaskId = Field(alias="taskId")
    run_id: RunId = Field(alias="runId")
    status: Literal["queued"]


class RunStartedEventData(_TaskWireModel):
    run_id: RunId = Field(alias="runId")
    status: Literal["running"]


class ContentDeltaEventData(_TaskWireModel):
    text: str = Field(min_length=1, max_length=MAX_TASK_RESULT_LENGTH)
    evidence_class: TaskEvidenceClass = Field(alias="evidenceClass")


class PlanProposedEventData(_TaskWireModel):
    title: str = Field(min_length=1, max_length=100)
    steps: tuple[str, ...] = Field(min_length=1, max_length=8)
    revision: int = Field(strict=True, ge=1, le=MAX_PLAN_REVISION)
    evidence_refs: tuple[EvidenceId, ...] = Field(alias="evidenceRefs")
    evidence_class: TaskEvidenceClass = Field(alias="evidenceClass")


class InterruptRequestedEventData(_TaskWireModel):
    interrupt_id: InterruptId = Field(alias="interruptId")
    question: str = Field(min_length=1, max_length=200)
    decisions: tuple[DecisionValue, ...]
    plan_revision: int = Field(
        alias="planRevision",
        strict=True,
        ge=1,
        le=MAX_PLAN_REVISION,
    )


class DecisionRecordedEventData(_TaskWireModel):
    interrupt_id: InterruptId = Field(alias="interruptId")
    decision: DecisionValue
    comment_provided: bool = Field(alias="commentProvided")
    response_provided: bool = Field(alias="responseProvided")


class EvidenceRecordedEventData(EvidenceResponse):
    """Replayable evidence metadata without source content."""


class RunCompletedEventData(_TaskWireModel):
    run_id: RunId = Field(alias="runId")
    status: Literal["completed", "rejected", "failed"]
    safe_reason: str = Field(alias="safeReason", min_length=1, max_length=200)
    result_available: bool = Field(alias="resultAvailable")


_EVENT_MODELS: dict[TaskEventName, type[BaseModel]] = {
    TaskEventName.TASK_CREATED: TaskCreatedEventData,
    TaskEventName.RUN_STARTED: RunStartedEventData,
    TaskEventName.CONTENT_DELTA: ContentDeltaEventData,
    TaskEventName.PLAN_PROPOSED: PlanProposedEventData,
    TaskEventName.PLAN_UPDATED: PlanProposedEventData,
    TaskEventName.EVIDENCE_RECORDED: EvidenceRecordedEventData,
    TaskEventName.INTERRUPT_REQUESTED: InterruptRequestedEventData,
    TaskEventName.DECISION_RECORDED: DecisionRecordedEventData,
    TaskEventName.RUN_COMPLETED: RunCompletedEventData,
}


def encode_event_data(event: TaskEvent) -> str:
    """Validate normalized event data and emit compact JSON with public aliases."""

    model = _EVENT_MODELS[event.name].model_validate(dict(event.data))
    return model.model_dump_json(by_alias=True)


def _wire_status(status: TaskStatus) -> TaskWireStatus:
    """Map the internal state spelling to the web/domain wire vocabulary."""

    if status is TaskStatus.WAITING_APPROVAL:
        return "waiting-approval"
    if status is TaskStatus.QUEUED:
        return "queued"
    if status is TaskStatus.RUNNING:
        return "running"
    if status is TaskStatus.COMPLETED:
        return "completed"
    if status is TaskStatus.REJECTED:
        return "rejected"
    return "failed"
