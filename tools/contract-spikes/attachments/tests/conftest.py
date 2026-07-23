"""Global network denial and explicit live-profile gating."""

from __future__ import annotations

import socket
from pathlib import Path

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--live-profile", default=None)
    parser.addoption("--evidence-dir", type=Path, default=None)


@pytest.fixture(autouse=True)
def deny_network(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> None:
    if request.node.get_closest_marker("live_contract"):
        return

    def blocked(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network access denied by attachment contract harness")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
