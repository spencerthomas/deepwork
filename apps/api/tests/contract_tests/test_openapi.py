"""Contract test: the committed OpenAPI document must not drift from the app."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from export_openapi import OPENAPI_PATH, render_openapi  # noqa: E402


def test_committed_openapi_matches_application() -> None:
    """apps/api/openapi.json equals create_app().openapi(); regenerate on drift."""

    assert OPENAPI_PATH.exists(), (
        "apps/api/openapi.json is missing; run "
        "'uv run --frozen python scripts/export_openapi.py --write'"
    )
    committed = OPENAPI_PATH.read_text(encoding="utf-8")
    assert committed == render_openapi(), (
        "apps/api/openapi.json is out of date; run "
        "'uv run --frozen python scripts/export_openapi.py --write'"
    )


def test_openapi_documents_the_versioned_surface() -> None:
    """The exported contract covers the health check and every /api/v1 route."""

    import json

    document = json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))
    paths = set(document["paths"])
    assert "/health" in paths
    assert {path for path in paths if path.startswith("/api/v1/")} == {
        "/api/v1/demo/status",
        "/api/v1/tasks",
        "/api/v1/tasks/{task_id}",
        "/api/v1/tasks/{task_id}/decisions",
        "/api/v1/tasks/{task_id}/events",
        "/api/v1/tasks/{task_id}/plan",
        "/api/v1/tasks/{task_id}/result",
    }
