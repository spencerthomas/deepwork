from __future__ import annotations


def pytest_addoption(parser) -> None:
    group = parser.getgroup("live_contract")
    group.addoption("--live-profile", default="")
    group.addoption("--evidence-dir", default="")
    group.addoption("--live-base-url", default="")
    group.addoption("--live-account-tier", default="")
    group.addoption("--live-region", default="")
    group.addoption("--live-server-revision", default="")
