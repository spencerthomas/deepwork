"""Scan retained evidence for credential material and unsafe paths."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re

PATTERNS = {
    "github_tokens": re.compile(
        r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|ghs_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"
    ),
    "private_keys": re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
    "authorization_headers": re.compile(r"(?im)^\s*authorization\s*:\s*(?:bearer|token)\s+\S+"),
    "credential_remotes": re.compile(r"https://[^/\s:@]+:[^@\s]+@(?:github\.com|api\.github\.com)"),
    "auth_refs": re.compile(r'(?i)"auth_?ref"\s*:\s*"(?!none|null|not-supplied)[^"]+"'),
    "cookies": re.compile(r"(?im)^\s*(?:cookie|set-cookie)\s*:\s*\S+"),
    "absolute_user_paths": re.compile(r"/Users/[^/\s]+/"),
}


def scan(root: Path) -> dict[str, list[str]]:
    findings = {name: [] for name in PATTERNS}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "scrub-report.json":
            continue
        text = path.read_text(errors="replace")
        for name, pattern in PATTERNS.items():
            if pattern.search(text):
                findings[name].append(path.relative_to(root).as_posix())
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    findings = scan(args.root)
    report = {
        "scanned_at": date(2026, 7, 23).isoformat(),
        "root": "docs/references/research/coding-github-contracts",
        "status": "clean" if not any(findings.values()) else "rejected",
        "findings": findings,
        "counts": {name: len(paths) for name, paths in findings.items()},
    }
    output = args.root / "scrub-report.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if report["status"] != "clean":
        raise SystemExit(f"scrub rejected: {findings}")
    print("scrub clean: no credential material or unsanitized user paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
