"""Offline evaluation dataset for bounded plan quality."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool

from deepwork_agent import create_graph, initial_state

if TYPE_CHECKING:
    from langchain_core.language_models import LanguageModelInput
    from langchain_core.runnables import Runnable

ToolDefinition = dict[str, Any] | type | Callable[..., Any] | BaseTool
MAX_PLAN_STEPS = 6


class PlannerFakeChatModel(GenericFakeChatModel):
    """Public fake model sufficient for planner-only evaluation cases."""

    def bind_tools(
        self,
        tools: Sequence[ToolDefinition],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,  # noqa: ANN401 - mirrors the public BaseChatModel contract
    ) -> Runnable[LanguageModelInput, AIMessage]:
        """Remain deterministic if the graph factory binds built-in tools."""
        _ = tools, tool_choice, kwargs
        return self


@pytest.mark.parametrize(
    ("task", "plan", "required_terms"),
    [
        (
            "Research a technical claim and write a note.",
            "- Gather evidence.\n- Verify the claim.\n- Write a sourced note.",
            {"evidence", "verify", "write"},
        ),
        (
            "Review a code change.",
            "- Inspect the diff.\n- Run focused tests.\n- Report actionable findings.",
            {"inspect", "tests", "findings"},
        ),
        (
            "Update contributor documentation.",
            "- Read current guidance.\n- Edit the documentation.\n- Validate every command.",
            {"read", "edit", "validate"},
        ),
    ],
)
def test_plans_cover_the_offline_quality_rubric(
    task: str,
    plan: str,
    required_terms: set[str],
) -> None:
    """Every evaluation plan is bounded, ordered, and covers its task rubric."""
    model = PlannerFakeChatModel(messages=iter([AIMessage(content=plan)]))
    graph = create_graph(model=model)

    paused = graph.invoke(
        initial_state(task),
        {"configurable": {"thread_id": task}},
    )
    normalized = " ".join(paused["plan"]).lower()

    assert 1 <= len(paused["plan"]) <= MAX_PLAN_STEPS
    assert all(term in normalized for term in required_terms)
    assert paused["status"] == "planned"
