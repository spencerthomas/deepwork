"""Architecture tests for the independent package boundary."""

from __future__ import annotations

import ast
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src" / "deepwork_agent"
FORBIDDEN_IMPORT_ROOTS = {
    "apps",
    "deepwork_api",
    "fastapi",
    "packages",
    "sqlalchemy",
}


def _import_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.partition(".")[0])
    return roots


def _violations(source_root: Path) -> list[str]:
    violations: list[str] = []
    for path in sorted(source_root.rglob("*.py")):
        forbidden = sorted(_import_roots(path) & FORBIDDEN_IMPORT_ROOTS)
        if forbidden:
            imports = ", ".join(forbidden)
            violations.append(f"{path.relative_to(source_root)} imports {imports}")
    return violations


def test_source_has_no_application_or_framework_imports() -> None:
    """Every source file stays independent of application-service internals."""
    violations = _violations(SOURCE_ROOT)

    assert not violations, (
        "packages/agent violates ARCHITECTURE.md independent-package boundary:\n"
        + "\n".join(violations)
    )


def test_intentional_forbidden_import_is_detected(tmp_path: Path) -> None:
    """The boundary check names an importing file and its forbidden root."""
    fixture = tmp_path / "intentional_violation.py"
    fixture.write_text("import fastapi\n", encoding="utf-8")

    assert _violations(tmp_path) == ["intentional_violation.py imports fastapi"]
