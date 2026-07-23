from __future__ import annotations

import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest

from coding_review_surface_spikes.contracts import (
    exact_diff_errors,
    fixture_manifest_errors,
    normalize_relative_path,
    validate_browser_mode,
    validate_matrix_document,
    validate_scope_document,
    validate_terminal_pair,
    validate_upstream_lock,
)
from coding_review_surface_spikes.fake_adapters import (
    FakeFileAdapter,
    FileSnapshot,
    bounded_safe_text,
    sanitize_transcript,
)
from coding_review_surface_spikes.scrub import scan

ROOT = Path(__file__).parents[4]
EVIDENCE = ROOT / "docs/references/research/coding-review-surfaces-contracts"


def load(name: str) -> dict[str, object]:
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def test_offline_suite_denies_network() -> None:
    with pytest.raises(RuntimeError, match="network denied"):
        socket.create_connection(("synthetic.invalid", 443))


@pytest.mark.parametrize(
    "path",
    [
        "/outside",
        "../outside",
        "safe/../../outside",
        "bad\x00name",
        "C:\\outside",
        "safe\\outside",
        "./same",
    ],
)
def test_path_policy_rejects_escape_and_ambiguity(path: str) -> None:
    with pytest.raises(ValueError):
        normalize_relative_path(path)


def test_path_policy_accepts_normalized_relative_path() -> None:
    assert normalize_relative_path("nested/a/file.txt") == "nested/a/file.txt"


def test_fake_listing_is_stable_and_paged() -> None:
    files = {
        name: FileSnapshot(name, "v1", name.encode())
        for name in ("z.txt", "a.txt", "nested/b.txt")
    }
    adapter = FakeFileAdapter(files)
    first = adapter.list_page(cursor=0, limit=2)
    second = adapter.list_page(cursor=first["next_cursor"], limit=2)
    assert [item["path"] for item in first["items"]] == ["a.txt", "nested/b.txt"]
    assert [item["path"] for item in second["items"]] == ["z.txt"]
    assert second["next_cursor"] is None


def test_fake_read_detects_changed_version_without_mixing_bytes() -> None:
    first = FileSnapshot("README.txt", "version-a", b"alpha")
    adapter = FakeFileAdapter({"README.txt": first})
    metadata_checksum = first.checksum
    adapter.replace("README.txt", FileSnapshot("README.txt", "version-b", b"beta"))
    with pytest.raises(RuntimeError, match="stale_file_version"):
        adapter.read("README.txt", expected_version="version-a")
    assert metadata_checksum != adapter.read("README.txt", expected_version="version-b").checksum


def test_fake_adapter_never_follows_symlink() -> None:
    adapter = FakeFileAdapter(
        {"safe.txt": FileSnapshot("safe.txt", "v1", b"safe")},
        symlinks={"link-out": "../outside"},
    )
    with pytest.raises(ValueError, match="never followed"):
        adapter.read("link-out", expected_version="v1")


def test_content_bounds_precede_decode() -> None:
    result = bounded_safe_text(b"x" * 20, maximum_bytes=8)
    assert result == {
        "mode": "metadata_only",
        "truncated": True,
        "total_bytes": 20,
        "returned_bytes": 0,
    }
    binary = bounded_safe_text(b"\xff\xfe", maximum_bytes=8)
    assert binary["mode"] == "metadata_only"


def test_terminal_sanitizer_removes_control_and_active_link_sequences() -> None:
    payload = "\x1b[31mred\x1b[0m \x1b]8;;https://synthetic.invalid\x07label\x1b]8;;\x07"
    result = sanitize_transcript(payload, maximum_characters=32)
    assert result["rendering"] == "escaped_plain_text"
    assert result["active_links"] == 0
    assert "\x1b" not in result["text"]


def test_terminal_sanitizer_reports_exact_truncation() -> None:
    result = sanitize_transcript("0123456789", maximum_characters=4)
    assert result["truncated"] is True
    assert result["returned_characters"] == 4
    assert result["omitted_characters"] == 6


@pytest.mark.parametrize(
    ("terminal", "command_input"),
    [("interactive", "pty"), ("transcript", "discrete_reviewed"), ("transcript", "none"), ("none", "none")],
)
def test_canonical_terminal_pairs(terminal: str, command_input: str) -> None:
    validate_terminal_pair(terminal, command_input)


@pytest.mark.parametrize(
    ("terminal", "command_input"),
    [("interactive", "none"), ("transcript", "pty"), ("none", "discrete_reviewed")],
)
def test_noncanonical_terminal_pairs_fail(terminal: str, command_input: str) -> None:
    with pytest.raises(ValueError):
        validate_terminal_pair(terminal, command_input)


