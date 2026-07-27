"""Durable system-prompt store backed by a small dedicated SQLite file.

This intentionally does not share the versioned task database. The editable
prompt is a single workspace setting with a trivial, stable shape, so it lives
in its own file behind the same ``PromptStore`` port. Writes are serialized and
run off the event loop; reads are cheap.
"""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

from deepwork_api.domain import normalize_system_prompt

_SETTINGS_KEY = "system_prompt"
_SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
)
"""


class SQLitePromptStore:
    """Single-row settings storage for the workspace system prompt."""

    def __init__(self, database_path: str | Path) -> None:
        self._path = Path(database_path)
        self._lock = asyncio.Lock()
        self._initialized = False

    async def _ensure(self) -> None:
        if self._initialized:
            return
        async with self._lock:
            # Re-check under the lock so concurrent first-callers initialize once.
            # (The schema step is idempotent regardless.)
            if not self._initialized:
                await asyncio.to_thread(self._initialize_sync)
                self._initialized = True

    def _initialize_sync(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._path) as connection:
            connection.execute(_SCHEMA)
            connection.commit()

    async def get_system_prompt(self) -> str | None:
        await self._ensure()
        return await asyncio.to_thread(self._get_sync)

    def _get_sync(self) -> str | None:
        with sqlite3.connect(self._path) as connection:
            row = connection.execute(
                "SELECT value FROM settings WHERE key = ?", (_SETTINGS_KEY,)
            ).fetchone()
        if row is None:
            return None
        return normalize_system_prompt(row[0])

    async def set_system_prompt(self, prompt: str | None) -> None:
        normalized = normalize_system_prompt(prompt)
        await self._ensure()
        async with self._lock:
            await asyncio.to_thread(self._set_sync, normalized)

    def _set_sync(self, normalized: str | None) -> None:
        with sqlite3.connect(self._path) as connection:
            if normalized is None:
                connection.execute("DELETE FROM settings WHERE key = ?", (_SETTINGS_KEY,))
            else:
                connection.execute(
                    "INSERT INTO settings (key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (_SETTINGS_KEY, normalized),
                )
            connection.commit()

    async def close(self) -> None:
        return None
