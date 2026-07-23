"""Typed state and human-review payloads for the local agent graph."""

from typing import Literal, NotRequired

from typing_extensions import TypedDict

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
    pending_interrupt_id: str
    approval: ApprovalStatus
    reviewer_comment: str
    requested_plan: list[str]
    status: AgentStatus
    final_answer: str
    final_answer_trust: ContentTrust


class AgentOutput(TypedDict):
    """Terminal output returned after approval, rejection, or execution."""

    task: str
    plan: list[str]
    plan_revision: int
    plan_trust: Literal["untrusted"]
    pending_interrupt_id: str
    approval: ApprovalStatus
    status: AgentStatus
    final_answer: str
    final_answer_trust: ContentTrust


class ApprovalRequest(TypedDict):
    """Serializable payload exposed by the LangGraph interrupt."""

    kind: Literal["deepwork-plan-approval"]
    action: Literal["execute_plan"]
    task: str
    plan: list[str]
    plan_revision: int
    interrupt_id: str
    plan_trust: Literal["untrusted"]
    allowed_decisions: list[ApprovalDecision]


class ApprovalResponse(TypedDict):
    """Value required when resuming an interrupted graph."""

    interrupt_id: str
    revision: int
    decision: ApprovalDecision
    comment: NotRequired[str]
    edited_plan: NotRequired[list[str]]


def initial_state(task: str) -> AgentInput:
    """Create validated input without contacting a model or provider."""
    normalized = task.strip()
    if not normalized:
        msg = "task must contain non-whitespace text"
        raise ValueError(msg)
    return {"task": normalized}
