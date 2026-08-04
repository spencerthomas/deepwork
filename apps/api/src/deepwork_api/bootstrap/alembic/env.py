"""Alembic environment for the packaged Deep Work PostgreSQL schema."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Sequence

from alembic import context
from sqlalchemy.engine import Connection, make_url
from sqlalchemy.ext.asyncio import create_async_engine

from deepwork_api.adapters.persistence.postgres_schema import metadata


def _database_url() -> str:
    value = os.environ.get("DEEPWORK_DATABASE_URL")
    if not value:
        raise RuntimeError("DEEPWORK_DATABASE_URL is required for migrations")
    parsed = make_url(value)
    if parsed.drivername != "postgresql+psycopg":
        raise RuntimeError("migrations require the postgresql+psycopg driver")
    return parsed.render_as_string(hide_password=False)


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(_database_url(), hide_parameters=True)
    try:
        async with engine.connect() as connection:
            await connection.run_sync(_run_migrations)
    finally:
        await engine.dispose()


def main(argv: Sequence[str] | None = None) -> None:
    del argv
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        asyncio.run(run_migrations_online())


main()
