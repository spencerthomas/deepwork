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

from deepwork_api.contracts._text import reject_unsafe_controls
from deepwork_api.domain import (
    MAX_PLAN_REVISION,
    MAX_PLAN_STEP_LENGTH,
    MAX_PLAN_STEPS,
    MAX_TASK_OBJECTIVE_LENGTH,
    MAX_TASK_RESULT_LENGTH,
    CancellationRecord,
    CodingOutcome,
    DecisionBatchRecord,
    DecisionRecord,
    DecisionType,
    DecisionValue,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSource,
    PlanUpdateRecord,
    ProposedPlan,
    TaskEvent,
    TaskEventName,
    TaskJourney,
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
AgentId = Annotated[str, StringConstraints(pattern=_SOURCE_SAFE_IDENTIFIER)]
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
    "cancelled",
]
type TaskEvidenceClass = Literal["fixture", "local-source"]


class _TaskWireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class TaskCreateRequest(_TaskWireModel):
    """Bounded local task creation request."""

    prompt: str = Field(min_length=1, max_length=MAX_TASK_OBJECTIVE_LENGTH)
    agent_id: AgentId | None = Field(
        default=None,
        alias="agentId",
        description=(
            "Optional identifier of a registered agent to run this task with. "
            "Omit to use the deployment's default assistant and the workspace "
            "system prompt."
        ),
    )
    journey: Literal["coding"] | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    repository_id: Literal["fixture_repo_deepwork"] | None = Field(
        default=None,
        alias="repositoryId",
        exclude_if=lambda value: value is None,
    )

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str) -> str:
        """Reject blank or control-bearing prompt input."""

        reject_unsafe_controls(value)
        if not value.strip():
            raise ValueError("prompt must contain visible text")
        return value

    @model_validator(mode="after")
    def validate_coding_binding(self) -> TaskCreateRequest:
        if (self.journey == "coding") != (self.repository_id is not None):
            raise ValueError("coding journey requires the reviewed fixture repository")
        return self


class TaskAcceptedResponse(_TaskWireModel):
    """Queued task receipt returned before background work starts."""

    task_id: TaskId = Field(alias="taskId")
    run_id: RunId = Field(alias="runId")
    status: Literal["queued"] = "queued"

    @classmethod
    def from_domain(cls, task: TaskSnapshot) -> TaskAcceptedResponse:
        return cls(task_id=task.task_id, run_id=task.run_id)


class PlanStepArgs(_TaskWireModel):
    """Bounded positional arguments for one fixture plan step."""

    position: int = Field(strict=True, ge=1, le=MAX_PLAN_STEPS)
    text: str = Field(min_length=1, max_length=MAX_PLAN_STEP_LENGTH)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        reject_unsafe_controls(value)
        if not value.strip():
            raise ValueError("plan step must contain visible text")
        return value


class ActionRequestResponse(_TaskWireModel):
    """One action in an ordered pending interrupt."""

    name: Literal["execute_plan_step"] = "execute_plan_step"
    args: PlanStepArgs
    description: str | None = Field(
        default=None,
        max_length=300,
        exclude_if=lambda value: value is None,
    )


