"""Credential-free tests for the serving composition root's git-credential seam."""

from __future__ import annotations

import pytest

from deepwork_agent.runtime import _resolve_github_token


def test_resolve_github_token_none_when_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in (
        "DEEPWORK_GITHUB_APP_ID",
        "DEEPWORK_GITHUB_APP_PRIVATE_KEY",
        "DEEPWORK_GITHUB_TOKEN",
    ):
        monkeypatch.delenv(var, raising=False)
    assert _resolve_github_token() is None


def test_resolve_github_token_uses_pat_when_no_app(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPWORK_GITHUB_APP_ID", raising=False)
    monkeypatch.delenv("DEEPWORK_GITHUB_APP_PRIVATE_KEY", raising=False)
    monkeypatch.setenv("DEEPWORK_GITHUB_TOKEN", "ghp_example")
    assert _resolve_github_token() == "ghp_example"


def test_resolve_github_token_falls_back_to_pat_on_app_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # App id + a bad key -> minting raises -> we fall back to the PAT rather than
    # crash the task.
    monkeypatch.setenv("DEEPWORK_GITHUB_APP_ID", "123456")
    monkeypatch.setenv("DEEPWORK_GITHUB_APP_PRIVATE_KEY", "not-a-key-and-not-base64 !!!")
    monkeypatch.setenv("DEEPWORK_GITHUB_TOKEN", "ghp_fallback")
    assert _resolve_github_token() == "ghp_fallback"
