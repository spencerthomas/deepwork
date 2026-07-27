"""Workspace long-term memory backends.

Memory is a small, durable key/value document the agent reads as long-term
context and appends learnings to. The backend is injected at the serving seam so
the pure graph never reads credentials:

- :class:`SupabaseWorkspaceMemory` persists to Supabase Postgres over PostgREST
  (HTTP, no database driver), so memory survives task boundaries *and* redeploys.
- :class:`InMemoryWorkspaceMemory` is a process-local stand-in for tests and
  keyless local runs.

Both expose the same tiny contract: ``read()`` and ``save(additions)``.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Protocol, runtime_checkable

__all__ = [
    "InMemoryWorkspaceMemory",
    "SupabaseWorkspaceMemory",
    "WorkspaceMemory",
]

# Bound the stored document so memory cannot grow without limit.
_MAX_MEMORY_CHARS = 20_000


def _merge(existing: str, additions: list[str]) -> str:
    """Append new, non-duplicate notes to the existing memory, bounded."""
    lines = [line.strip() for line in existing.splitlines() if line.strip()]
    seen = set(lines)
    for note in additions:
        entry = note.strip()
        if entry and entry not in seen:
            lines.append(entry)
            seen.add(entry)
    return "\n".join(lines)[-_MAX_MEMORY_CHARS:]


@runtime_checkable
class WorkspaceMemory(Protocol):
    """Durable, workspace-scoped long-term memory the agent reads and appends to."""

    def read(self) -> str:
        """Return the current memory text (empty when unset/unavailable)."""
        ...

    def save(self, additions: list[str]) -> None:
        """Append durable notes; failures must not raise into task execution."""
        ...


class InMemoryWorkspaceMemory:
    """Process-local memory for tests and keyless local runs."""

    def __init__(self, initial: str = "") -> None:
        self._text = initial

    def read(self) -> str:
        return self._text

    def save(self, additions: list[str]) -> None:
        if additions:
            self._text = _merge(self._text, additions)


class SupabaseWorkspaceMemory:
    """Durable workspace memory in Supabase Postgres via PostgREST.

    Reads and upserts a single row keyed by ``key`` in ``table``. Uses the
    service-role key, which is server-held and bypasses row-level security; it
    is read only at the serving seam and never enters agent-visible content.
    All calls fail open (return empty / no-op) so a memory outage never fails a
    task.
    """

    def __init__(
        self,
        base_url: str,
        service_key: str,
        *,
        table: str = "workspace_memory",
        key: str = "default",
        timeout: float = 15.0,
    ) -> None:
        self._rest = f"{base_url.rstrip('/')}/rest/v1/{table}"
        self._key = key
        self._service_key = service_key
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "apikey": self._service_key,
            "Authorization": f"Bearer {self._service_key}",
            "Content-Type": "application/json",
            "User-Agent": "deep-work-agent",
        }

    def read(self) -> str:
        query = urllib.parse.urlencode({"key": f"eq.{self._key}", "select": "content"})
        request = urllib.request.Request(f"{self._rest}?{query}")  # noqa: S310 - fixed https host
        for header, value in self._headers().items():
            request.add_header(header, value)
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:  # noqa: S310
                rows = json.loads(response.read().decode("utf-8") or "[]")
        except (urllib.error.URLError, TimeoutError, ValueError):
            return ""
        if not isinstance(rows, list) or not rows:
            return ""
        content = rows[0].get("content", "") if isinstance(rows[0], dict) else ""
        return content if isinstance(content, str) else ""

    def save(self, additions: list[str]) -> None:
        if not additions:
            return
        combined = _merge(self.read(), additions)
        body = json.dumps([{"key": self._key, "content": combined}]).encode("utf-8")
        request = urllib.request.Request(self._rest, data=body, method="POST")  # noqa: S310
        for header, value in self._headers().items():
            request.add_header(header, value)
        # Upsert on the primary key, and don't ask PostgREST to echo the row back.
        request.add_header("Prefer", "resolution=merge-duplicates,return=minimal")
        try:
            urllib.request.urlopen(request, timeout=self._timeout).close()  # noqa: S310
        except (urllib.error.URLError, TimeoutError):
            return
