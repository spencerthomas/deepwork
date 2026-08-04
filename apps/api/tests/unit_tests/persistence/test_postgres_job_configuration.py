"""Bounded PostgreSQL client configuration tests."""

import pytest

from deepwork_api.adapters.persistence import postgres_jobs


def test_postgres_job_repository_bounds_pool_connection_statement_and_lock_waits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    engine = object()

    def fake_create_async_engine(url: object, **options: object) -> object:
        captured["url"] = url
        captured.update(options)
        return engine

    monkeypatch.setattr(postgres_jobs, "create_async_engine", fake_create_async_engine)

    repository = postgres_jobs.PostgresJobRepository(
        "postgresql+psycopg://deepwork@127.0.0.1/deepwork_test"
    )

    assert repository._engine is engine
    assert captured["pool_timeout"] == 5
    connect_args = captured["connect_args"]
    assert isinstance(connect_args, dict)
    assert connect_args["connect_timeout"] == 5
    assert connect_args["options"] == (
        "-c statement_timeout=10000 -c lock_timeout=5000 "
        "-c idle_in_transaction_session_timeout=10000"
    )
