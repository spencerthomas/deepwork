from __future__ import annotations

from auth_contract_spikes.scrub import scan


def test_scrubber_allows_redacted_placeholders(tmp_path) -> None:
    (tmp_path / "fixture.json").write_text(
        '{"Authorization":"<stripped>","Cookie":"<redacted>","X-Api-Key":"<redacted>"}'
    )
    assert scan(tmp_path) == []


def test_scrubber_finds_secret_shaped_values_without_retaining_them(tmp_path) -> None:
    (tmp_path / "fixture.txt").write_text(
        "LANGSMITH_API_KEY=" + "lsv2_" + "sk_" + ("X" * 20)
    )
    findings = scan(tmp_path)
    assert {finding["type"] for finding in findings} == {
        "environment-dump",
        "langsmith-key",
    }
    assert all("X" not in str(finding) for finding in findings)


def test_scrubber_rejects_opaque_raw_authority_values(tmp_path) -> None:
    (tmp_path / "retained.json").write_text(
        '{"X-Api-Key":"opaque-value","X-Tenant-Id":"tenant-alias",'
        '"X-Organization-Id":"org-alias"}'
    )
    findings = scan(tmp_path)
    assert [finding["type"] for finding in findings] == [
        "raw-sensitive-header-or-context-value",
        "raw-sensitive-header-or-context-value",
        "raw-sensitive-header-or-context-value",
    ]
    assert all("opaque" not in str(finding) for finding in findings)


def test_scrubber_rejects_placeholder_prefix_and_arbitrary_alias_bypass(
    tmp_path,
) -> None:
    (tmp_path / "retained.json").write_text(
        '{"X-Api-Key":"<synthetic-key>opaque-tail",'
        '"X-Tenant-Id":"<workspace-customer-alias>"}'
    )
    findings = scan(tmp_path)
    assert len(findings) == 2
    assert all(
        finding["type"] == "raw-sensitive-header-or-context-value"
        for finding in findings
    )


def test_scrubber_rejects_raw_header_lines_and_proxy_authority(tmp_path) -> None:
    (tmp_path / "retained.md").write_text("X-Api-Key: opaque-value\n")
    (tmp_path / "retained.json").write_text(
        '{"Proxy-Authorization":"Basic opaque-value"}'
    )
    assert {finding["type"] for finding in scan(tmp_path)} == {
        "raw-sensitive-header-line-value",
        "raw-sensitive-header-or-context-value",
    }


def test_scrubber_rejects_credential_handles_and_schemeless_origins(
    tmp_path,
) -> None:
    (tmp_path / "retained.txt").write_text(
        "credential_id: retained-handle\n"
        "tenant.example-deployment.langgraph.app\n"
    )
    assert {finding["type"] for finding in scan(tmp_path)} == {
        "credential-reference-value",
        "schemeless-reusable-instance-endpoint",
    }
