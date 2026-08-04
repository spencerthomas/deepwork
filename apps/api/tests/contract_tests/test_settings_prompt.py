"""Contract tests for the editable workspace system-prompt setting."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
import pytest

from deepwork_api import create_app
from deepwork_api.adapters.prompt import InMemoryPromptStore, SQLitePromptStore
from deepwork_api.domain import (
    MAX_SYSTEM_PROMPT_LENGTH,
    SecurityContext,
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


@asynccontextmanager
async def _scoped_clients(
    *,
    settings_database_path: Path,
    contexts: Mapping[str, SecurityContext],
) -> AsyncIterator[tuple[httpx.AsyncClient, httpx.AsyncClient]]:
    app = create_app(
        settings_database_path=settings_database_path,
        access_key_contexts=contexts,
    )
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with (
            httpx.AsyncClient(transport=transport, base_url="https://settings.test") as client_a,
            httpx.AsyncClient(transport=transport, base_url="https://settings.test") as client_b,
        ):
            assert (
                await client_a.post("/api/v1/auth/login", json={"accessKey": "access-key-a"})
            ).status_code == 200
            assert (
                await client_b.post("/api/v1/auth/login", json={"accessKey": "access-key-b"})
            ).status_code == 200
            yield client_a, client_b


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


async def test_prompt_settings_are_tenant_and_workspace_scoped_across_restart(
    tmp_path: Path,
) -> None:
    """Same-named workspaces in separate tenants never share prompt settings."""

    settings_db = tmp_path / "tenant-settings.sqlite3"
    contexts = {
        "access-key-a": SecurityContext("tenant-secret-a", "workspace-shared", "actor-a"),
        "access-key-b": SecurityContext("tenant-secret-b", "workspace-shared", "actor-b"),
    }

    async with _scoped_clients(
        settings_database_path=settings_db,
        contexts=contexts,
    ) as (client_a, client_b):
        set_a = await client_a.put(
            "/api/v1/settings/prompt", json={"systemPrompt": "Use the first persona."}
        )
        assert set_a.json() == {"systemPrompt": "Use the first persona.", "isDefault": False}
        assert (await client_b.get("/api/v1/settings/prompt")).json() == {
            "systemPrompt": None,
            "isDefault": True,
        }

        set_b = await client_b.put(
            "/api/v1/settings/prompt", json={"systemPrompt": "Use the second persona."}
        )
        assert set_b.json() == {"systemPrompt": "Use the second persona.", "isDefault": False}
        assert (await client_a.get("/api/v1/settings/prompt")).json()["systemPrompt"] == (
            "Use the first persona."
        )

        cleared_a = await client_a.put("/api/v1/settings/prompt", json={"systemPrompt": None})
        assert cleared_a.json() == {"systemPrompt": None, "isDefault": True}
        assert (await client_b.get("/api/v1/settings/prompt")).json()["systemPrompt"] == (
            "Use the second persona."
        )

        spoofed = await client_a.put(
            "/api/v1/settings/prompt",
            json={
                "systemPrompt": "Do not store this.",
                "tenantId": "tenant-secret-b",
                "workspaceId": "workspace-shared",
            },
        )
        assert spoofed.status_code == 422
        assert (await client_a.get("/api/v1/settings/prompt")).json()["systemPrompt"] is None

        serialized = " ".join((set_a.text, set_b.text, cleared_a.text))
        assert "tenant-secret-a" not in serialized
        assert "tenant-secret-b" not in serialized

    async with _scoped_clients(
        settings_database_path=settings_db,
        contexts=contexts,
    ) as (client_a, client_b):
        assert (await client_a.get("/api/v1/settings/prompt")).json() == {
            "systemPrompt": None,
            "isDefault": True,
        }
        assert (await client_b.get("/api/v1/settings/prompt")).json() == {
            "systemPrompt": "Use the second persona.",
            "isDefault": False,
        }


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


async def test_memory_prompt_initial_value_and_identifiers_are_safely_scoped() -> None:
    store = InMemoryPromptStore("Default-context persona.")
    assert await store.get_system_prompt() == "Default-context persona."
    assert (
        await store.get_system_prompt(tenant_id="tenant-a", workspace_id="workspace-local") is None
    )
    with pytest.raises(ValueError, match="tenant_id"):
        await store.get_system_prompt(tenant_id="../tenant", workspace_id="workspace-local")
    with pytest.raises(ValueError, match="workspace_id"):
        await store.set_system_prompt(
            "Unsafe scope.", tenant_id="tenant-a", workspace_id="workspace/escape"
        )


async def test_sqlite_prompt_keys_keep_ambiguous_scope_pairs_distinct(tmp_path: Path) -> None:
    store = SQLitePromptStore(tmp_path / "collision-safe.sqlite3")
    await store.set_system_prompt("First.", tenant_id="tenant-a", workspace_id="workspace-ab")
    await store.set_system_prompt("Second.", tenant_id="tenant-aa", workspace_id="workspace-b")

    assert (
        await store.get_system_prompt(tenant_id="tenant-a", workspace_id="workspace-ab") == "First."
    )
    assert (
        await store.get_system_prompt(tenant_id="tenant-aa", workspace_id="workspace-b")
        == "Second."
    )
    with pytest.raises(ValueError, match="tenant_id"):
        await store.get_system_prompt(tenant_id="", workspace_id="workspace-b")
    await store.close()


async def test_sqlite_prompt_store_preserves_legacy_default_without_scoped_fallback(
    tmp_path: Path,
) -> None:
    import sqlite3

    database = tmp_path / "legacy-settings.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        connection.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?)",
            ("system_prompt", "Legacy default persona."),
        )

    store = SQLitePromptStore(database)
    assert await store.get_system_prompt() == "Legacy default persona."
    assert (
        await store.get_system_prompt(tenant_id="tenant-a", workspace_id="workspace-local") is None
    )

    await store.set_system_prompt(
        "Scoped persona.", tenant_id="tenant-a", workspace_id="workspace-local"
    )
    assert (
        await store.get_system_prompt(tenant_id="tenant-a", workspace_id="workspace-local")
        == "Scoped persona."
    )
    await store.set_system_prompt(None, tenant_id="tenant-a", workspace_id="workspace-local")
    assert (
        await store.get_system_prompt(tenant_id="tenant-a", workspace_id="workspace-local") is None
    )
    assert await store.get_system_prompt() == "Legacy default persona."

    await store.set_system_prompt(None)
    assert await store.get_system_prompt() is None
    await store.close()
