"""Scan retained evidence for secrets, unsafe content, and hidden reasoning."""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

from .common import dump_json


PATTERNS = {
    "credential_assignment": re.compile(r"(?i)(api[_-]?key|password|secret|token)\s*[:=]\s*[\"']?[A-Za-z0-9_-]{12,}"),
    "unlabelled_secret": re.compile(
        r"\b(sk-(?:proj|live)-[A-Za-z0-9_-]{8,}|AKIA[A-Z0-9]{16}|gh[pousr]_[A-Za-z0-9]{20,})\b"
    ),
    "authorization_header": re.compile(r"(?i)authorization\s*:\s*(bearer|basic)\s+"),
    "raw_header": re.compile(
        r"(?im)^\s*(authorization|proxy-authorization|x-api-key|set-cookie|cookie)\s*:"
    ),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "hidden_reasoning": re.compile(
        r"(?i)(chain[- ]of[- ]thought|hidden_reasoning\s*[:=]|private_reasoning\s*[:=])"
    ),
    "unsafe_html": re.compile(r"(?i)<(script|iframe|object|embed)\b|javascript:"),
    "absolute_user_path": re.compile(
        r"(?:(?:/Users|/home)/[A-Za-z0-9._-]+/|[A-Za-z]:\\\\Users\\\\[A-Za-z0-9._-]+\\\\)"
    ),
    "reusable_endpoint": re.compile(
        r"https?://(?![A-Za-z0-9.-]*example\.invalid\b)[^\s\"']+"
        r"(?:[?&](?:token|signature|sig|key|expires)=|/signed/)"
    ),
    "customer_data": re.compile(
        r"(?i)(customer_(?:name|email|address)|production_tenant|real_customer|customer_record)\s*[:=]"
    ),
}

SKIP = {"scrub-report.json", "hashes.json", "review.json"}


def scan(root: Path) -> tuple[list[dict[str, object]], int]:
    findings: list[dict[str, object]] = []
    covered = 0
    max_mtime_ns = 0
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if path.name in SKIP or ".git" in path.parts:
            continue
        covered += 1
        max_mtime_ns = max(max_mtime_ns, path.stat().st_mtime_ns)
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            findings.append({"path": path.relative_to(root).as_posix(), "kind": "binary_evidence"})
            continue
        for kind, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append({"path": path.relative_to(root).as_posix(), "kind": kind})
    return findings, max_mtime_ns


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    args = parser.parse_args()
    root = Path(args.root)
    findings, max_mtime_ns = scan(root)
    report = {
        "schema_version": "dw.scrub-report.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "covered_file_count": sum(
            1 for path in root.rglob("*") if path.is_file() and path.name not in SKIP
        ),
        "covered_max_mtime_ns": max_mtime_ns,
        "finding_count": len(findings),
        "findings": findings,
        "categories": sorted(PATTERNS),
    }
    dump_json(root / "scrub-report.json", report)
    if findings:
        print(f"scrub failed: {len(findings)} finding(s)")
        return 1
    print("scrub passed: zero findings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
