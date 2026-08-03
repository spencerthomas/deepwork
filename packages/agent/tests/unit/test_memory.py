"""Credential-free tests for workspace memory backends."""

from __future__ import annotations

from deepwork_agent.memory import (
    _MAX_MEMORY_CHARS,
    InMemoryWorkspaceMemory,
    SupabaseWorkspaceMemory,
    WorkspaceMemory,
    _merge,
)


def test_in_memory_backend_appends_and_dedupes() -> None:
    """Process-local memory appends new notes and ignores duplicates."""
    memory = InMemoryWorkspaceMemory("first note")
    memory.save(["second note", "first note"])  # duplicate ignored
    memory.save([])  # no-op
    assert memory.read() == "first note\nsecond note"


def test_in_memory_backend_satisfies_the_protocol() -> None:
    """Both supported memory implementations satisfy the injected protocol."""
    assert isinstance(InMemoryWorkspaceMemory(), WorkspaceMemory)
    assert isinstance(SupabaseWorkspaceMemory("https://x.supabase.co", "key"), WorkspaceMemory)


def test_merge_is_bounded() -> None:
    """Memory merging cannot exceed the package storage bound."""
    huge = ["x" * (_MAX_MEMORY_CHARS + 1000)]
    assert len(_merge("", huge)) == _MAX_MEMORY_CHARS


def test_supabase_backend_builds_the_rest_url() -> None:
    """Supabase configuration produces the expected PostgREST endpoint and headers."""
    backend = SupabaseWorkspaceMemory(
        "https://abc.supabase.co/", "svc-key", table="workspace_memory"
    )
    assert backend._rest == "https://abc.supabase.co/rest/v1/workspace_memory"  # noqa: SLF001
    headers = backend._headers()  # noqa: SLF001
    assert headers["apikey"] == "svc-key"
    assert headers["Authorization"] == "Bearer svc-key"
