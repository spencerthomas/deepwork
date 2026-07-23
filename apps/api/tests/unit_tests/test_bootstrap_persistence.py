"""Composition and lifecycle tests for optional local SQLite task persistence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import pytest

from deepwork_api import create_app
from deepwork_api.adapters.fixture import InMemoryTaskRepository
from deepwork_api.adapters.persistence import (
    SQLiteTaskRepository,
    SQLiteTaskRepositoryClosedError,
    SQLiteTaskRepositoryError,
)


async def test_default_apps_use_independent_memory_and_fixture_status() -> None:
    first = create_app()
    second = create_app()

    assert isinstance(first.state.task_repository, InMemoryTaskRepository)
    assert isinstance(second.state.task_repository, InMemoryTaskRepository)
    assert first.state.task_repository is not second.state.task_repository

    async with first.router.lifespan_context(first):
        created = await first.state.task_repository.create_task(
            title="Only in the first app",
            objective="Only in the first app",
        )
        assert created.task_id == "task_00000001"
        assert await second.state.task_repository.list_tasks() == ()

        status = await first.state.task_service.repository.get_task(created.task_id)
        assert status.task_id == created.task_id
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=first),
            base_url="http://fixture.test",
        ) as client:
            demo = (await client.get("/api/v1/demo/status")).json()
        assert demo["mode"] == "fixture"
        assert demo["evidence_class"] == "fixture"
        capabilities = {item["name"]: item["state"] for item in demo["capabilities"]}
        assert capabilities["external_providers"] == "unavailable"

    provider_status = await second.state.task_service.repository.list_tasks()
    assert provider_status == ()


async def test_sqlite_initializes_on_startup_and_closes_after_runner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = (tmp_path / "tasks.sqlite").resolve()
    app = create_app(task_database_path=database)
    repository = app.state.task_repository
    runner = app.state.task_runner
    order: list[str] = []
    original_runner_close = type(runner).close
    original_repository_close = type(repository).close

    async def runner_close(self: Any) -> None:
        order.append("runner")
        await original_runner_close(self)

    async def repository_close(self: Any) -> None:
        order.append("repository")
        await original_repository_close(self)

    monkeypatch.setattr(type(runner), "close", runner_close)
    monkeypatch.setattr(type(repository), "close", repository_close)

    assert isinstance(repository, SQLiteTaskRepository)
    assert not database.exists()
    async with app.router.lifespan_context(app):
        assert database.is_file()
        assert await repository.list_tasks() == ()

    assert order == ["runner", "repository"]
    with pytest.raises(SQLiteTaskRepositoryClosedError, match="closed"):
        await repository.list_tasks()


async def test_sqlite_closes_when_runner_close_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = create_app(task_database_path=(tmp_path / "tasks.sqlite").resolve())
    repository = app.state.task_repository
    runner = app.state.task_runner

    async def failing_close(_self: Any) -> None:
        raise RuntimeError("runner close failed")

    monkeypatch.setattr(type(runner), "close", failing_close)

    with pytest.raises(RuntimeError, match="runner close failed"):
        async with app.router.lifespan_context(app):
            assert await repository.list_tasks() == ()

    with pytest.raises(SQLiteTaskRepositoryClosedError, match="closed"):
        await repository.list_tasks()


async def test_explicit_sqlite_startup_failure_does_not_fall_back(tmp_path: Path) -> None:
    database = (tmp_path / "not-a-database.sqlite").resolve()
    database.write_bytes(b"not sqlite")
    app = create_app(task_database_path=database)

    with pytest.raises(SQLiteTaskRepositoryError, match=r"database|encrypted"):
        async with app.router.lifespan_context(app):
            raise AssertionError("startup must not serve")

    assert isinstance(app.state.task_repository, SQLiteTaskRepository)
