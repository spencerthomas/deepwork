"""Tests for the bounded local-runtime configuration."""

import pytest

from deepwork_agent import AgentConfig

DEFAULT_MAX_PLAN_STEPS = 6


def test_default_config_requires_plan_approval() -> None:
    """The local runtime defaults to a bounded plan and approval gate."""
    config = AgentConfig()

    assert config.schema_version == 1
    assert config.runtime_mode == "local-runtime"
    assert config.require_plan_approval is True
    assert config.require_tool_approval is True
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