class ReviewConfigResponse(_TaskWireModel):
    """Allowed decisions aligned to one action by array position."""

    action_name: Literal["execute_plan_step"] = Field(
        default="execute_plan_step", alias="actionName"
    )
    allowed_decisions: tuple[DecisionType, ...] = Field(alias="allowedDecisions")
    args_schema: dict[str, object] | None = Field(
        default=None,
        alias="argsSchema",
        exclude_if=lambda value: value is None,
    )


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
    version: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        exclude_if=lambda value: value is None,
    )
    action_requests: tuple[ActionRequestResponse, ...] | None = Field(
        default=None,
        alias="actionRequests",
        exclude_if=lambda value: value is None,
    )
    review_configs: tuple[ReviewConfigResponse, ...] | None = Field(
        default=None,
        alias="reviewConfigs",
        exclude_if=lambda value: value is None,
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
    agent_id: AgentId | None = Field(default=None, alias="agentId")
    # Null only for tasks migrated from a pre-timestamp schema; the field stays
    # present on the wire so clients can distinguish "unknown" from a real time.
    created_at: str | None = Field(alias="createdAt", min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=80)
    objective: str = Field(min_length=1, max_length=MAX_TASK_OBJECTIVE_LENGTH)
    status: TaskWireStatus
    last_event_id: int = Field(alias="lastEventId", ge=1)
    journey: Literal["coding"] | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )

    @classmethod
    def from_domain(cls, task: TaskSnapshot) -> TaskSummaryResponse:
        return cls(
            task_id=task.task_id,
            run_id=task.run_id,
            agent_id=task.agent_id,
            created_at=task.created_at,
            title=task.title,
            objective=task.objective,
            status=_wire_status(task.status),
            last_event_id=task.last_event_id,
            journey=("coding" if task.journey is TaskJourney.CODING else None),
        )


class TaskListResponse(_TaskWireModel):
    """Deterministically ordered task collection."""

    items: tuple[TaskSummaryResponse, ...]


class CodingOutcomeResponse(_TaskWireModel):
    """Exact-revision coding evidence with an explicit fixture truth class."""

    evidence_class: Literal["fixture"] = Field(alias="evidenceClass")
    repository_id: Literal["fixture_repo_deepwork"] = Field(alias="repositoryId")
    repository: str = Field(min_length=1, max_length=200)
    base_branch: str = Field(alias="baseBranch", min_length=1, max_length=100)
    base_sha: str = Field(alias="baseSha", pattern=r"^[a-f0-9]{40}$")
    head_sha: str = Field(alias="headSha", pattern=r"^[a-f0-9]{40}$")
    environment: str = Field(min_length=1, max_length=200)
    environment_version: int = Field(alias="environmentVersion", strict=True, ge=1)
    snapshot_digest: str = Field(alias="snapshotDigest", pattern=r"^sha256:[a-f0-9]{16,64}$")
    sandbox_state: Literal["cleaned"] = Field(alias="sandboxState")
    setup_status: Literal["passed"] = Field(alias="setupStatus")
    changed_files: tuple[str, ...] = Field(alias="changedFiles", min_length=1, max_length=100)
    draft_pr_number: int = Field(alias="draftPrNumber", strict=True, ge=1)
    draft_pr_status: Literal["draft"] = Field(alias="draftPrStatus")
    pr_create_attempts: int = Field(alias="prCreateAttempts", strict=True, ge=1)
    reconciled_after_timeout: bool = Field(alias="reconciledAfterTimeout")
    checks: tuple[str, ...] = Field(min_length=1, max_length=50)
    merge_state: Literal["unavailable"] = Field(alias="mergeState")

    @classmethod
    def from_domain(cls, coding: CodingOutcome) -> CodingOutcomeResponse:
        return cls(
            evidence_class=coding.evidence_class,
            repository_id=coding.repository_id,
            repository=coding.repository,
            base_branch=coding.base_branch,
            base_sha=coding.base_sha,
            head_sha=coding.head_sha,
            environment=coding.environment,
            environment_version=coding.environment_version,
            snapshot_digest=coding.snapshot_digest,
            sandbox_state=coding.sandbox_state,
            setup_status=coding.setup_status,
            changed_files=coding.changed_files,
            draft_pr_number=coding.draft_pr_number,
            draft_pr_status=coding.draft_pr_status,
            pr_create_attempts=coding.pr_create_attempts,
            reconciled_after_timeout=coding.reconciled_after_timeout,
            checks=coding.checks,
            merge_state=coding.merge_state,
        )


