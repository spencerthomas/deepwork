"""Typed state and human-review payloads for the local agent graph."""

from typing import Literal, NotRequired

from typing_extensions import TypedDict

from deepwork_agent.profiles import FinalArtifact, JourneyProfile

AgentStatus = Literal["planned", "approved", "completed", "rejected"]
ApprovalDecision = Literal["approve", "reject", "respond"]
ApprovalStatus = Literal["pending", "approve", "reject", "respond", "not-required"]
ContentTrust = Literal["trusted", "untrusted"]


class AgentInput(TypedDict):
    """Input accepted by the local graph."""

    task: str


class AgentState(AgentInput, total=False):
    """Internal deterministic state accumulated by graph nodes."""

    plan: list[str]
    plan_revision: int
    plan_trust: Literal["untrusted"]
    approval: ApprovalStatus
    reviewer_comment: str
    status: AgentStatus
    final_answer: str
    final_answer_trust: ContentTrust
    profile: JourneyProfile
    final_artifact: FinalArtifact
    rubric_verdict: str
    rubric_repair_history: list[dict[str, object]]


class AgentOutput(TypedDict):
    """Terminal output returned after approval, rejection, or execution."""

    task: str
    plan: list[str]
    plan_revision: int
    plan_trust: Literal["untrusted"]
    approval: ApprovalStatus
    status: AgentStatus
    final_answer: str
    final_answer_trust: ContentTrust
    profile: JourneyProfile
    final_artifact: FinalArtifact
    rubric_verdict: str
    rubric_repair_history: list[dict[str, object]]


class ApprovalRequest(TypedDict):
    """Serializable payload exposed by the LangGraph interrupt."""

    kind: Literal["deepwork-plan-approval"]
    action: Literal["execute_plan"]
    task: str
    plan: list[str]
    plan_revision: int
    plan_trust: Literal["untrusted"]
    allowed_decisions: list[ApprovalDecision]


class ApprovalResponse(TypedDict):
    """Value required when resuming an interrupted graph."""

    decision: ApprovalDecision
    comment: NotRequired[str]


def initial_state(task: str) -> AgentInput:
    """Create validated input without contacting a model or provider."""
    normalized = task.strip()
    if not normalized:
        msg = "task must contain non-whitespace text"
        raise ValueError(msg)
    return {"task": normalized}
