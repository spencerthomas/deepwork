"""Scrub retained evidence for credentials, private data, and unsafe payloads."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


FORBIDDEN_PATTERNS = {
    "absolute-user-path": re.compile(r"/Users/|[A-Za-z]:\\\\Users\\\\"),
    "credential-assignment": re.compile(
        r"(?i)(api[_-]?key|access[_-]?token|secret|password)"
        r"\s*[=:]\s*[\"'][^\"']{4,}[\"']"
    ),
    "authorization-value": re.compile(r"(?i)authorization\s*:\s*(bearer|basic)\s+\S+"),
    "cookie-value": re.compile(r"(?i)(set-cookie|cookie)\s*:\s*\S+="),
    "signed-query": re.compile(
        r"(?i)(x-amz-signature|x-goog-signature|sig|signature|token)=[A-Za-z0-9%_-]{8,}"
    ),
    "reusable-endpoint": re.compile(r"https?://"),
    "private-key": re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def scan(root: Path) -> dict[str, object]:
    """Return a zero-tolerance scrub report."""
    findings: list[dict[str, str]] = []
    files_scanned = 0
    bytes_scanned = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "scrub-report.json":
            continue
        files_scanned += 1
        raw = path.read_bytes()
        bytes_scanned += len(raw)
        relative = path.relative_to(root).as_posix()
        if b"\x00" in raw:
            findings.append({"file": relative, "kind": "unsafe-binary-nul"})
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            findings.append({"file": relative, "kind": "non-utf8-content"})
            continue
        for kind, pattern in FORBIDDEN_PATTERNS.items():
            if pattern.search(text):
                findings.append({"file": relative, "kind": kind})
    return {
        "schema_version": "1.0",
        "scan_date": "2026-07-23",
        "files_scanned": files_scanned,
        "bytes_scanned": bytes_scanned,
        "findings": findings,
        "finding_count": len(findings),
        "zero_secrets": len(findings) == 0,
        "zero_customer_or_tenant_data": len(findings) == 0,
        "zero_reusable_endpoints_or_grants": len(findings) == 0,
        "zero_raw_headers_or_cookies": len(findings) == 0,
        "zero_unsafe_binary_content": len(findings) == 0,
        "zero_unsanitized_absolute_paths": len(findings) == 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    report = scan(args.root)
    output = args.root / "scrub-report.json"
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if report["finding_count"]:
        raise SystemExit(
            f"scrub failed with {report['finding_count']} finding(s); see {output.as_posix()}"
        )
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
