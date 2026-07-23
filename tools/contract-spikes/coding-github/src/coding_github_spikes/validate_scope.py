"""Reject changes outside the packet's allowed paths."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

ALLOWED = (
    "tools/contract-spikes/coding-github/",
    "docs/references/research/coding-github-contracts/",
)
PACKET = "docs/exec-plans/external/DW-EXT-W1-CODING-GITHUB-CONTRACT-RESEARCH.md"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--include-untracked", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()
    tracked = subprocess.run(
        ["git", "diff", "--name-only", args.base],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    untracked: list[str] = []
    if args.include_untracked:
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    changed = sorted(set(tracked + untracked))
    denied = [name for name in changed if name != PACKET and not name.startswith(ALLOWED)]
    if denied:
        raise SystemExit(f"out-of-scope paths: {denied}")
    print(f"scope valid: {len(changed)} changed paths are packet-owned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

