"""Integration proof for nested Deep Agents authorization and streaming."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, cast

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool, tool
from langgraph.types import Command
from pydantic import Field

from deepwork_agent import create_graph, initial_state, validate_approval_response

if TYPE_CHECKING:
    from langchain_core.language_models import LanguageModelInput
    from langchain_core.runnables import Runnable, RunnableConfig

ToolDefinition = dict[str, Any] | type | Callable[..., Any] | BaseTool


class ToolBindingFakeChatModel(GenericFakeChatModel):
    """Deterministic public fake model that supports LangChain tool binding."""

    bound_tool_count: int = Field(default=0)

    def bind_tools(
        self,
        tools: Sequence[ToolDefinition],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,  # noqa: ANN401 - mirrors the public BaseChatModel contract
    ) -> Runnable[LanguageModelInput, AIMessage]:
        """Record binding and remain the runnable used by Deep Agents."""
        _ = tool_choice, kwargs
        self.bound_tool_count = len(tools)
        return self


def _run_config(thread_id: str) -> RunnableConfig:
    return {"configurable": {"thread_id": thread_id}}


def test_tool_call_requires_separate_approval_before_execution() -> None:
    """Plan approval never implicitly authorizes a consequential tool call."""
    calls: list[str] = []

    @tool
    def collect_research_note(topic: str) -> str:
        """Return one deterministic note and record the authorized action."""
        calls.append(topic)
        return f"Verified note about {topic}."

    model = ToolBindingFakeChatModel(
        messages=iter(
            [
                AIMessage(content="- Collect the evidence.\n- Summarize it."),
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "collect_research_note",
                            "args": {"topic": "approval boundaries"},
                            "id": "call-1",
                            "type": "tool_call",
                        }
                    ],
                ),
                AIMessage(content="The authorized evidence was summarized."),
            ]
        )
    )
    graph = create_graph(model=model, tools=[collect_research_note])
    run_config = _run_config("tool-approval")

    plan_pause = cast(
        "dict[str, Any]",
        graph.invoke(initial_state("Research approval boundaries."), run_config),
    )
    assert plan_pause["__interrupt__"][0].value["kind"] == "deepwork-plan-approval"

    tool_pause = cast(
        "dict[str, Any]",
        graph.invoke(
            Command(resume=validate_approval_response({"decision": "approve"})),
            run_config,
        ),
    )
    assert calls == []
    action_request = tool_pause["__interrupt__"][0].value["action_requests"][0]
    assert action_request["name"] == "collect_research_note"
    assert action_request["args"] == {"topic": "approval boundaries"}

    completed = graph.invoke(
        Command(resume={"decisions": [{"type": "approve"}]}),
        run_config,
    )

    assert calls == ["approval boundaries"]
    assert completed["status"] == "completed"
    assert completed["final_answer"] == "The authorized evidence was summarized."
    assert model.bound_tool_count > 0


def test_nested_execution_emits_sanitized_custom_progress() -> None:
    """Callers can observe lifecycle progress without receiving model contents."""
    model = ToolBindingFakeChatModel(
        messages=iter(
            [
                AIMessage(content="Draft the result."),
                AIMessage(content="Completed without a tool."),
            ]
        )
    )
    graph = create_graph(model=model)
    run_config = _run_config("nested-streaming")
    graph.invoke(initial_state("Write a result."), run_config)

    chunks = list(
        graph.stream(
            Command(resume=validate_approval_response({"decision": "approve"})),
            run_config,
            stream_mode=["custom", "updates"],
        )
    )
    custom_events = [
        payload
        for mode, payload in chunks
        if mode == "custom"
        and isinstance(payload, dict)
        and payload.get("kind") == "deepwork-execution"
    ]

    assert custom_events[0] == {"kind": "deepwork-execution", "phase": "started"}
    assert custom_events[-1] == {"kind": "deepwork-execution", "phase": "completed"}
    assert any(event.get("phase") == "node-finished" for event in custom_events)
    assert all("content" not in event for event in custom_events)
