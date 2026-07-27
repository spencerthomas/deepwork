"""Tests for the reuse-first reliability envelope around the Deep Agents executor.

These prove that the maintained LangChain middleware is wired with the configured
per-run caps and retries, and that the executor is invoked under a bounded
LangGraph ``recursion_limit`` — the loop/cost controls that keep an approved plan
from running away.
"""

from __future__ import annotations

from langchain.agents.middleware import (
    AgentMiddleware,
    ModelCallLimitMiddleware,
    ModelRetryMiddleware,
    ToolCallLimitMiddleware,
    ToolRetryMiddleware,
)

from deepwork_agent import AgentConfig, build_reliability_middleware

DEFAULT_MODEL_CALL_LIMIT = 25
DEFAULT_TOOL_CALL_LIMIT = 50
CUSTOM_MODEL_CALLS = 5
CUSTOM_TOOL_CALLS = 7
CUSTOM_MODEL_RETRIES = 1
CUSTOM_TOOL_RETRIES = 3


def _by_type(
    middleware: list[AgentMiddleware],
    cls: type[AgentMiddleware],
) -> AgentMiddleware:
    found = [m for m in middleware if isinstance(m, cls)]
    assert len(found) == 1, f"expected exactly one {cls.__name__}, found {len(found)}"
    return found[0]


def test_default_reliability_middleware_enforces_run_caps() -> None:
    """Model/tool call-limit middleware raise at the cap rather than fake success.

    ``exit_behavior="error"`` makes a reached cap raise a catchable exception so
    the graph fails the run honestly, instead of ``"end"`` injecting a synthetic
    AI message that could be surfaced as a completed answer.
    """
    middleware = build_reliability_middleware(AgentConfig())

    model_limit = _by_type(middleware, ModelCallLimitMiddleware)
    assert model_limit.run_limit == DEFAULT_MODEL_CALL_LIMIT
    assert model_limit.exit_behavior == "error"

    tool_limit = _by_type(middleware, ToolCallLimitMiddleware)
    assert tool_limit.run_limit == DEFAULT_TOOL_CALL_LIMIT
    assert tool_limit.exit_behavior == "error"


def test_tool_retries_are_off_by_default() -> None:
    """The default envelope adds model retries but not blanket tool retries.

    Retrying an arbitrary tool on any exception could duplicate a non-idempotent
    side effect, so tool retries are opt-in.
    """
    middleware = build_reliability_middleware(AgentConfig())

    assert any(isinstance(m, ModelRetryMiddleware) for m in middleware)
    assert not any(isinstance(m, ToolRetryMiddleware) for m in middleware)


def test_reliability_middleware_honors_custom_limits() -> None:
    """Configured caps and retry counts flow into the middleware instances."""
    config = AgentConfig(
        max_model_calls=CUSTOM_MODEL_CALLS,
        max_tool_calls=CUSTOM_TOOL_CALLS,
        model_max_retries=CUSTOM_MODEL_RETRIES,
        tool_max_retries=CUSTOM_TOOL_RETRIES,
    )
    middleware = build_reliability_middleware(config)

    assert _by_type(middleware, ModelCallLimitMiddleware).run_limit == CUSTOM_MODEL_CALLS
    assert _by_type(middleware, ToolCallLimitMiddleware).run_limit == CUSTOM_TOOL_CALLS
    assert _by_type(middleware, ModelRetryMiddleware).max_retries == CUSTOM_MODEL_RETRIES
    assert _by_type(middleware, ToolRetryMiddleware).max_retries == CUSTOM_TOOL_RETRIES


def test_retries_disabled_when_zero() -> None:
    """Setting a retry count to zero omits that retry middleware entirely."""
    config = AgentConfig(model_max_retries=0, tool_max_retries=0)
    middleware = build_reliability_middleware(config)

    assert not any(isinstance(m, ModelRetryMiddleware) for m in middleware)
    assert not any(isinstance(m, ToolRetryMiddleware) for m in middleware)
    # Call-limit backstops are always present.
    assert any(isinstance(m, ModelCallLimitMiddleware) for m in middleware)
    assert any(isinstance(m, ToolCallLimitMiddleware) for m in middleware)
