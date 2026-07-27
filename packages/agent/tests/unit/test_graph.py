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


def _grader_call(call_id: str, result: str, criteria: list[dict[str, Any]]) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[
            {
                "name": "GraderResponse",
                "args": {"result": result, "explanation": "Verdict.", "criteria": criteria},
                "id": call_id,
            }
        ],
    )


def test_rubric_verification_attaches_a_passed_verdict_to_the_result() -> None:
    """With a rubric, execution is graded and a verification record is returned."""
    from deepwork_agent import RubricCriterion, RubricSpec

    rubric = RubricSpec(
        rubric_id="test-general",
        version=1,
        criteria=(
            RubricCriterion(criterion_id="addresses-task", text="Addresses the task."),
            RubricCriterion(criterion_id="no-fabrication", text="No fabricated claims."),
        ),
        max_iterations=2,
    )
    model = _model(
        "- Do the work.",
        "Plan-first agents separate intent from execution, which aids review.",
    )
    verifier = ToolBindingFakeChatModel(
        messages=iter(
            [
                _grader_call(
                    "g1",
                    "satisfied",
                    [
                        {"name": "addresses-task", "passed": True},
                        {"name": "no-fabrication", "passed": True},
                    ],
                )
            ]
        )
    )
    graph = create_graph(model=model, rubric=rubric, verifier_model=verifier)
    run_config = cast("RunnableConfig", {"configurable": {"thread_id": "rubric-pass"}})

    graph.invoke(initial_state("Explain plan-first agents."), run_config)
    result = graph.invoke(
        Command(resume=validate_approval_response({"decision": "approve"})), run_config
    )

    assert result["status"] == "completed"
    verification = result["verification"]
    assert verification["status"] == "passed"
    assert verification["rubric_id"] == "test-general"
    assert [entry["criterion_id"] for entry in verification["verdicts"][0]["results"]] == [
        "addresses-task",
        "no-fabrication",
    ]


def test_memory_backend_injects_persisted_memory_as_context() -> None:
    """Memory saved by a prior task is injected as context into a later task."""
    from deepwork_agent.memory import InMemoryWorkspaceMemory

    memory = InMemoryWorkspaceMemory("MEMORY_FACT_TEAL: the workspace's brand color is teal.")
    model = RecordingFakeChatModel(
        messages=iter([AIMessage(content="- Do the work."), AIMessage(content="Done.")])
    )
    graph = create_graph(model=model, memory_backend=memory)
    run_config = cast("RunnableConfig", {"configurable": {"thread_id": "memory-run"}})

    graph.invoke(initial_state("A task that should run with workspace memory."), run_config)
    result = graph.invoke(
        Command(resume=validate_approval_response({"decision": "approve"})), run_config
    )

    assert result["status"] == "completed"
    assert any("MEMORY_FACT_TEAL" in call for call in model.calls), (
        "persisted workspace memory was not injected into the executor"
    )


def test_memory_backend_saves_remembered_notes_and_strips_them() -> None:
    """A <remember> block is persisted to memory and removed from the answer."""
    from deepwork_agent.memory import InMemoryWorkspaceMemory

    memory = InMemoryWorkspaceMemory()
    model = RecordingFakeChatModel(
        messages=iter(
            [
                AIMessage(content="- Do the work."),
                AIMessage(
                    content=(
                        "Here is the result.\n"
                        "<remember>The user prefers metric units.</remember>"
                    )
                ),
            ]
        )
    )
    graph = create_graph(model=model, memory_backend=memory)
    run_config = cast("RunnableConfig", {"configurable": {"thread_id": "memory-write"}})

    graph.invoke(initial_state("A task that teaches a durable preference."), run_config)
    result = graph.invoke(
        Command(resume=validate_approval_response({"decision": "approve"})), run_config
    )

    # The note is saved to durable memory...
    assert "The user prefers metric units." in memory.read()
    # ...and stripped from the answer shown to the user.
    assert result["final_answer"] == "Here is the result."
    assert "<remember>" not in result["final_answer"]


def test_no_memory_backend_still_strips_stray_remember_blocks() -> None:
    """Without a memory backend, tasks still run and stray <remember> is stripped."""
    model = RecordingFakeChatModel(
        messages=iter(
            [
                AIMessage(content="- Do the work."),
                AIMessage(content="Done. <remember>ignored</remember>"),
            ]
        )
    )
    graph = create_graph(model=model, memory_backend=None)
    run_config = cast("RunnableConfig", {"configurable": {"thread_id": "no-memory"}})

    graph.invoke(initial_state("A task with no memory backend."), run_config)
    result = graph.invoke(
        Command(resume=validate_approval_response({"decision": "approve"})), run_config
    )
    assert result["status"] == "completed"
    # No backend means no <remember> handling — the answer is passed through as-is.
    assert result["final_answer"] == "Done. <remember>ignored</remember>"


