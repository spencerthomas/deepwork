"""Package-local dependency boundary checks."""

from __future__ import annotations

import ast
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src" / "deepwork_api"
PACKAGE_FORBIDDEN = {"apps", "deepagents", "langchain", "langgraph", "packages", "sqlalchemy"}
DOMAIN_ALLOWED = {"__future__", "dataclasses", "deepwork_api", "enum"}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", maxsplit=1)[0])
    return imported


def test_package_has_no_forbidden_deep_work_or_provider_imports() -> None:
    violations: dict[str, set[str]] = {}
    for path in SOURCE_ROOT.rglob("*.py"):
        forbidden = _imports(path) & PACKAGE_FORBIDDEN
        if forbidden:
            violations[str(path.relative_to(SOURCE_ROOT))] = forbidden
    assert violations == {}


def test_domain_uses_only_the_standard_library() -> None:
    violations: dict[str, set[str]] = {}
    for path in (SOURCE_ROOT / "domain").rglob("*.py"):
        forbidden = _imports(path) - DOMAIN_ALLOWED
        if forbidden:
            violations[str(path.relative_to(SOURCE_ROOT))] = forbidden
    assert violations == {}
