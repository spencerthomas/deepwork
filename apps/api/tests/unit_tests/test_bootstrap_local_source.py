"""Composition tests for the gated, development-only loopback Agent Server mode."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import deepwork_api.bootstrap.api as bootstrap_api
from deepwork_api import create_app
from deepwork_api.adapters.fixture import InMemoryTaskRepository
from deepwork_api.adapters.sources.local import (
    LocalAgentServerSource,
    LocalSourceConfigurationError,
    LocalSourceGatedError,
)
from deepwork_api.application import DeterministicFixtureRunner, LocalAgentServerRunner

_LOCAL_ENDPOINT = "http://127.0.0.1:2024"
_LOCAL_ASSISTANT = "deep-work-local-agent"


def test_default_create_app_stays_in_deterministic_fixture_mode() -> None:
    app = create_app()

    assert isinstance(app.state.task_runner, DeterministicFixtureRunner)
    assert isinstance(app.state.task_repository, InMemoryTaskRepository)
    description = app.description.casefold()
    assert "no live provider contract" in description
    assert "classic" not in description


def test_loopback_config_is_gated_off_without_the_explicit_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A supplied loopback endpoint alone must not build a provider-calling source."""

    built: list[tuple[str, str]] = []

    def _tracking_builder(*, endpoint: str, assistant_id: str) -> LocalAgentServerSource:
        built.append((endpoint, assistant_id))
        raise AssertionError("the gated source builder must not run without opt-in")

    monkeypatch.setattr(bootstrap_api, "_build_local_agent_server_source", _tracking_builder)

    with pytest.raises(LocalSourceGatedError, match="SPIKE-SOURCE-001"):
        create_app(
            local_agent_server_endpoint=_LOCAL_ENDPOINT,
            local_agent_server_assistant=_LOCAL_ASSISTANT,
        )
    assert built == []


def test_opt_in_without_a_loopback_endpoint_is_rejected() -> None:
    with pytest.raises(ValueError, match="requires an explicit loopback endpoint"):
        create_app(allow_ungated_local_agent_source=True)


def test_local_mode_requires_complete_explicit_configuration(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="assistant identifier"):
        create_app(
            local_agent_server_endpoint=_LOCAL_ENDPOINT,
            allow_ungated_local_agent_source=True,
        )
    with pytest.raises(ValueError, match="explicit loopback endpoint"):
        create_app(local_agent_server_assistant=_LOCAL_ASSISTANT)
    with pytest.raises(ValueError, match="persistent task recovery"):
        create_app(
            task_database_path=(tmp_path / "tasks.sqlite").resolve(),
            local_agent_server_endpoint=_LOCAL_ENDPOINT,
            local_agent_server_assistant=_LOCAL_ASSISTANT,
            allow_ungated_local_agent_source=True,
        )


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://example.com",
        "https://127.0.0.1:2024",
        "http://10.0.0.1:2024",
        "http://169.254.169.254:80",
        "http://localhost:2024",
        "http://127.0.0.1",
        "http://127.0.0.1:2024/api",
        "http://user:secret@127.0.0.1:2024",
        "not a url",
    ],
)
def test_local_mode_rejects_every_non_loopback_or_ambiguous_url(endpoint: str) -> None:
    with pytest.raises(LocalSourceConfigurationError):
        create_app(
            local_agent_server_endpoint=endpoint,
            local_agent_server_assistant=_LOCAL_ASSISTANT,
            allow_ungated_local_agent_source=True,
        )


def test_local_mode_rejects_invalid_assistant_identity() -> None:
    with pytest.raises(LocalSourceConfigurationError):
        create_app(
            local_agent_server_endpoint=_LOCAL_ENDPOINT,
            local_agent_server_assistant="not a valid identifier!",
            allow_ungated_local_agent_source=True,
        )


async def test_opted_in_local_mode_wires_official_sdk_runner_and_closes_cleanly() -> None:
    app = create_app(
        local_agent_server_endpoint=_LOCAL_ENDPOINT,
        local_agent_server_assistant=_LOCAL_ASSISTANT,
        allow_ungated_local_agent_source=True,
    )

    runner = app.state.task_runner
    assert isinstance(runner, LocalAgentServerRunner)
    source: Any = runner.source
    assert isinstance(source, LocalAgentServerSource)
    assert source.endpoint == _LOCAL_ENDPOINT
    assert source.assistant_id == _LOCAL_ASSISTANT
    assert isinstance(app.state.task_repository, InMemoryTaskRepository)

    async with app.router.lifespan_context(app):
        pass


def test_cli_gates_loopback_execution_behind_an_explicit_flag() -> None:
    parser = bootstrap_api._parser()

    default_args = parser.parse_args([])
    assert default_args.allow_ungated_local_agent_source is False

    opted_in = parser.parse_args(
        [
            "--local-agent-server-endpoint",
            _LOCAL_ENDPOINT,
            "--local-agent-server-assistant",
            _LOCAL_ASSISTANT,
            "--allow-ungated-local-agent-source",
        ]
    )
    assert opted_in.allow_ungated_local_agent_source is True

    # Supplying the loopback flags without the opt-in flag stays gated off.
    gated = parser.parse_args(
        [
            "--local-agent-server-endpoint",
            _LOCAL_ENDPOINT,
            "--local-agent-server-assistant",
            _LOCAL_ASSISTANT,
        ]
    )
    assert gated.allow_ungated_local_agent_source is False
    with pytest.raises(LocalSourceGatedError):
        create_app(
            local_agent_server_endpoint=gated.local_agent_server_endpoint,
            local_agent_server_assistant=gated.local_agent_server_assistant,
            allow_ungated_local_agent_source=gated.allow_ungated_local_agent_source,
        )