def test_external_link_is_not_browser_evidence() -> None:
    validate_browser_mode("none", {"kind": "external_link"})
    with pytest.raises(ValueError, match="verified evidence provenance"):
        validate_browser_mode("evidence", {"kind": "external_link"})
    with pytest.raises(ValueError, match="authorized expiring binding"):
        validate_browser_mode("service_url", {"kind": "external_link"})


def test_scope_and_upstream_hashes_are_exact() -> None:
    assert validate_scope_document(load("matrix-scope.json")) == []
    assert validate_upstream_lock(load("upstream-lock.json")) == []


def test_matrix_cross_product_and_blockers_are_complete() -> None:
    matrix = load("matrix.json")
    scope = load("matrix-scope.json")
    upstream = load("upstream-lock.json")
    assert validate_matrix_document(matrix, scope, upstream) == []
    assert all(row["conclusion"] != "accepted-live" for row in matrix["rows"])
    assert all(item["e2e_credit"] == 0 for item in matrix["spike_dispositions"].values())


def test_matrix_rejects_fake_live_promotion() -> None:
    matrix = load("matrix.json")
    scope = load("matrix-scope.json")
    upstream = load("upstream-lock.json")
    invalid = deepcopy(matrix)
    invalid["rows"][0]["conclusion"] = "accepted-live"
    assert any("accepted-live requires accepted-live evidence" in item for item in validate_matrix_document(invalid, scope, upstream))


def test_matrix_rejects_transcript_labelled_pty() -> None:
    matrix = load("matrix.json")
    scope = load("matrix-scope.json")
    upstream = load("upstream-lock.json")
    invalid = deepcopy(matrix)
    terminal = next(row for row in invalid["rows"] if row["row_id"] == "TERMINAL-TRANSCRIPT-001")
    terminal["command_input"] = "pty"
    assert any("transcript cannot claim pty" in item for item in validate_matrix_document(invalid, scope, upstream))


def test_exact_diff_bytes_and_document_hash_match() -> None:
    document = load("fixtures/exact-diff.json")
    patch = (EVIDENCE / "fixtures/exact-review.patch").read_bytes()
    assert exact_diff_errors(document, patch) == []
    statuses = {item["status"] for item in document["files"]}
    assert statuses == {"added", "modified", "deleted", "renamed"}
    binary = next(item for item in document["files"] if item["binary"])
    assert binary["hunks"] == []


def test_stale_head_fixture_blocks_mutation() -> None:
    race = load("fixtures/mutation-races.json")["diff_anchor"]
    assert race["reviewed_head_sha"] != race["current_head_sha"]
    assert race["expected"] == "mutation-blocked-remap-required"


def test_terminal_disconnect_does_not_claim_stopped() -> None:
    transcript = load("fixtures/terminal-transcript.json")
    assert transcript["reconnect"]["process_state"] == "unknown"


def test_browser_none_retains_no_placeholder() -> None:
    browser = load("fixtures/browser-modes.json")
    assert browser["placeholder_screenshot"] is None
    assert browser["model_authored_timeline"] is None
    assert browser["external_link"]["browser_capability"] == "none"
    assert browser["external_link"]["auto_open"] is False


def test_fixture_manifest_hashes_match() -> None:
    manifest = load("fixtures/manifest.json")
    assert fixture_manifest_errors(EVIDENCE / "fixtures", manifest) == []


def test_schemas_are_parseable_and_closed() -> None:
    for path in sorted((EVIDENCE / "schemas").glob("*.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        assert schema["$schema"].endswith("2020-12/schema")
        assert schema["additionalProperties"] is False


def test_retained_evidence_scrubs_clean() -> None:
    report = scan(EVIDENCE)
    assert report["findings"] == []


def _require_live_option(request: pytest.FixtureRequest, option: str) -> str:
    value = request.config.getoption(option)
    if not value:
        raise RuntimeError(f"required live option missing: {option}")
    return value


@pytest.mark.live_contract
def test_live_contract_fails_closed_without_accepted_upstreams(request: pytest.FixtureRequest) -> None:
    _require_live_option(request, "--live-profile")
    _require_live_option(request, "--read-grant")
    upstream = load("upstream-lock.json")
    assert all(item["review_verdict"] == "accepted" for item in upstream["dependencies"])
    pytest.fail("live adapter intentionally absent until both upstream packets and current permission are accepted")


@pytest.mark.live_contract
@pytest.mark.terminal_live_contract
def test_terminal_live_contract_requires_separate_grant(request: pytest.FixtureRequest) -> None:
    _require_live_option(request, "--live-profile")
    _require_live_option(request, "--read-grant")
    _require_live_option(request, "--terminal-grant")
    pytest.fail("terminal live adapter intentionally absent until exact public input and cleanup contracts are accepted")
