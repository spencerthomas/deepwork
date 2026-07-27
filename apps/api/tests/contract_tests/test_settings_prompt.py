"""Contract tests for the editable workspace system-prompt setting."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
import pytest

from deepwork_api import create_app
from deepwork_api.adapters.prompt import SQLitePromptStore
from deepwork_api.domain import (
    MAX_SYSTEM_PROMPT_LENGTH,
    SystemPromptTooLongError,
    normalize_system_prompt,
)


@asynccontextmanager
async def _app(**kwargs: Any) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(**kwargs)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="https://settings.test"
        ) as client:
            yield client


async def test_prompt_defaults_to_unset_and_reports_default() -> None:
    async with _app() as client:
        response = await client.get("/api/v1/settings/prompt")
        assert response.status_code == 200
        assert response.json() == {"systemPrompt": None, "isDefault": True}


async def test_prompt_can_be_set_read_back_and_cleared() -> None:
    async with _app() as client:
        put = await client.put(
            "/api/v1/settings/prompt", json={"systemPrompt": "  Always be terse.  "}
        )
        assert put.status_code == 200
        assert put.json() == {"systemPrompt": "Always be terse.", "isDefault": False}

        got = await client.get("/api/v1/settings/prompt")
        assert got.json() == {"systemPrompt": "Always be terse.", "isDefault": False}

        cleared = await client.put("/api/v1/settings/prompt", json={"systemPrompt": "   "})
        assert cleared.json() == {"systemPrompt": None, "isDefault": True}


async def test_over_length_prompt_is_rejected_by_the_wire_contract() -> None:
    async with _app() as client:
        response = await client.put(
            "/api/v1/settings/prompt",
            json={"systemPrompt": "x" * (MAX_SYSTEM_PROMPT_LENGTH + 1)},
        )
        # The pydantic max_length bound rejects before the handler runs.
        assert response.status_code == 422


async def test_durable_prompt_survives_a_fresh_app_on_the_same_database(tmp_path: Path) -> None:
    settings_db = tmp_path / "settings.sqlite3"
    async with _app(settings_database_path=settings_db) as client:
        await client.put("/api/v1/settings/prompt", json={"systemPrompt": "Persist me."})

    # A brand-new app pointed at the same settings database must see the value.
    async with _app(settings_database_path=settings_db) as client:
        got = await client.get("/api/v1/settings/prompt")
        assert got.json() == {"systemPrompt": "Persist me.", "isDefault": False}


async def test_settings_prompt_is_session_guarded_when_access_key_is_set() -> None:
    async with _app(access_key="secret-key") as client:
        unauthenticated = await client.get("/api/v1/settings/prompt")
        assert unauthenticated.status_code == 401


def test_normalize_system_prompt_rules() -> None:
    assert normalize_system_prompt(None) is None
    assert normalize_system_prompt("   ") is None
    assert normalize_system_prompt("  hi  ") == "hi"
    with pytest.raises(SystemPromptTooLongError):
        normalize_system_prompt("x" * (MAX_SYSTEM_PROMPT_LENGTH + 1))


async def test_sqlite_prompt_store_round_trips_and_clears(tmp_path: Path) -> None:
    store = SQLitePromptStore(tmp_path / "s.sqlite3")
    assert await store.get_system_prompt() is None
    await store.set_system_prompt("workspace persona")
    assert await store.get_system_prompt() == "workspace persona"
    await store.set_system_prompt(None)
    assert await store.get_system_prompt() is None
    await store.close()
