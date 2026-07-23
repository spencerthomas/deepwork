"""Fail closed when retained evidence contains secret-like or identifying data."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".txt"}
SKIP_NAMES = {"scrub-report.json"}
RULES = {
    "secret": re.compile(r"(?i)(sk-[a-z0-9_-]{12,}|bearer\\s+[a-z0-9._~-]{12,}|x-api-key\\s*[:=]\\s*[^<\\s]+)"),
    "credential_reference": re.compile(r"(?i)\\b(authref|secretref|credentialref)\\s*[:=]\\s*[^<\\s]+"),
    "tenant_or_customer": re.compile(r"(?i)\\b(tenant|customer)[_-]?id\\s*[:=]\\s*(?!null|none|synthetic)[a-z0-9_-]+"),
    "unapproved_host": re.compile(r"https?://(?!localhost(?::\\d+)?(?:/|$)|127\\.0\\.0\\.1(?::\\d+)?(?:/|$)|synthetic\\.invalid(?:/|$))[^\\s\"')]+"),
}


def scan(root: Path) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    files_scanned = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES or path.name in SKIP_NAMES:
            continue
        files_scanned += 1
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
    counts = {rule: sum(item["rule"] == rule for item in findings) for rule in RULES}
    return {
        "schema_version": "1.0",
        "root": ".",
        "files_scanned": files_scanned,
        "findings": findings,
        "finding_counts": counts,
        "passed": not findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    report = scan(args.root)
    output = args.root / "scrub-report.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"scrubbed {report['files_scanned']} evidence files; findings={len(report['findings'])}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
