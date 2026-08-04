"""Durable system-prompt store backed by a small dedicated SQLite file.

This intentionally does not share the versioned task database. The editable
prompt is a single workspace setting with a trivial, stable shape, so it lives
in its own file behind the same ``PromptStore`` port. Writes are serialized and
run off the event loop; reads are cheap.
"""

from __future__ import annotations

import asyncio
import base64
import sqlite3
from pathlib import Path

from deepwork_api.domain import (
    DEFAULT_TENANT_ID,
    DEFAULT_WORKSPACE_ID,
    SecurityContext,
    normalize_system_prompt,
)

_SETTINGS_KEY = "system_prompt"
_SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
)
"""


class SQLitePromptStore:
    """Tenant/workspace settings storage without expanding the legacy schema."""

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

    @staticmethod
    def _settings_key(tenant_id: str, workspace_id: str) -> str:
        context = SecurityContext(tenant_id=tenant_id, workspace_id=workspace_id)
        if context.tenant_id == DEFAULT_TENANT_ID and context.workspace_id == DEFAULT_WORKSPACE_ID:
            # Preserve the exact legacy row for the open local/default context.
            return _SETTINGS_KEY

        # URL-safe base64 is an injective encoding. Delimiting the independently
        # encoded values keeps similarly prefixed tenant/workspace pairs distinct.
        encoded_tenant = base64.urlsafe_b64encode(context.tenant_id.encode()).decode().rstrip("=")
        encoded_workspace = (
            base64.urlsafe_b64encode(context.workspace_id.encode()).decode().rstrip("=")
        )
        return f"{_SETTINGS_KEY}:v1:{encoded_tenant}:{encoded_workspace}"

    async def get_system_prompt(
        self,
        *,
        tenant_id: str = DEFAULT_TENANT_ID,
        workspace_id: str = DEFAULT_WORKSPACE_ID,
    ) -> str | None:
        key = self._settings_key(tenant_id, workspace_id)
        await self._ensure()
        return await asyncio.to_thread(self._get_sync, key)

    def _get_sync(self, key: str) -> str | None:
        with sqlite3.connect(self._path) as connection:
            row = connection.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        if row is None:
            return None
        return normalize_system_prompt(row[0])

    async def set_system_prompt(
        self,
        prompt: str | None,
        *,
        tenant_id: str = DEFAULT_TENANT_ID,
        workspace_id: str = DEFAULT_WORKSPACE_ID,
    ) -> None:
        key = self._settings_key(tenant_id, workspace_id)
        normalized = normalize_system_prompt(prompt)
        await self._ensure()
        async with self._lock:
            await asyncio.to_thread(self._set_sync, key, normalized)

    def _set_sync(self, key: str, normalized: str | None) -> None:
        with sqlite3.connect(self._path) as connection:
            if normalized is None:
                connection.execute("DELETE FROM settings WHERE key = ?", (key,))
            else:
                connection.execute(
                    "INSERT INTO settings (key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (key, normalized),
                )
            connection.commit()

    async def close(self) -> None:
        return None