class TaskDetailResponse(TaskSummaryResponse):
    """Task summary plus the currently actionable interrupt."""

    pending_interrupt: PendingInterruptResponse | None = Field(alias="pendingInterrupt")
    proposed_plan: ProposedPlanResponse | None = Field(alias="proposedPlan")
    evidence: tuple[EvidenceResponse, ...]
    result: str | None = Field(default=None, max_length=MAX_TASK_RESULT_LENGTH)
    coding: CodingOutcomeResponse | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )

    @classmethod
    def from_domain(
        cls,
        task: TaskSnapshot,
        *,
        batch_allowed_decisions: tuple[DecisionType, ...] | None = (
            DecisionType.APPROVE,
            DecisionType.EDIT,
            DecisionType.REJECT,
        ),
    ) -> TaskDetailResponse:
        pending = (
            PendingInterruptResponse(
                interrupt_id=task.pending_interrupt_id,
                plan_revision=task.proposed_plan.revision,
                version=(
                    str(task.proposed_plan.revision)
                    if batch_allowed_decisions is not None
                    else None
                ),
                action_requests=(
                    tuple(
                        ActionRequestResponse(
                            args=PlanStepArgs(position=position, text=step),
                        )
                        for position, step in enumerate(task.proposed_plan.steps, start=1)
                    )
                    if batch_allowed_decisions is not None
                    else None
                ),
                review_configs=(
                    tuple(
                        ReviewConfigResponse(allowed_decisions=batch_allowed_decisions)
                        for _ in task.proposed_plan.steps
                    )
                    if batch_allowed_decisions is not None
                    else None
                ),
            )
            if task.pending_interrupt_id is not None and task.proposed_plan is not None
            else None
        )
        return cls(
            task_id=task.task_id,
            run_id=task.run_id,
            agent_id=task.agent_id,
            created_at=task.created_at,
            title=task.title,
            objective=task.objective,
            status=_wire_status(task.status),
            last_event_id=task.last_event_id,
            journey=("coding" if task.journey is TaskJourney.CODING else None),
            pending_interrupt=pending,
            proposed_plan=(
                ProposedPlanResponse.from_domain(task.proposed_plan)
                if task.proposed_plan is not None
                else None
            ),
            evidence=tuple(EvidenceResponse.from_domain(item) for item in task.evidence),
            result=task.result,
            coding=(
                CodingOutcomeResponse.from_domain(task.coding) if task.coding is not None else None
            ),
        )


class ApproveDecisionRequest(_TaskWireModel):
    type: Literal["approve"]


class EditedActionRequest(_TaskWireModel):
    name: str = Field(min_length=1, max_length=100)
    args: PlanStepArgs


class EditDecisionRequest(_TaskWireModel):
    type: Literal["edit"]
    edited_action: EditedActionRequest = Field(alias="editedAction")


class RejectDecisionRequest(_TaskWireModel):
    type: Literal["reject"]
    message: str | None = Field(default=None, max_length=1_000)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str | None) -> str | None:
        if value is not None:
            reject_unsafe_controls(value)
        return value


class RespondDecisionRequest(_TaskWireModel):
    type: Literal["respond"]
    message: str = Field(min_length=1, max_length=1_000)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        reject_unsafe_controls(value)
        if not value.strip():
            raise ValueError("respond requires a non-blank message")
        return value


OrderedDecisionRequest = Annotated[
    ApproveDecisionRequest | EditDecisionRequest | RejectDecisionRequest | RespondDecisionRequest,
    Field(discriminator="type"),
]


class DecisionBatchRequest(_TaskWireModel):
    """One complete ordered vector for the exact reviewed interrupt version."""

    interrupt_id: InterruptId = Field(alias="interruptId")
    expected_version: str = Field(alias="expectedVersion", min_length=1, max_length=64)
    idempotency_key: str = Field(
        alias="idempotencyKey",
        min_length=1,
        max_length=128,
    )
    decisions: tuple[OrderedDecisionRequest, ...] = Field(min_length=1, max_length=MAX_PLAN_STEPS)

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency_key(cls, value: str) -> str:
        reject_unsafe_controls(value)
        if not value.strip():
            raise ValueError("idempotency key must contain visible text")
        return value


