"""Prove every change since the exact base is confined to packet-authorized paths."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ALLOWED_PREFIXES = (
    "tools/contract-spikes/coding-review-surfaces/",
    "docs/references/research/coding-review-surfaces-contracts/",
)
ALLOWED_EXACT = {
    "docs/exec-plans/external/DW-EXT-W1-CODING-REVIEW-SURFACES-CONTRACT-RESEARCH.md"
}


def _run(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def _allowed(path: str) -> bool:
    return path in ALLOWED_EXACT or any(path.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--include-untracked", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()
    if not (root / ".git").exists():
        print("validation must run from the assigned worktree root")
        return 1
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", args.base, "HEAD"],
        check=False,
    ).returncode:
        print("exact base is not an ancestor of HEAD")
        return 1
    changed = set(_run("git", "diff", "--name-only", args.base).splitlines())
    changed.update(_run("git", "diff", "--cached", "--name-only", args.base).splitlines())
    if args.include_untracked:
        changed.update(_run("git", "ls-files", "--others", "--exclude-standard").splitlines())
    rejected = sorted(path for path in changed if path and not _allowed(path))
    if rejected:
        for path in rejected:
            print(f"out-of-scope path: {path}")
        return 1
    print(f"validated {len(changed)} changed or untracked paths against exact base {args.base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
