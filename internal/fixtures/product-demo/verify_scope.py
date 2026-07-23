#!/usr/bin/env python3
"""Linked-worktree-safe, shell-free Git scope proof for this fixture cell."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath


FULL_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SCOPES = {
    "implementation": [
        "docs/exec-plans/active/DW-EXEC-M1-FIXTURE-CONTRACT.md",
        "internal/fixtures/product-demo/",
    ],
    "coordinator-transition": [
        "docs/exec-plans/active/DW-EXEC-M1-FIXTURE-CONTRACT.md",
        "docs/exec-plans/index.md",
    ],
}


def run_git(repo, *arguments):
    completed = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(arguments)} failed: {stderr}")
    return completed.stdout


def decode_text(value, label):
    try:
        return value.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError as error:
        raise ValueError(f"{label} is not valid UTF-8") from error


def validate_commit(repo, value, label):
    if not FULL_COMMIT_RE.fullmatch(value):
        raise ValueError(f"{label} must be an exact lowercase 40-character commit")
    run_git(repo, "cat-file", "-e", f"{value}^{{commit}}")


def validate_path(path):
    if not path:
        raise ValueError("empty Git path")
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or "." in pure.parts:
        raise ValueError(f"unsafe Git path: {path}")
    if "\x00" in path:
        raise ValueError("NUL in Git path")
    return path


def allowed(path, scope):
    entries = SCOPES[scope]
    return any(path == entry or (entry.endswith("/") and path.startswith(entry)) for entry in entries)


def parse_name_status(raw, label):
    if not raw:
        return []
    try:
        fields = raw.decode("utf-8", errors="strict").split("\x00")
    except UnicodeDecodeError as error:
        raise ValueError(f"{label} contains an undecodable path") from error
    if fields[-1] != "":
        raise ValueError(f"{label} is not NUL terminated")
    fields.pop()
    records = []
    index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        path_count = 2 if status.startswith(("R", "C")) else 1
        if index + path_count > len(fields):
            raise ValueError(f"{label} has a truncated name-status record")
        paths = [validate_path(path) for path in fields[index:index + path_count]]
        index += path_count
        records.append({"status": status, "paths": paths})
    return records


def parse_paths(raw, label):
    if not raw:
        return []
    try:
        fields = raw.decode("utf-8", errors="strict").split("\x00")
    except UnicodeDecodeError as error:
        raise ValueError(f"{label} contains an undecodable path") from error
    if fields[-1] != "":
        raise ValueError(f"{label} is not NUL terminated")
    return [validate_path(path) for path in fields[:-1]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--scope", required=True, choices=sorted(SCOPES))
    parser.add_argument("--base", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--include-untracked", action="store_true", required=True)
    args = parser.parse_args()

    repo_input = Path(args.repo).resolve()
    validate_commit(repo_input, args.base, "base")
    validate_commit(repo_input, args.candidate, "candidate")
    root = Path(decode_text(run_git(repo_input, "rev-parse", "--show-toplevel"), "worktree root"))
    git_dir = decode_text(
        run_git(root, "rev-parse", "--path-format=absolute", "--git-dir"),
        "Git directory",
    )
    common_dir = decode_text(
        run_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir"),
        "Git common directory",
    )
    head = decode_text(run_git(root, "rev-parse", "HEAD"), "HEAD")
    if head != args.candidate:
        raise ValueError("candidate must be the exact checked-out HEAD")
    run_git(root, "merge-base", "--is-ancestor", args.base, args.candidate)

    states = {
        "committed": parse_name_status(
            run_git(root, "diff", "--name-status", "-z", "--find-renames", args.base, args.candidate),
            "committed",
        ),
        "staged": parse_name_status(
            run_git(root, "diff", "--cached", "--name-status", "-z", "--find-renames"),
            "staged",
        ),
        "unstaged": parse_name_status(
            run_git(root, "diff", "--name-status", "-z", "--find-renames"),
            "unstaged",
        ),
        "untracked": [
            {"status": "?", "paths": [path]}
            for path in parse_paths(
                run_git(root, "ls-files", "--others", "--exclude-standard", "-z"),
                "untracked",
            )
        ],
    }
    rejected = []
    for state, records in states.items():
        for record in records:
            for path in record["paths"]:
                if not allowed(path, args.scope):
                    rejected.append({"state": state, "status": record["status"], "path": path})

    report = {
        "scope": args.scope,
        "base": args.base,
        "candidate": args.candidate,
        "worktreeRoot": str(root),
        "gitDirectory": git_dir,
        "gitCommonDirectory": common_dir,
        "allowlist": SCOPES[args.scope],
        "states": states,
        "rejected": rejected,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if rejected else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError) as error:
        print(f"scope_error={error}", file=sys.stderr)
        raise SystemExit(2)
