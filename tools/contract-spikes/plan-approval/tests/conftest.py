from __future__ import annotations

import socket

import pytest


def pytest_addoption(parser):
    parser.addoption("--live-profile")
    parser.addoption("--evidence-dir")


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("network access is denied in the offline harness")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
