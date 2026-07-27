"""Credential-free tests for workspace memory backends."""

from __future__ import annotations

from deepwork_agent.memory import (
    InMemoryWorkspaceMemory,
    SupabaseWorkspaceMemory,
    WorkspaceMemory,
)
from deepwork_agent.memory import _MAX_MEMORY_CHARS, _merge


def test_in_memory_backend_appends_and_dedupes() -> None:
    memory = InMemoryWorkspaceMemory("first note")
    memory.save(["second note", "first note"])  # duplicate ignored
    memory.save([])  # no-op
    assert memory.read() == "first note\nsecond note"


def test_in_memory_backend_satisfies_the_protocol() -> None:
    assert isinstance(InMemoryWorkspaceMemory(), WorkspaceMemory)
    assert isinstance(SupabaseWorkspaceMemory("https://x.supabase.co", "key"), WorkspaceMemory)


def test_merge_is_bounded() -> None:
    huge = ["x" * (_MAX_MEMORY_CHARS + 1000)]
    assert len(_merge("", huge)) == _MAX_MEMORY_CHARS


def test_supabase_backend_builds_the_rest_url() -> None:
    backend = SupabaseWorkspaceMemory("https://abc.supabase.co/", "svc-key", table="workspace_memory")
    assert backend._rest == "https://abc.supabase.co/rest/v1/workspace_memory"
    headers = backend._headers()
    assert headers["apikey"] == "svc-key"
    assert headers["Authorization"] == "Bearer svc-key"
