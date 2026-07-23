"""Validate the retained matrix against immutable scope, upstream locks, and diff bytes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from coding_review_surface_spikes.contracts import exact_diff_errors, validate_matrix_document


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--scope", type=Path, required=True)
    parser.add_argument("--upstream-lock", type=Path, required=True)
    parser.add_argument("--require-complete-cross-product", action="store_true", required=True)
    parser.add_argument("--require-exact-diff", action="store_true", required=True)
    parser.add_argument("--reject-blocked-dependency-promotion", action="store_true", required=True)
    parser.add_argument("--reject-simulated-capabilities", action="store_true", required=True)
    parser.add_argument("--reject-unresolved-precedence-conflicts", action="store_true", required=True)
    args = parser.parse_args()
    matrix = _load(args.matrix)
    scope = _load(args.scope)
    upstream = _load(args.upstream_lock)
    errors = validate_matrix_document(matrix, scope, upstream)
    evidence_root = args.matrix.parent
    diff_document = _load(evidence_root / "fixtures/exact-diff.json")
    patch = (evidence_root / "fixtures/exact-review.patch").read_bytes()
    errors.extend(exact_diff_errors(diff_document, patch))
    unresolved = matrix.get("unresolved_precedence_conflicts", [])
    if unresolved:
        errors.append("unresolved precedence conflicts remain")
    if errors:
        for error in errors:
            print(error)
        return 1
    print(
        "validated "
        f"{len(matrix['rows'])} complete rows; exact diff and blocked-dependency rules passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
