"""Microbenchmark for the deterministic graph-construction boundary."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool

from deepwork_agent import create_graph

if TYPE_CHECKING:
    from langchain_core.language_models import LanguageModelInput
    from langchain_core.runnables import Runnable
    from pytest_benchmark.fixture import BenchmarkFixture

ToolDefinition = dict[str, Any] | type | Callable[..., Any] | BaseTool


class PlannerFakeChatModel(GenericFakeChatModel):
    """Public fake model with the tool-binding method the factory requires."""

    def bind_tools(
        self,
        tools: Sequence[ToolDefinition],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,  # noqa: ANN401 - mirrors the public BaseChatModel contract
    ) -> Runnable[LanguageModelInput, AIMessage]:
        """Remain deterministic during graph construction."""
        _ = tools, tool_choice, kwargs
        return self


def test_graph_construction_benchmark(benchmark: BenchmarkFixture) -> None:
    """Track graph-factory regressions without making timing a CI gate."""
    model = PlannerFakeChatModel(messages=iter([AIMessage(content="Plan.")]))

    graph = benchmark(lambda: create_graph(model=model))

    assert graph.name == "deep-work-local-agent"
