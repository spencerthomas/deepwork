"""Reject changes outside the packet's governed paths."""

from __future__ import annotations

import argparse
import subprocess

from .common import ValidationError, require


ALLOWED_PREFIXES = (
    "tools/contract-spikes/research-writing-outcomes/",
    "docs/references/research/research-writing-outcomes/",
)
ALLOWED_EXACT = {
    "docs/exec-plans/external/DW-EXT-W1-RESEARCH-WRITING-OUTCOME-CONTRACT.md",
}


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    ).stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--include-untracked", action="store_true")
    args = parser.parse_args()
    try:
        changed = set(_git("diff", "--name-only", args.base).splitlines())
        changed.update(_git("diff", "--cached", "--name-only", args.base).splitlines())
        if args.include_untracked:
            changed.update(_git("ls-files", "--others", "--exclude-standard").splitlines())
        violations = sorted(
            path for path in changed
            if path not in ALLOWED_EXACT and not path.startswith(ALLOWED_PREFIXES)
        )
        require(not violations, f"out-of-scope paths changed: {violations}")
    except (subprocess.SubprocessError, ValidationError) as exc:
        print(f"scope validation failed: {exc}")
        return 1
    print(f"scope validation passed: {len(changed)} changed path(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
