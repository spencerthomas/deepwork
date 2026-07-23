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
    validate_approval_response,
    validate_plan_edit,
)

if TYPE_CHECKING:
    from langchain_core.language_models import LanguageModelInput
    from langchain_core.runnables import Runnable, RunnableConfig

ToolDefinition = dict[str, Any] | type | Callable[..., Any] | BaseTool
REVISED_PLAN_REVISION = 2


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


def test_runtime_capabilities_are_truthful_and_local_only() -> None:
    """Capability reporting does not imply hosted or credential support."""
    capabilities = runtime_capabilities()

    assert capabilities.runtime_mode == "local-runtime"
    assert capabilities.available is True
    assert capabilities.managed_external_providers == "unavailable"
    assert capabilities.model_injection_required is True
    assert capabilities.plan_first is True
    assert capabilities.human_in_the_loop == "langgraph-interrupt"
    assert capabilities.tool_authorization == "deepagents-interrupt-on"
    assert capabilities.nested_execution_streaming is True
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
        "plan_trust": "untrusted",
        "allowed_decisions": ["approve", "reject", "respond"],
    }

    result = graph.invoke(
        Command(resume=validate_approval_response({"decision": "approve"})),
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

    graph.invoke(initial_state("Prepare a short note."), run_config)
    result = graph.invoke(
        Command(resume=validate_approval_response({"decision": "reject"})),
        run_config,
    )

    assert result["status"] == "rejected"
    assert result["approval"] == "reject"
    assert result["final_answer"] == "Execution was not approved."
    assert result["final_answer_trust"] == "trusted"


def test_approval_can_be_explicitly_disabled_for_local_automation() -> None:
    """Callers may run the same plan-first flow without a pause when reviewed."""
    model = _model("Draft the response.", "A concise completed response.")
    graph = create_graph(
        model=model,
        config=AgentConfig(require_plan_approval=False, require_tool_approval=False),
    )

    result = graph.invoke(
        initial_state("Write a concise response."),
        _run_config("research-writing-no-approval"),
    )

    assert result["plan"] == ["Draft the response."]
    assert result["approval"] == "not-required"
    assert result["status"] == "completed"
    assert result["final_answer"] == "A concise completed response."


def test_unnamed_tools_fail_closed_when_approval_is_required() -> None:
    """An ambiguous tool cannot silently bypass the default authorization gate."""
    model = _model("Draft the response.")

    with pytest.raises(ValueError, match="every tool must expose a name"):
        create_graph(model=model, tools=[cast("Callable[..., Any]", object())])


def test_invalid_resume_is_rejected_before_command_and_does_not_poison_checkpoint() -> None:
    """Callers validate before Command so the same thread can still resume safely."""
    model = _model("Review the evidence.", "The reviewed answer.")
    graph = create_graph(model=model)
    run_config = _run_config("research-writing-invalid-approval")
    graph.invoke(initial_state("Review a short note."), run_config)

    with pytest.raises(ValueError, match="approve, reject, or respond"):
        validate_approval_response({"decision": "edit"})

    result = graph.invoke(
        Command(resume=validate_approval_response({"decision": "approve"})),
        run_config,
    )
    assert result["status"] == "completed"


def test_respond_replans_and_uses_fresh_langgraph_interrupt_authority() -> None:
    """Bounded guidance creates a new revision and official interrupt before execution."""
    model = _model(
        "Inspect the evidence.\nDraft a note.",
        "Use only supplied evidence.\nReturn exactly two sentences.",
        "The revised two-sentence note.",
    )
    graph = create_graph(model=model)
    run_config = _run_config("respond-and-replan")
    first_pause = cast(
        "dict[str, Any]",
        graph.invoke(initial_state("Prepare a short note."), run_config),
    )
    first_interrupt = first_pause["__interrupt__"][0]

    second_pause = cast(
        "dict[str, Any]",
        graph.invoke(
            Command(
                resume=validate_approval_response(
                    {
                        "decision": "respond",
                        "comment": "Use supplied evidence and return two sentences.",
                    }
                )
            ),
            run_config,
        ),
    )
    second_interrupt = second_pause["__interrupt__"][0]

    assert second_pause["plan"] == [
        "Use only supplied evidence.",
        "Return exactly two sentences.",
    ]
    assert second_pause["plan_revision"] == REVISED_PLAN_REVISION
    assert second_interrupt.id != first_interrupt.id
    assert second_interrupt.value["plan_revision"] == REVISED_PLAN_REVISION
    completed = graph.invoke(
        Command(resume=validate_approval_response({"decision": "approve"})),
        run_config,
    )
    assert completed["status"] == "completed"
    assert completed["plan_revision"] == REVISED_PLAN_REVISION
    assert completed["final_answer"] == "The revised two-sentence note."


def test_plan_edit_uses_public_checkpoint_update_then_fresh_approval() -> None:
    """Plan edits are state updates, not respond payload fields."""
    model = _model("Inspect the request.\nDraft the result.", "Edited plan completed.")
    graph = create_graph(model=model)
    run_config = _run_config("checkpoint-plan-edit")
    first_pause = cast(
        "dict[str, Any]",
        graph.invoke(initial_state("Prepare a bounded result."), run_config),
    )
    first_interrupt = first_pause["__interrupt__"][0]
    edited_plan = validate_plan_edit(["Use the supplied inputs only.", "Return a bounded result."])

    graph.update_state(
        run_config,
        {
            "plan": edited_plan,
            "plan_revision": REVISED_PLAN_REVISION,
            "plan_trust": "untrusted",
            "approval": "pending",
            "status": "planned",
        },
        as_node="plan",
    )
    assert graph.get_state(run_config).next == ("approve",)
    second_pause = cast("dict[str, Any]", graph.invoke(None, run_config))
    second_interrupt = second_pause["__interrupt__"][0]

    assert second_pause["plan"] == edited_plan
    assert second_interrupt.value["plan"] == edited_plan
    assert second_interrupt.value["plan_revision"] == REVISED_PLAN_REVISION
    assert second_interrupt.id != first_interrupt.id
    completed = graph.invoke(
        Command(resume=validate_approval_response({"decision": "approve"})),
        run_config,
    )
    assert completed["plan"] == edited_plan
    assert completed["final_answer"] == "Edited plan completed."


@pytest.mark.parametrize(
    "value",
    [[], [""], ["x" * 501], ["a", "b", "c", "d", "e", "f", "g"]],
)
def test_plan_edit_preflight_is_bounded(value: object) -> None:
    """Checkpoint edits are validated before changing graph state."""
    with pytest.raises((TypeError, ValueError), match=r"edited plan|each edited plan"):
        validate_plan_edit(value)


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ({"decision": "respond"}, "non-empty comment"),
        ({"decision": "respond", "comment": "   "}, "non-empty comment"),
        (
            {"decision": "respond", "comment": "x" * 1_001},
            "at most 1000 characters",
        ),
        (
            {"decision": "respond", "comment": "Revise.", "edited_plan": ["No."]},
            "only decision and optional comment",
        ),
    ],
)
def test_respond_preflight_is_bounded(value: object, message: str) -> None:
    """Respond guidance is bounded and cannot smuggle plan edits into resume."""
    with pytest.raises(ValueError, match=message):
        validate_approval_response(value)


def test_create_graph_requires_an_initialized_chat_model() -> None:
    """Provider strings cannot make the package select credentials implicitly."""
    with pytest.raises(TypeError, match="initialized BaseChatModel"):
        create_graph(model="provider:model")  # type: ignore[arg-type]
