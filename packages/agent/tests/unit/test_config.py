"""Tests for the package-scaffold configuration boundary."""

import pytest

from deepwork_agent import AgentPackageConfig


def test_default_config_is_explicitly_disabled() -> None:
    """The only supported scaffold config keeps runtime unavailable."""
    config = AgentPackageConfig()

    assert config.schema_version == 1
    assert config.runtime_enabled is False


def test_unknown_schema_is_rejected() -> None:
    """Runtime validation rejects an unsupported scaffold schema."""
    with pytest.raises(ValueError, match="unsupported agent package scaffold schema"):
        AgentPackageConfig(schema_version=2)  # type: ignore[arg-type]


def test_runtime_cannot_be_enabled() -> None:
    """A runtime value cannot bypass the open configuration gate."""
    with pytest.raises(ValueError, match="cannot be enabled"):
        AgentPackageConfig(runtime_enabled=True)  # type: ignore[arg-type]
