"""Scrub retained evidence for credentials, host paths, active content, and control abuse."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TEXT_SUFFIXES = {".json", ".md", ".txt", ".patch"}
SKIP_NAMES = {"scrub-report.json"}
RULES = {
    "credential": re.compile(
        r"(?i)(sk-[a-z0-9_-]{12,}|bearer\s+[a-z0-9._~-]{12,}|"
        r"(?:authorization|cookie|set-cookie|x-api-key)[\"']?\s*:\s*[\"']?\s*(?!none|null)[^\"'\s,}]+)"
    ),
    "credential_reference_value": re.compile(
        r"(?i)\b(?:authref|secretref|credentialref)\s*[:=]\s*[\"']?(?!none|null)[a-z0-9._/-]{3,}"
    ),
    "host_path": re.compile(r"(?:/Users/|/home/|/private/(?:tmp|var)/|[A-Za-z]:\\\\)"),
    "active_content": re.compile(r"(?i)<\s*(?:script|iframe|object|embed|svg|html)\b"),
    "control_character": re.compile(r"[\x00-\x08\x0b-\x1f\x7f]"),
    "reusable_signed_url": re.compile(r"(?i)https?://[^\s\"')]+(?:token|signature|sig|key)="),
}


def scan(root: Path) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    scanned = 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            findings.append(
                {
                    "file": str(path.relative_to(root)),
                    "line": 0,
                    "rule": "symlink",
                }
            )
            continue
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES or path.name in SKIP_NAMES:
            continue
        try:
            path.resolve().relative_to(root.resolve())
        except ValueError:
            findings.append(
                {
                    "file": str(path.relative_to(root)),
                    "line": 0,
                    "rule": "root_escape",
                }
            )
            continue
        scanned += 1
        text = path.read_text(encoding="utf-8")
        for rule, pattern in RULES.items():
            for match in pattern.finditer(text):
                findings.append(
                    {
                        "file": str(path.relative_to(root)),
                        "line": text.count("\n", 0, match.start()) + 1,
                        "rule": rule,
                    }
                )
    return {
        "schema_version": "1.0",
        "root": ".",
        "files_scanned": scanned,
        "finding_counts": {
            rule: sum(item["rule"] == rule for item in findings)
            for rule in (*RULES, "symlink", "root_escape")
        },
        "findings": findings,
        "passed": not findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    report = scan(args.root)
    (args.root / "scrub-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"scrubbed {report['files_scanned']} evidence files; findings={len(report['findings'])}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
