from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


RULES = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "bearer-token": re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}", re.I),
    "basic-auth": re.compile(r"\bBasic\s+[A-Za-z0-9+/=]{8,}", re.I),
    "cookie-header": re.compile(r"^\s*(?:set-)?cookie\s*:", re.I | re.M),
    "auth-or-api-key-header": re.compile(
        r"^\s*(?:authorization|x-api-key|api-key)\s*:", re.I | re.M
    ),
    "credential-assignment": re.compile(
        r"\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*[\"']?[^\s,\"']{8,}",
        re.I,
    ),
    "unsanitized-user-path": re.compile(r"/Users/[A-Za-z0-9._-]+/"),
    "unsanitized-linux-home": re.compile(r"/home/[A-Za-z0-9._-]+/"),
    "unsanitized-windows-user-path": re.compile(
        r"[A-Za-z]:\\Users\\[A-Za-z0-9._-]+\\"
    ),
    "reusable-endpoint": re.compile(r"https?://(?!example\.invalid\b)[^\s)\"']+"),
    "hidden-reasoning": re.compile(r"\b(?:chain[- ]of[- ]thought|hidden reasoning)\b", re.I),
    "email-address": re.compile(
        r"\b[A-Za-z0-9._%+-]+@(?!example\.invalid\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    ),
    "non-synthetic-customer-identity": re.compile(
        r"\"(?:customer|tenant|workspace)_(?:id|name)\"\s*:\s*"
        r"\"(?![^\"]*synthetic)[^\"]+\"",
        re.I,
    ),
}

TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".txt", ".toml", ".yaml", ".yml"}
CATEGORY_BY_RULE = {
    "private-key": "secrets_or_credentials",
    "bearer-token": "secrets_or_credentials",
    "basic-auth": "secrets_or_credentials",
    "credential-assignment": "secrets_or_credentials",
    "cookie-header": "raw_headers_or_cookies",
    "auth-or-api-key-header": "raw_headers_or_cookies",
    "unsanitized-user-path": "unsanitized_absolute_paths",
    "unsanitized-linux-home": "unsanitized_absolute_paths",
    "unsanitized-windows-user-path": "unsanitized_absolute_paths",
    "reusable-endpoint": "reusable_endpoints",
    "hidden-reasoning": "hidden_reasoning",
    "email-address": "customer_or_tenant_data",
    "non-synthetic-customer-identity": "customer_or_tenant_data",
}
CATEGORIES = (
    "secrets_or_credentials",
    "customer_or_tenant_data",
    "reusable_endpoints",
    "raw_headers_or_cookies",
    "hidden_reasoning",
    "unsanitized_absolute_paths",
)


def scan(root: Path) -> dict[str, object]:
    findings: list[dict[str, str]] = []
    categories = {category: 0 for category in CATEGORIES}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "scrub-report.json":
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        for rule, pattern in RULES.items():
            if pattern.search(text):
                category = CATEGORY_BY_RULE[rule]
                findings.append(
                    {
                        "path": str(path.relative_to(root)),
                        "rule": rule,
                        "category": category,
                    }
                )
                categories[category] += 1
    return {
        "schema_version": "plan-approval-scrub.v1",
        "generated_at": None,
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
        "categories": categories,
        "status": "clean" if not findings else "rejected",
        "attestation": (
            "Only deterministic synthetic identities and pinned public provenance "
            "are retained; pattern scanning is defense in depth, not proof that "
            "arbitrary customer content is safe."
        ),
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
