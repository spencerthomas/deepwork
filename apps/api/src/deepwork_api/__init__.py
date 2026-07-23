"""Public entry points for the Deep Work application-service scaffold."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

__all__ = ["create_app"]


def create_app(*, task_database_path: Path | None = None) -> FastAPI:
    """Load and create the fixture application only when explicitly called."""

    from deepwork_api.bootstrap.api import create_app as _create_app

    return _create_app(task_database_path=task_database_path)
