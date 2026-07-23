from __future__ import annotations

import socket

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--live-profile")
    parser.addoption("--read-grant")
    parser.addoption("--terminal-grant")
    parser.addoption("--evidence-dir")


@pytest.fixture(autouse=True)
def deny_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*args, **kwargs):
        del args, kwargs
        raise RuntimeError("network denied by offline contract suite")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
