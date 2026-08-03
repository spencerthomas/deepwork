"""Tests for the bounded local-runtime configuration."""

import pytest

from deepwork_agent import AgentConfig
from deepwork_agent.config import ServingConfig

DEFAULT_MAX_PLAN_STEPS = 6
MAX_VERIFICATION_ITERATIONS = 3


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


def test_serving_config_reads_the_complete_environment_contract() -> None:
    """Serving settings are parsed once at the package configuration boundary."""
    config = ServingConfig.from_environment(
        {
            "DEEPWORK_AGENT_FAKE": "1",
            "DEEPWORK_AGENT_MODEL": "openrouter:openai/gpt-4o-mini",
            "OPENROUTER_API_KEY": "router-secret",
            "DEEPWORK_AGENT_SYSTEM_PROMPT": "Custom prompt",
            "DEEPWORK_SANDBOX": "langsmith",
            "LANGSMITH_API_KEY": "langsmith-secret",
            "DEEPWORK_VERIFY": "1",
            "DEEPWORK_VERIFY_ITERS": "9",
            "DEEPWORK_SUPABASE_URL": "https://example.supabase.co",
            "DEEPWORK_SUPABASE_SERVICE_KEY": "supabase-secret",
            "DEEPWORK_MEMORY_TABLE": "custom_memory",
            "DEEPWORK_MEMORY": "1",
        }
    )

    assert config.use_fake_model is True
    assert config.model_identifier == "openrouter:openai/gpt-4o-mini"
    assert config.openrouter_api_key == "router-secret"
    assert config.system_prompt == "Custom prompt"
    assert config.sandbox_backend == "langsmith"
    assert config.langsmith_api_key == "langsmith-secret"
    assert config.verification_enabled is True
    assert config.verification_iterations == MAX_VERIFICATION_ITERATIONS
    assert config.supabase_url == "https://example.supabase.co"
    assert config.supabase_service_key == "supabase-secret"
    assert config.memory_table == "custom_memory"
    assert config.memory_enabled is True


def test_serving_config_defaults_preserve_disabled_optional_capabilities() -> None:
    """An empty environment keeps fake mode, memory, sandbox, and verification off."""
    config = ServingConfig.from_environment({})

    assert config.use_fake_model is False
    assert config.model_identifier is None
    assert config.system_prompt is None
    assert config.sandbox_backend is None
    assert config.verification_enabled is False
    assert config.verification_iterations == 1
    assert config.memory_enabled is False
    assert config.memory_table == "workspace_memory"


def test_serving_config_repr_does_not_expose_credentials() -> None:
    """Typed configuration must not make server credentials printable."""
    config = ServingConfig.from_environment(
        {
            "OPENROUTER_API_KEY": "router-secret",
            "LANGSMITH_API_KEY": "langsmith-secret",
            "DEEPWORK_SUPABASE_SERVICE_KEY": "supabase-secret",
        }
    )

    rendered = repr(config)
    assert "router-secret" not in rendered
    assert "langsmith-secret" not in rendered
    assert "supabase-secret" not in rendered
