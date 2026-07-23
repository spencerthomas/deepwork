"""Shared plan-first nodes and review validators for Deep Work graphs.

Both the general local graph and the journey graphs compose these nodes so the
plan-approval pause stays one official LangGraph interrupt boundary with one
payload contract, instead of drifting into per-graph variants.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal, Protocol, cast

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import interrupt

# LangGraph resolves node and branch type hints at runtime, so the state types
# referenced in annotations below must stay imported at runtime.
from deepwork_agent.state import (
    AgentState,  # noqa: TC001
    ApprovalRequest,  # noqa: TC001
    ApprovalResponse,  # noqa: TC001
)

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langchain_core.messages import BaseMessage

    from deepwork_agent.state import ApprovalDecision


class PlanFlowNode(Protocol):
    """Graph node over the shared plan-first state with a named parameter."""

    def __call__(self, state: AgentState) -> dict[str, object]:
        """Return a LangGraph state update for the shared plan-first flow."""
        ...


PROTECTED_ACTION = "execute_plan"
PLAN_SYSTEM_PROMPT = (
    "Create a short execution plan for the task. Return one concrete step per line, "
    "with no preamble. Do not perform the task yet."
)
REVISE_SYSTEM_PROMPT = (
    "Revise the plan using the reviewer response. Return one concrete "
    "step per line with no preamble. Do not perform the task yet."
)
_STEP_PREFIX = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s*")
_MAX_REVIEW_COMMENT_LENGTH = 1_000
_MAX_PLAN_STEP_LENGTH = 500
_MAX_PLAN_STEPS = 12


def message_text(message: BaseMessage) -> str:
    """Return normalized text from a model message or fail closed."""
    text = message.text.strip()
    if not text:
        msg = "model response must contain text"
        raise ValueError(msg)
    return text


def parse_plan(message: BaseMessage, *, limit: int) -> list[str]:
    """Parse a bounded, ordered plan from plain model text."""
    steps = [
        _STEP_PREFIX.sub("", line).strip()
        for line in message_text(message).splitlines()
        if line.strip()
    ]
    steps = [step for step in steps if step][:limit]
    if not steps:
        msg = "model response did not contain an executable plan"
        raise ValueError(msg)
    return steps


def validate_approval_response(value: object) -> ApprovalResponse:
    """Validate a resume value before callers construct a LangGraph Command."""
    if not isinstance(value, dict):
        msg = "approval response must be a mapping"
        raise TypeError(msg)
    mapping = cast("dict[str, object]", value)
    if not set(mapping).issubset({"decision", "comment"}) or "decision" not in mapping:
        msg = "approval response may contain only decision and optional comment"
        raise ValueError(msg)
    decision = mapping["decision"]
    if decision not in ("approve", "reject", "respond"):
        msg = "approval decision must be approve, reject, or respond"
        raise ValueError(msg)
    comment = mapping.get("comment")
    if comment is not None and not isinstance(comment, str):
        msg = "approval comment must be text"
        raise ValueError(msg)
    normalized_comment = comment.strip() if isinstance(comment, str) else None
    if normalized_comment is not None and len(normalized_comment) > _MAX_REVIEW_COMMENT_LENGTH:
        msg = "approval comment must contain at most 1000 characters"
        raise ValueError(msg)
    if decision == "respond" and not normalized_comment:
        msg = "respond requires a non-empty comment"
        raise ValueError(msg)
    response: ApprovalResponse = {"decision": cast("ApprovalDecision", decision)}
    if normalized_comment:
        response["comment"] = normalized_comment
    return response


def validate_plan_edit(value: object, *, max_plan_steps: int = 6) -> list[str]:
    """Bound a plan before an official ``update_state(..., as_node="plan")`` edit."""
    if not 1 <= max_plan_steps <= _MAX_PLAN_STEPS:
        msg = "max_plan_steps must be between 1 and 12"
        raise ValueError(msg)
    if not isinstance(value, list) or not value or len(value) > max_plan_steps:
        msg = f"edited plan must contain between 1 and {max_plan_steps} steps"
        raise ValueError(msg)
    steps: list[str] = []
    for item in value:
        if not isinstance(item, str):
            msg = "each edited plan step must be text"
            raise TypeError(msg)
        step = item.strip()
        if not step or len(step) > _MAX_PLAN_STEP_LENGTH:
            msg = "each edited plan step must contain 1 to 500 characters"
            raise ValueError(msg)
        steps.append(step)
    return steps


def build_plan_node(
    model: BaseChatModel,
    *,
    max_plan_steps: int,
) -> PlanFlowNode:
    """Create the plan node that turns the task into a bounded untrusted plan."""

    def plan(state: AgentState) -> dict[str, object]:
        task = state["task"].strip()
        if not task:
            msg = "task must contain non-whitespace text"
            raise ValueError(msg)
        response = model.invoke(
            [
                SystemMessage(content=PLAN_SYSTEM_PROMPT),
                HumanMessage(content=task),
            ]
        )
        parsed_plan = parse_plan(response, limit=max_plan_steps)
        return {
            "task": task,
            "plan": parsed_plan,
            "plan_revision": 1,
            "plan_trust": "untrusted",
            "approval": "pending",
            "status": "planned",
        }

    return plan


def build_approve_node(
    *,
    require_plan_approval: bool,
) -> PlanFlowNode:
    """Create the approval node around the official LangGraph interrupt."""

    def approve(state: AgentState) -> dict[str, object]:
        if not require_plan_approval:
            return {"approval": "not-required", "status": "approved"}
        request: ApprovalRequest = {
            "kind": "deepwork-plan-approval",
            "action": PROTECTED_ACTION,
            "task": state["task"],
            "plan": list(state["plan"]),
            "plan_revision": state["plan_revision"],
            "plan_trust": "untrusted",
            "allowed_decisions": ["approve", "reject", "respond"],
        }
        response = validate_approval_response(interrupt(request))
        decision = response["decision"]
        status = (
            "approved"
            if decision == "approve"
            else "rejected"
            if decision == "reject"
            else "planned"
        )
        return {
            "approval": decision,
            "reviewer_comment": response.get("comment", ""),
            "status": status,
        }

    return approve


def route_after_approval(state: AgentState) -> Literal["execute", "reject", "revise"]:
    """Route an approval decision to execution, rejection, or replanning."""
    if state["approval"] == "reject":
        return "reject"
    if state["approval"] == "respond":
        return "revise"
    return "execute"


def build_revise_node(
    model: BaseChatModel,
    *,
    max_plan_steps: int,
) -> PlanFlowNode:
    """Create the revise node that replans from bounded reviewer guidance."""

    def revise(state: AgentState) -> dict[str, object]:
        current_plan = "\n".join(f"- {step}" for step in state["plan"])
        response = model.invoke(
            [
                SystemMessage(content=REVISE_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"Task:\n{state['task']}\n\nCurrent plan:\n{current_plan}\n\n"
                        f"Reviewer response:\n{state['reviewer_comment']}"
                    )
                ),
            ]
        )
        return {
            "plan": parse_plan(response, limit=max_plan_steps),
            "plan_revision": state["plan_revision"] + 1,
            "plan_trust": "untrusted",
            "approval": "pending",
            "status": "planned",
        }

    return revise


def reject_node(state: AgentState) -> dict[str, object]:
    """Terminate a rejected run with a trusted local message."""
    _ = state
    return {
        "status": "rejected",
        "final_answer": "Execution was not approved.",
        "final_answer_trust": "trusted",
    }


def numbered_plan_request(task: str, plan: list[str], *, closing: str) -> str:
    """Compose the execution request from the approved task and plan."""
    numbered_plan = "\n".join(f"{index}. {step}" for index, step in enumerate(plan, start=1))
    return f"Task:\n{task}\n\nApproved plan:\n{numbered_plan}\n\n{closing}"
