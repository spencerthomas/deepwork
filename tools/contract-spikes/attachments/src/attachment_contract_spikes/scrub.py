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
    "authref-value": re.compile(
        r"(?i)[\"']?authref[\"']?\s*[=:]\s*[\"']"
        r"(?!synthetic|unknown|none|not-supplied)[^\"']+[\"']"
    ),
    "customer-or-tenant-value": re.compile(
        r"(?i)[\"']?(customer_id|tenant_id|customer_name|customer_email)[\"']?"
        r"\s*[=:]\s*[\"'](?!synthetic|unknown|none|not-supplied)[^\"']+[\"']"
    ),
    "email-address": re.compile(
        r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"
    ),
    "public-ipv4": re.compile(
        r"\b(?!10\.|127\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)"
        r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
    ),
}
SECRET_KINDS = {
    "credential-assignment",
    "authorization-value",
    "private-key",
    "authref-value",
}
PRIVATE_DATA_KINDS = {
    "customer-or-tenant-value",
    "email-address",
    "public-ipv4",
}
ENDPOINT_KINDS = {"signed-query", "reusable-endpoint"}
HEADER_KINDS = {"authorization-value", "cookie-value"}
BINARY_KINDS = {"unsafe-binary-nul", "non-utf8-content"}


def scan(root: Path) -> dict[str, object]:
    """Return a zero-tolerance scrub report."""
    findings: list[dict[str, str]] = []
    files_scanned = 0
    bytes_scanned = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
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
    finding_kinds = {finding["kind"] for finding in findings}
    return {
        "schema_version": "1.0",
        "scan_date": "2026-07-23",
        "files_scanned": files_scanned,
        "bytes_scanned": bytes_scanned,
        "findings": findings,
        "finding_count": len(findings),
        "zero_secrets": finding_kinds.isdisjoint(SECRET_KINDS),
        "zero_customer_or_tenant_data": finding_kinds.isdisjoint(PRIVATE_DATA_KINDS),
        "zero_reusable_endpoints_or_grants": finding_kinds.isdisjoint(ENDPOINT_KINDS),
        "zero_raw_headers_or_cookies": finding_kinds.isdisjoint(HEADER_KINDS),
        "zero_unsafe_binary_content": finding_kinds.isdisjoint(BINARY_KINDS),
        "zero_unsanitized_absolute_paths": "absolute-user-path" not in finding_kinds,
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
