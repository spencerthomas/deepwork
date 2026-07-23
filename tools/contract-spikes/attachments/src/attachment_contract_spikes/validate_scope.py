"""Validate immutable scope history and allowed-path confinement."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from attachment_contract_spikes.scope import SCOPE_RELATIVE_PATH


ALLOWED_PREFIXES = (
    "tools/contract-spikes/attachments/",
    "docs/references/research/attachment-contract-spikes/",
)
ALLOWED_EXACT = {
    "docs/exec-plans/external/DW-EXT-W1-FIRST-TASK-SAFE-ATTACHMENTS.md"
}


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        check=check,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout


def _paths(output: str) -> set[str]:
    return {line.strip() for line in output.splitlines() if line.strip()}


def is_allowed(path: str) -> bool:
    return path in ALLOWED_EXACT or path.startswith(ALLOWED_PREFIXES)


def validate(base: str, *, include_untracked: bool) -> set[str]:
    """Reject path expansion and any mutation of the frozen scope blob."""
    git("merge-base", "--is-ancestor", base, "HEAD")
    changed = _paths(git("diff", "--name-only", f"{base}...HEAD"))
    changed |= _paths(git("diff", "--name-only"))
    changed |= _paths(git("diff", "--cached", "--name-only"))
    if include_untracked:
        changed |= _paths(git("ls-files", "--others", "--exclude-standard"))
    forbidden = sorted(path for path in changed if not is_allowed(path))
    if forbidden:
        raise ValueError(f"out-of-scope paths: {forbidden}")
    plans = sorted(path for path in changed if path.startswith("docs/plans/"))
    if plans:
        raise ValueError(f"forbidden docs/plans mutation: {plans}")

    scope_path = SCOPE_RELATIVE_PATH.as_posix()
    add_commits = _paths(
        git("log", "--diff-filter=A", "--format=%H", "--", scope_path)
    )
    if len(add_commits) != 1:
        raise ValueError(f"scope must have exactly one add commit, found {len(add_commits)}")
    add_commit = next(iter(add_commits))
    committed = subprocess.run(
        ["git", "show", f"{add_commit}:{scope_path}"],
        check=True,
        capture_output=True,
        timeout=30,
    ).stdout
    current = Path(scope_path).read_bytes()
    if committed != current:
        raise ValueError("matrix-scope.json changed after its immutable add commit")
    matrix_path = (
        "docs/references/research/attachment-contract-spikes/matrix.json"
    )
    matrix_add = _paths(
        git("log", "--diff-filter=A", "--format=%H", "--", matrix_path)
    )
    for commit in matrix_add:
        git("merge-base", "--is-ancestor", add_commit, commit)
        if commit == add_commit:
            raise ValueError("matrix scope and observations were committed together")
    print(f"scope valid; {len(changed)} allowed path(s)")
    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--include-untracked", action="store_true")
    args = parser.parse_args()
    validate(args.base, include_untracked=args.include_untracked)


if __name__ == "__main__":
    main()
