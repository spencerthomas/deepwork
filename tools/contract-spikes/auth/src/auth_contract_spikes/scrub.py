"""Secret and tenant-data scrubber for retained evidence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from .catalog import COLLECTED_AT

TEXT_SUFFIXES = {".json", ".md", ".txt"}
URL_PATTERN = re.compile(r"https?://[A-Za-z0-9._~:/?#[\]@!$&'()*+,;=%-]+")
ALLOWED_PUBLIC_HOSTS = {
    "api.example.com",
    "api.host.langchain.com",
    "api.smith.langchain.com",
    "apac.api.host.langchain.com",
    "apac.api.smith.langchain.com",
    "aws.api.host.langchain.com",
    "aws.api.smith.langchain.com",
    "docs.langchain.com",
    "eu.api.host.langchain.com",
    "eu.api.smith.langchain.com",
    "pypi.org",
    "registry.npmjs.org",
}
SECRET_PATTERNS = {
    "langsmith-key": re.compile(r"\blsv2_(?:pt|sk)_[A-Za-z0-9_-]{12,}\b"),
    "legacy-langsmith-key": re.compile(r"\bls__[A-Za-z0-9_-]{12,}\b"),
    "bearer-value": re.compile(
        r"(?i)\bauthorization\b[\"':\s]+bearer\s+(?!<)[A-Za-z0-9._~+/-]{8,}"
    ),
    "cookie-value": re.compile(
        r'(?i)"(?:cookie|set-cookie)"\s*:\s*"(?!<(?:redacted|stripped)>)[^"]+"'
    ),
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "environment-dump": re.compile(
        r"(?m)^(?:LANGSMITH_API_KEY|LANGCHAIN_API_KEY|AUTH_CONTRACT_LIVE_API_KEY)="
    ),
    "credential-reference": re.compile(
        r"(?i)\b(?:authref|vault://|secret-manager://|credential-reference://)[A-Za-z0-9_./:-]*"
    ),
    "credential-reference-value": re.compile(
        r'(?im)"?(?:auth_ref|credential_id|credential_ref|'
        r'credential_reference)"?\s*[:=]\s*"?'
        r"(?!<(?:redacted|stripped|opaque)>|null\b|none\b)"
        r"[A-Za-z0-9][A-Za-z0-9_./:-]*"
    ),
    "url-userinfo-or-secret-query": re.compile(
        r"https?://[^/\s:@]+:[^/\s@]+@|https?://[^\s]+[?&](?:token|key|secret|authorization)=",
        re.IGNORECASE,
    ),
    "customer-email": re.compile(
        r"\b[A-Za-z0-9._%+-]+@(?!example\.(?:com|org)\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    ),
    "customer-or-tenant-uuid": re.compile(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b"
    ),
    "raw-sensitive-header-or-context-value": re.compile(
        r'(?i)"(?:authorization|proxy-authorization|cookie|set-cookie|'
        r'x-api-key|x-tenant-id|x-organization-id|'
        r'api_key|workspace_id|tenant_id|organization_id)"\s*:\s*"'
        r'(?!<(?:redacted|stripped|synthetic-key|workspace-id|'
        r'wrong-workspace-id|organization-id|selector-only-workspace-id|'
        r'wrong-selector-workspace-id)>")[^"]+"'
    ),
    "raw-sensitive-header-line-value": re.compile(
        r"(?im)^[ \t>*-]*(?:authorization|proxy-authorization|cookie|"
        r"set-cookie|x-api-key|x-tenant-id|x-organization-id)\s*:\s*"
        r"(?!<(?:redacted|stripped|synthetic-key|workspace-id|"
        r"wrong-workspace-id|organization-id|selector-only-workspace-id|"
        r"wrong-selector-workspace-id)>\s*$)[^\r\n]+$"
    ),
    "schemeless-reusable-instance-endpoint": re.compile(
        r"(?i)(?<![/@A-Za-z0-9.-])(?:[A-Za-z0-9-]+\.)+"
        r"langgraph\.app(?::[0-9]{1,5})?(?:/[^\s]*)?"
    ),
}


def scan(root: Path) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            findings.append(
                {
                    "path": str(path.relative_to(root)),
                    "line": 0,
                    "type": "symlink",
                }
            )
            continue
        if (
            not path.is_file()
            or path.suffix.lower() not in TEXT_SUFFIXES
            or path.name == "scrub-report.json"
        ):
            continue
        text = path.read_text(errors="replace")
        for finding_type, pattern in SECRET_PATTERNS.items():
            for match in pattern.finditer(text):
                findings.append(
                    {
                        "path": str(path.relative_to(root)),
                        "line": text.count("\n", 0, match.start()) + 1,
                        "type": finding_type,
                    }
                )
        for match in URL_PATTERN.finditer(text):
            from urllib.parse import urlsplit

            hostname = (urlsplit(match.group()).hostname or "").lower()
            if hostname not in ALLOWED_PUBLIC_HOSTS:
                findings.append(
                    {
                        "path": str(path.relative_to(root)),
                        "line": text.count("\n", 0, match.start()) + 1,
                        "type": "account-specific-reusable-instance-endpoint",
                    }
                )
    return findings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    findings = scan(args.root)
    report = {
        "schema_version": 1,
        "collection_date": COLLECTED_AT,
        "root": "docs/references/research/auth-contract-spikes",
        "categories": [
            "secret",
            "credential-reference",
            "customer-or-tenant-value",
            "account-specific-reusable-instance-endpoint",
            "raw-authorization-value",
            "cookie",
            "environment-dump",
        ],
        "finding_count": len(findings),
        "findings": findings,
        "attestation": (
            "pass: no prohibited values found"
            if not findings
            else "fail: prohibited values found"
        ),
    }
    (args.root / "scrub-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    if findings:
        raise SystemExit(f"scrub-failed:{len(findings)}")
    print("scrub-pass:0-findings")


if __name__ == "__main__":
    main()
