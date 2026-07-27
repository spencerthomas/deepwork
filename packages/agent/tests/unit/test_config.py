"""Tests for the bounded local-runtime configuration."""

import pytest

from deepwork_agent import AgentConfig

DEFAULT_MAX_PLAN_STEPS = 6
DEFAULT_MAX_MODEL_CALLS = 25
DEFAULT_MAX_TOOL_CALLS = 50
DEFAULT_MAX_RETRIES = 2
DEFAULT_RECURSION_LIMIT = 50


def test_default_config_requires_plan_approval() -> None:
    """The local runtime defaults to a bounded plan and approval gate."""
    config = AgentConfig()

    assert config.schema_version == 1
    assert config.runtime_mode == "local-runtime"
    assert config.require_plan_approval is True
    assert config.max_plan_steps == DEFAULT_MAX_PLAN_STEPS


def test_unknown_schema_is_rejected() -> None:
    """Runtime validation rejects an unsupported schema."""
    with pytest.raises(ValueError, match="unsupported agent configuration schema"):
        AgentConfig(schema_version=2)  # type: ignore[arg-type]


def test_non_local_runtime_mode_is_rejected() -> None:
    """Hosted and provider runtime selection stay outside this package."""
    with pytest.raises(ValueError, match="only the injected-model local-runtime"):
        AgentConfig(runtime_mode="hosted")  # type: ignore[arg-type]


@pytest.mark.parametrize("limit", [0, 13])
def test_plan_step_limit_is_bounded(limit: int) -> None:
    """Plan parsing cannot be configured to an unbounded size."""
    with pytest.raises(ValueError, match="between 1 and 12"):
        AgentConfig(max_plan_steps=limit)


def test_reliability_envelope_has_bounded_defaults() -> None:
    """The default config caps model/tool calls, retries, and recursion depth."""
    config = AgentConfig()

    assert config.max_model_calls == DEFAULT_MAX_MODEL_CALLS
    assert config.max_tool_calls == DEFAULT_MAX_TOOL_CALLS
    assert config.model_max_retries == DEFAULT_MAX_RETRIES
    assert config.tool_max_retries == DEFAULT_MAX_RETRIES
    assert config.recursion_limit == DEFAULT_RECURSION_LIMIT


@pytest.mark.parametrize("value", [0, 201])
def test_model_call_limit_is_bounded(value: int) -> None:
    """A run cannot be configured to spend unbounded model calls."""
    with pytest.raises(ValueError, match="max_model_calls must be between 1 and 200"):
        AgentConfig(max_model_calls=value)


@pytest.mark.parametrize("value", [0, 501])
def test_tool_call_limit_is_bounded(value: int) -> None:
    """A run cannot be configured to spend unbounded tool calls."""
    with pytest.raises(ValueError, match="max_tool_calls must be between 1 and 500"):
        AgentConfig(max_tool_calls=value)


@pytest.mark.parametrize("value", [3, 501])
def test_recursion_limit_is_bounded(value: int) -> None:
    """The executor recursion backstop stays within a sane range."""
    with pytest.raises(ValueError, match="recursion_limit must be between 4 and 500"):
        AgentConfig(recursion_limit=value)


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("model_max_retries", "model_max_retries must be between 0 and 8"),
        ("tool_max_retries", "tool_max_retries must be between 0 and 8"),
    ],
)
def test_retry_counts_are_bounded(field: str, message: str) -> None:
    """Retry counts are non-negative and capped."""
    with pytest.raises(ValueError, match=message):
        AgentConfig(**{field: 9})