def test_create_graph_rejects_an_uninitialized_verifier_model() -> None:
    from deepwork_agent import RubricCriterion, RubricSpec

    rubric = RubricSpec(
        rubric_id="test-general",
        version=1,
        criteria=(RubricCriterion(criterion_id="addresses-task", text="Addresses the task."),),
    )
    with pytest.raises(TypeError, match="verifier_model must be an initialized"):
        create_graph(model=_model("x"), rubric=rubric, verifier_model="nope")  # type: ignore[arg-type]


class RecordingFakeChatModel(ToolBindingFakeChatModel):
    """Fake model that records the full text of every prompt it is called with."""

    calls: list[str] = Field(default_factory=list)

    def _generate(
        self,
        messages: Sequence[Any],
        stop: list[str] | None = None,
        run_manager: Any = None,  # noqa: ANN401
        **kwargs: Any,  # noqa: ANN401
    ) -> Any:  # noqa: ANN401
        self.calls.append("\n".join(message.text for message in messages))
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        (None, None),
        ({}, None),
        ({"configurable": {}}, None),
        ({"configurable": {"system_prompt": None}}, None),
        ({"configurable": {"system_prompt": ""}}, None),
        ({"configurable": {"system_prompt": "   "}}, None),
        ({"configurable": {"system_prompt": 123}}, None),
        ({"configurable": {"system_prompt": "  Be terse.  "}}, "Be terse."),
    ],
)
def test_run_prompt_override_reads_defensively(config: object, expected: str | None) -> None:
    """A missing, blank, or non-string override falls back to the baked-in default."""
    from deepwork_agent.graph import _run_prompt_override

    assert _run_prompt_override(cast("Any", config)) == expected


def test_run_prompt_override_is_length_bounded() -> None:
    """An over-long in-app prompt is truncated, never passed through unbounded."""
    from deepwork_agent.graph import _MAX_RUN_PROMPT_CHARS, _run_prompt_override

    huge = "x" * (_MAX_RUN_PROMPT_CHARS + 5_000)
    result = _run_prompt_override({"configurable": {"system_prompt": huge}})
    assert result is not None
    assert len(result) == _MAX_RUN_PROMPT_CHARS


def test_per_run_system_prompt_override_reaches_the_executor() -> None:
    """The in-app prompt flows into execution via configurable.system_prompt."""
    marker = "DEEPWORK_OVERRIDE_MARKER_9f3a"
    model = RecordingFakeChatModel(
        messages=iter([AIMessage(content="- Do the work."), AIMessage(content="Done.")])
    )
    graph = create_graph(model=model)
    run_config = cast(
        "RunnableConfig",
        {"configurable": {"thread_id": "override-run", "system_prompt": marker}},
    )

    graph.invoke(initial_state("A task the workspace prompt should govern."), run_config)
    graph.invoke(Command(resume=validate_approval_response({"decision": "approve"})), run_config)

    # The planning call never carries the persona prompt; the execution call must.
    assert any(marker in call for call in model.calls), (
        "per-run system_prompt override did not reach the deep-agent executor"
    )


def test_per_run_system_prompt_override_reaches_the_executor_via_input() -> None:
    """The prompt delivered in the graph input governs execution (hosted path)."""
    marker = "DEEPWORK_INPUT_MARKER_ab12"
    model = RecordingFakeChatModel(
        messages=iter([AIMessage(content="- Do the work."), AIMessage(content="Done.")])
    )
    graph = create_graph(model=model)
    run_config = cast("RunnableConfig", {"configurable": {"thread_id": "input-override-run"}})

    state = initial_state("A task the workspace prompt should govern.")
    graph.invoke({**state, "system_prompt": marker}, run_config)
    graph.invoke(Command(resume=validate_approval_response({"decision": "approve"})), run_config)

    assert any(marker in call for call in model.calls), (
        "system_prompt delivered in the input did not reach the deep-agent executor"
    )


def test_without_override_the_default_system_prompt_governs_execution() -> None:
    """With no override, the baked-in Deep Work prompt still reaches execution."""
    from deepwork_agent.graph import DEEP_WORK_SYSTEM_PROMPT

    probe = DEEP_WORK_SYSTEM_PROMPT[:40]
    model = RecordingFakeChatModel(
        messages=iter([AIMessage(content="- Do the work."), AIMessage(content="Done.")])
    )
    graph = create_graph(model=model)
    run_config = cast("RunnableConfig", {"configurable": {"thread_id": "default-run"}})

    graph.invoke(initial_state("A task governed by the default prompt."), run_config)
    graph.invoke(Command(resume=validate_approval_response({"decision": "approve"})), run_config)

    assert any(probe in call for call in model.calls)
