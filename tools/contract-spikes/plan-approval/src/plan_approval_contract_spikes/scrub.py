from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


RULES = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "bearer-token": re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}", re.I),
    "cookie-header": re.compile(r"^\s*(?:set-)?cookie\s*:", re.I | re.M),
    "credential-assignment": re.compile(
        r"\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*[\"']?[^\s,\"']{8,}",
        re.I,
    ),
    "unsanitized-user-path": re.compile(r"/Users/[A-Za-z0-9._-]+/"),
    "reusable-endpoint": re.compile(r"https?://(?!example\.invalid\b)[^\s)\"']+"),
    "hidden-reasoning": re.compile(r"\b(?:chain[- ]of[- ]thought|hidden reasoning)\b", re.I),
}

TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".txt", ".toml", ".yaml", ".yml"}


def scan(root: Path) -> dict[str, object]:
    findings: list[dict[str, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "scrub-report.json":
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        for rule, pattern in RULES.items():
            if pattern.search(text):
                findings.append({"path": str(path.relative_to(root)), "rule": rule})
    return {
        "schema_version": "plan-approval-scrub.v1",
        "root": ".",
        "files_scanned": sum(
            1
            for path in root.rglob("*")
            if path.is_file()
            and path.name != "scrub-report.json"
            and path.suffix.lower() in TEXT_SUFFIXES
        ),
        "finding_count": len(findings),
        "findings": findings,
        "status": "clean" if not findings else "rejected",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    report = scan(args.root)
    output = args.root / "scrub-report.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if report["finding_count"]:
        raise SystemExit(f"scrub rejected {report['finding_count']} finding(s)")
    print(f"scrubbed {report['files_scanned']} text files")


if __name__ == "__main__":
    main()
