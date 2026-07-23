"""Composition tests for the explicit-only loopback Agent Server mode."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from deepwork_api import create_app
from deepwork_api.adapters.fixture import InMemoryTaskRepository
from deepwork_api.adapters.sources.local import (
    LocalAgentServerSource,
    LocalSourceConfigurationError,
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


def test_local_mode_requires_complete_explicit_configuration(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="assistant identifier"):
        create_app(local_agent_server_endpoint=_LOCAL_ENDPOINT)
    with pytest.raises(ValueError, match="explicit loopback endpoint"):
        create_app(local_agent_server_assistant=_LOCAL_ASSISTANT)
    with pytest.raises(ValueError, match="persistent task recovery"):
        create_app(
            task_database_path=(tmp_path / "tasks.sqlite").resolve(),
            local_agent_server_endpoint=_LOCAL_ENDPOINT,
            local_agent_server_assistant=_LOCAL_ASSISTANT,
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
        )


def test_local_mode_rejects_invalid_assistant_identity() -> None:
    with pytest.raises(LocalSourceConfigurationError):
        create_app(
            local_agent_server_endpoint=_LOCAL_ENDPOINT,
            local_agent_server_assistant="not a valid identifier!",
        )


async def test_local_mode_wires_official_sdk_runner_and_closes_cleanly() -> None:
    app = create_app(
        local_agent_server_endpoint=_LOCAL_ENDPOINT,
        local_agent_server_assistant=_LOCAL_ASSISTANT,
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
