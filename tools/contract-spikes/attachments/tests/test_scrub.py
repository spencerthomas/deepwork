from __future__ import annotations

from pathlib import Path

from attachment_contract_spikes.scrub import scan


def test_scrub_accepts_sanitized_text(tmp_path: Path) -> None:
    (tmp_path / "safe.json").write_text('{"actor": "synthetic"}\n', encoding="utf-8")
    report = scan(tmp_path)
    assert report["finding_count"] == 0
    assert report["zero_secrets"] is True


def test_scrub_rejects_secret_endpoint_and_absolute_path(tmp_path: Path) -> None:
    (tmp_path / "unsafe.txt").write_text(
        'api_key="synthetic-secret-value"\n'
        "https://service.example/path?sig=abcdefgh\n"
        "/Users/operator/private.txt\n",
        encoding="utf-8",
    )
    report = scan(tmp_path)
    kinds = {finding["kind"] for finding in report["findings"]}  # type: ignore[index]
    assert {
        "credential-assignment",
        "reusable-endpoint",
        "absolute-user-path",
    } <= kinds
