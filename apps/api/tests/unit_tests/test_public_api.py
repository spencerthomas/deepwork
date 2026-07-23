"""Public import and package-data tests."""

from __future__ import annotations

import subprocess
import sys
from importlib.resources import files

import deepwork_api


def test_public_api_is_deliberate_and_typed() -> None:
    assert deepwork_api.__all__ == ["create_app"]
    assert callable(deepwork_api.create_app)
    assert files("deepwork_api").joinpath("py.typed").is_file()


def test_public_import_is_lazy_and_does_not_read_environment() -> None:
    program = """
import os
import sys

class DeniedEnvironment:
    def _deny(self, *args, **kwargs):
        raise AssertionError("public package import attempted to read the environment")

    __contains__ = _deny
    __getitem__ = _deny
    __iter__ = _deny
    __len__ = _deny
    get = _deny
    items = _deny
    keys = _deny
    values = _deny

os.environ = DeniedEnvironment()
from deepwork_api import create_app
assert callable(create_app)
assert "fastapi" not in sys.modules
assert "pydantic" not in sys.modules
assert "deepwork_api.bootstrap.api" not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-c", program],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
