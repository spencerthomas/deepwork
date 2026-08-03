#!/usr/bin/env python3
"""Fail closed when credential canaries or token-in-sandbox fallbacks are retained."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable
from pathlib import Path

CANARY = b"deepwork-security-canary-4f3c7d91"
FORBIDDEN_AGENT_MARKERS = (
    b"DEEPWORK_GITHUB_TOKEN",
    b".git-credentials",
    b"x-access-token:",
    b"credential.helper store",
)
PUBLIC_SCHEMA_MARKERS = (
    b'"authRef"',
    b'"credentialRef"',
    b'"providerToken"',
    b'"refreshToken"',
)
MAX_FILE_BYTES = 64 * 1024 * 1024


def _files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        try:
            if path.is_file():
                yield path
                continue
            for candidate in sorted(path.rglob("*")):
                if candidate.is_file() and not candidate.is_symlink():
                    yield candidate
        except OSError:
            continue


def _scan(paths: Iterable[Path], markers: Iterable[bytes]) -> list[str]:
    findings: list[str] = []
    marker_set = tuple(markers)
    for path in _files(paths):
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            content = path.read_bytes()
        except OSError:
            continue
        for marker in marker_set:
            if marker in content:
                findings.append(
                    f"{path}: retained forbidden marker {marker.decode('ascii')!r}"
                )
    return findings


def _self_test() -> None:
    assert CANARY in b"prefix deepwork-security-canary-4f3c7d91 suffix"
    assert all(marker not in b"safe artifact" for marker in FORBIDDEN_AGENT_MARKERS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    root = args.root.resolve()
    _self_test()

    findings = _scan(
        (root / "packages/agent/src/deepwork_agent",),
        FORBIDDEN_AGENT_MARKERS,
    )
    findings.extend(
        _scan(
            (root / "apps/api/openapi.json",),
            PUBLIC_SCHEMA_MARKERS,
        )
    )
    findings.extend(
        _scan(
            (
                root / "apps/web/.next/static",
                root / "output/playwright/security-results",
                root / "output/playwright/security-report",
            ),
            (CANARY,),
        )
    )
    if findings:
        for finding in findings:
            print(finding, file=sys.stderr)
        return 1
    print("credential boundary scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