class DecisionBatchAcceptedResponse(_TaskWireModel):
    """Accepted or idempotently replayed ordered decision receipt."""

    task_id: TaskId = Field(alias="taskId")
    run_id: RunId = Field(alias="runId")
    interrupt_id: InterruptId = Field(alias="interruptId")
    version: str = Field(min_length=1, max_length=64)
    decision_types: tuple[DecisionType, ...] = Field(alias="decisionTypes")
    status: Literal["accepted"] = "accepted"
    duplicate: bool

    @classmethod
    def from_domain(cls, record: DecisionBatchRecord) -> DecisionBatchAcceptedResponse:
        return cls(
            task_id=record.task_id,
            run_id=record.run_id,
            interrupt_id=record.interrupt_id,
            version=record.version,
            decision_types=record.decision_types,
            duplicate=record.duplicate,
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
            reject_unsafe_controls(value)
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


class CancellationAcceptedResponse(_TaskWireModel):
    """Accepted or idempotently replayed task cancellation receipt."""

    task_id: TaskId = Field(alias="taskId")
    run_id: RunId = Field(alias="runId")
    status: Literal["cancelled"] = "cancelled"
    duplicate: bool

    @classmethod
    def from_domain(cls, record: CancellationRecord) -> CancellationAcceptedResponse:
        return cls(
            task_id=record.task_id,
            run_id=record.run_id,
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
            reject_unsafe_controls(step)
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
    agent_id: AgentId | None = Field(default=None, alias="agentId")
    journey: Literal["coding"] | None = Field(default=None, exclude_if=lambda value: value is None)
    repository_id: Literal["fixture_repo_deepwork"] | None = Field(
        default=None,
        alias="repositoryId",
        exclude_if=lambda value: value is None,
    )
    status: Literal["queued"]


class RunStartedEventData(_TaskWireModel):
    run_id: RunId = Field(alias="runId")
    status: Literal["running"]


class ContentDeltaEventData(_TaskWireModel):
    text: str = Field(min_length=1, max_length=MAX_TASK_RESULT_LENGTH)
    evidence_class: TaskEvidenceClass = Field(alias="evidenceClass")


class PlanProposedEventData(_TaskWireModel):
    title: str = Field(min_length=1, max_length=100)
    steps: tuple[str, ...] = Field(min_length=1, max_length=MAX_PLAN_STEPS)
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
    decision_types: tuple[DecisionType, ...] | None = Field(
        default=None,
        alias="decisionTypes",
        exclude_if=lambda value: value is None,
    )


class EvidenceRecordedEventData(EvidenceResponse):
    """Replayable evidence metadata without source content."""


class RunCompletedEventData(_TaskWireModel):
    run_id: RunId = Field(alias="runId")
    status: Literal["completed", "rejected", "failed", "cancelled"]
    safe_reason: str = Field(alias="safeReason", min_length=1, max_length=200)
    result_available: bool = Field(alias="resultAvailable")


class CodingCompletedEventData(CodingOutcomeResponse):
    """Replayable credential-free coding proof for the exact retained revision."""


_EVENT_MODELS: dict[TaskEventName, type[BaseModel]] = {
    TaskEventName.TASK_CREATED: TaskCreatedEventData,
    TaskEventName.RUN_STARTED: RunStartedEventData,
    TaskEventName.CONTENT_DELTA: ContentDeltaEventData,
    TaskEventName.PLAN_PROPOSED: PlanProposedEventData,
    TaskEventName.PLAN_UPDATED: PlanProposedEventData,
    TaskEventName.EVIDENCE_RECORDED: EvidenceRecordedEventData,
    TaskEventName.INTERRUPT_REQUESTED: InterruptRequestedEventData,
    TaskEventName.DECISION_RECORDED: DecisionRecordedEventData,
    TaskEventName.CODING_COMPLETED: CodingCompletedEventData,
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
    if status is TaskStatus.CANCELLED:
        return "cancelled"
    return "failed"
