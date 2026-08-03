"""Credential-boundary tests for the serving composition root."""

from __future__ import annotations

import inspect

from deepwork_agent import runtime


def test_runtime_has_no_token_in_sandbox_fallback() -> None:
    """Private GitHub stays disabled until the reviewed auth proxy exists."""
    source = inspect.getsource(runtime)
    for forbidden in (
        "DEEPWORK_GITHUB_TOKEN",
        ".git-credentials",
        "x-access-token:",
        "credential.helper store",
    ):
        assert forbidden not in source

    assert not hasattr(runtime, "_resolve_github_token")
    assert not hasattr(runtime, "_configure_sandbox_github")


def test_runtime_reads_no_process_environment_directly() -> None:
    """Serving composition consumes typed config instead of ambient process state."""
    source = inspect.getsource(runtime)

    assert "os.environ" not in source
    assert "os.getenv" not in source
