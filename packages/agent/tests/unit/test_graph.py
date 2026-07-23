"""Credential-free tests for the plan-first Deep Work graph."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, cast

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool, tool
from langgraph.types import Command
from pydantic import Field

from deepwork_agent import (
    PROTECTED_ACTION,
    AgentConfig,
    create_graph,
    initial_state,
    runtime_capabilities,
)

if TYPE_CHECKING:
    from langchain_core.language_models import LanguageModelInput
    from langchain_core.runnables import Runnable, RunnableConfig

ToolDefinition = dict[str, Any] | type | Callable[..., Any] | BaseTool


class ToolBindingFakeChatModel(GenericFakeChatModel):
    """Official fake model with the tool-binding method agents require."""

    bound_tool_count: int = Field(default=0)
    bound_tool_names: tuple[str, ...] = Field(default=())

    def bind_tools(
        self,
        tools: Sequence[ToolDefinition],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,  # noqa: ANN401 - mirrors the public BaseChatModel contract
    ) -> Runnable[LanguageModelInput, AIMessage]:
        """Record tool binding and remain a deterministic runnable."""
        _ = tool_choice, kwargs
        self.bound_tool_count = len(tools)
        names: list[str] = []
        for candidate in tools:
            if isinstance(candidate, BaseTool):
                names.append(candidate.name)
            elif isinstance(candidate, dict):
                name = candidate.get("name")
                function = candidate.get("function")
                if not isinstance(name, str) and isinstance(function, dict):
                    name = function.get("name")
                if isinstance(name, str):
                    names.append(name)
            else:
                name = getattr(candidate, "__name__", None)
                if isinstance(name, str):
                    names.append(name)
        self.bound_tool_names = tuple(names)
        return self


@tool
def collect_research_note(topic: str) -> str:
    """Return a deterministic research note for a topic."""
    return f"Verified note about {topic}."


def _run_config(thread_id: str) -> RunnableConfig:
    return {"configurable": {"thread_id": thread_id}}


def _model(*responses: str) -> ToolBindingFakeChatModel:
    return ToolBindingFakeChatModel(
        messages=iter(AIMessage(content=response) for response in responses)
    )


def _resume_value(
    request: dict[str, Any],
    decision: str,
    *,
    comment: str | None = None,
    edited_plan: list[str] | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "interrupt_id": request["interrupt_id"],
        "revision": request["plan_revision"],
        "decision": decision,
    }
    if comment is not None:
        value["comment"] = comment
    if edited_plan is not None:
        value["edited_plan"] = edited_plan
    return value


def test_runtime_capabilities_are_truthful_and_local_only() -> None:
    """Capability reporting does not imply hosted or credential support."""
    capabilities = runtime_capabilities()

    assert capabilities.runtime_mode == "local-runtime"
    assert capabilities.available is True
    assert capabilities.external_providers == "unavailable"
    assert capabilities.model_injection_required is True
    assert capabilities.plan_first is True
    assert capabilities.human_in_the_loop == "langgraph-interrupt"
    assert capabilities.checkpointing == "in-memory-only"
    assert capabilities.hosted_deployment is False
    assert capabilities.provider_credentials_managed is False


def test_research_writing_task_plans_pauses_and_completes_after_approval() -> None:
    """A fake model proves the full local plan/approval/final-answer path."""
    model = _model(
        "- Gather the relevant evidence.\n- Draft a concise source-aware note.",
        "Plan-first work improves reviewability by separating intent from execution.",
    )
    graph = create_graph(model=model, tools=[collect_research_note])
    run_config = _run_config("research-writing-approved")

    paused = cast(
        "dict[str, Any]",
        graph.invoke(
            initial_state("Research and write a note about plan-first agents."),
            run_config,
        ),
    )

    assert paused["plan"] == [
        "Gather the relevant evidence.",
        "Draft a concise source-aware note.",
    ]
    assert paused["plan_trust"] == "untrusted"
    assert paused["approval"] == "pending"
    assert paused["status"] == "planned"
    assert "final_answer" not in paused
    interrupts = paused["__interrupt__"]
    assert len(interrupts) == 1
    request = interrupts[0].value
    assert request == {
        "kind": "deepwork-plan-approval",
        "action": PROTECTED_ACTION,
        "task": "Research and write a note about plan-first agents.",
        "plan": [
            "Gather the relevant evidence.",
            "Draft a concise source-aware note.",
        ],
        "plan_revision": 1,
        "interrupt_id": paused["pending_interrupt_id"],
        "plan_trust": "untrusted",
        "allowed_decisions": ["approve", "reject", "respond"],
    }

    result = graph.invoke(
        Command(resume=_resume_value(request, "approve")),
        run_config,
    )

    assert result["status"] == "completed"
    assert result["approval"] == "approve"
    assert result["final_answer"] == (
        "Plan-first work improves reviewability by separating intent from execution."
    )
    assert result["final_answer_trust"] == "untrusted"
    assert model.bound_tool_count > 0
    assert "collect_research_note" in model.bound_tool_names
    restored = graph.get_state(run_config)
    assert restored.values["plan"] == result["plan"]
    assert restored.values["final_answer"] == result["final_answer"]
    assert restored.next == ()


def test_rejection_ends_without_executing_the_deep_agent() -> None:
    """A rejected plan returns a trusted local message without another model call."""
    model = _model("1. Inspect the evidence.\n2. Write the answer.")
    graph = create_graph(model=model)
    run_config = _run_config("research-writing-rejected")

    paused = cast(
        "dict[str, Any]",
        graph.invoke(initial_state("Prepare a short note."), run_config),
    )
    request = cast("dict[str, Any]", paused["__interrupt__"][0].value)
    result = graph.invoke(Command(resume=_resume_value(request, "reject")), run_config)

    assert result["status"] == "rejected"
    assert result["approval"] == "reject"
    assert result["final_answer"] == "Execution was not approved."
    assert result["final_answer_trust"] == "trusted"


def test_approval_can_be_explicitly_disabled_for_local_automation() -> None:
    """Callers may run the same plan-first flow without a pause when reviewed."""
    model = _model("Draft the response.", "A concise completed response.")
    graph = create_graph(
        model=model,
        config=AgentConfig(require_plan_approval=False),
    )

    result = graph.invoke(
        initial_state("Write a concise response."),
        _run_config("research-writing-no-approval"),
    )

    assert result["plan"] == ["Draft the response."]
    assert result["approval"] == "not-required"
    assert result["status"] == "completed"
    assert result["final_answer"] == "A concise completed response."


def test_invalid_resume_payload_fails_closed() -> None:
    """The approval node accepts only the documented decision vocabulary."""
    model = _model("Review the evidence.")
    graph = create_graph(model=model)
    run_config = _run_config("research-writing-invalid-approval")
    paused = cast(
        "dict[str, Any]",
        graph.invoke(initial_state("Review a short note."), run_config),
    )
    request = cast("dict[str, Any]", paused["__interrupt__"][0].value)

    with pytest.raises(ValueError, match="approve, reject, or respond"):
        graph.invoke(Command(resume=_resume_value(request, "edit")), run_config)


def test_respond_with_edited_plan_creates_exact_next_review_before_execution() -> None:
    """A reviewer edit advances one revision and requires a fresh exact approval."""

    model = _model(
        "Inspect the request.\nDraft the result.",
        "Completed using the reviewer-edited plan.",
    )
    graph = create_graph(model=model)
    run_config = _run_config("reviewer-edit")
    first_pause = cast(
        "dict[str, Any]",
        graph.invoke(initial_state("Prepare a bounded note."), run_config),
    )
    first_request = cast("dict[str, Any]", first_pause["__interrupt__"][0].value)
    edited_plan = ["Use the supplied evidence only.", "Return a two-sentence note."]

    second_pause = cast(
        "dict[str, Any]",
        graph.invoke(
            Command(
                resume=_resume_value(
                    first_request,
                    "respond",
                    comment="Use this tighter plan.",
                    edited_plan=edited_plan,
                )
            ),
            run_config,
        ),
    )
    second_request = cast("dict[str, Any]", second_pause["__interrupt__"][0].value)

    assert second_request["plan"] == edited_plan
    assert second_request["plan_revision"] == 2
    assert second_request["interrupt_id"] != first_request["interrupt_id"]
    completed = graph.invoke(
        Command(resume=_resume_value(second_request, "approve")),
        run_config,
    )
    assert completed["plan"] == edited_plan
    assert completed["plan_revision"] == 2
    assert completed["final_answer"] == "Completed using the reviewer-edited plan."


def test_respond_requires_comment_and_exact_interrupt_revision() -> None:
    """Resume cannot omit feedback or target stale review authority."""

    graph = create_graph(model=_model("Inspect the request."))
    run_config = _run_config("stale-review")
    paused = cast(
        "dict[str, Any]",
        graph.invoke(initial_state("Review a note."), run_config),
    )
    request = cast("dict[str, Any]", paused["__interrupt__"][0].value)

    with pytest.raises(ValueError, match="non-empty comment"):
        graph.invoke(Command(resume=_resume_value(request, "respond")), run_config)

    stale = _resume_value(request, "approve")
    stale["revision"] = 2
    with pytest.raises(ValueError, match="stale or different plan revision"):
        graph.invoke(Command(resume=stale), run_config)


def test_create_graph_requires_an_initialized_chat_model() -> None:
    """Provider strings cannot make the package select credentials implicitly."""
    with pytest.raises(TypeError, match="initialized BaseChatModel"):
        create_graph(model="provider:model")  # type: ignore[arg-type]
