from __future__ import annotations

import argparse
import subprocess


ALLOWED_PREFIXES = (
    "tools/contract-spikes/plan-approval/",
    "docs/references/research/plan-approval-contract-spikes/",
)
ALLOWED_FILES = (
    "docs/exec-plans/external/DW-EXT-W1-FIRST-TASK-PLAN-APPROVAL.md",
)


def _git(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True
    )
    return [line for line in result.stdout.splitlines() if line]


def validate_scope(base: str, *, include_untracked: bool) -> list[str]:
    paths = set(_git("diff", "--name-only", base))
    if include_untracked:
        paths.update(_git("ls-files", "--others", "--exclude-standard"))
    rejected = sorted(
        path
        for path in paths
        if path not in ALLOWED_FILES
        and not any(path.startswith(prefix) for prefix in ALLOWED_PREFIXES)
    )
    if rejected:
        raise SystemExit("out-of-scope paths:\n" + "\n".join(rejected))
    return sorted(paths)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--include-untracked", action="store_true")
    args = parser.parse_args()
    paths = validate_scope(args.base, include_untracked=args.include_untracked)
    print(f"validated {len(paths)} changed path(s) inside dispatch scope")


if __name__ == "__main__":
    main()
