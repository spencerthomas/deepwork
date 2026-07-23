"""Bounded validation tests for structured journey artifacts."""

from __future__ import annotations

from typing import Any

import pytest

from deepwork_agent import validate_artifact


def _draft(**overrides: Any) -> dict[str, Any]:  # noqa: ANN401 - test fixture accepts arbitrary shapes
    draft: dict[str, Any] = {
        "title": "Plan-first agents",
        "summary": "Short summary.",
        "body": "Full body text.",
        "claims": [
            {"text": "Cited claim.", "basis": "evidence", "evidence_ids": ["e1"]},
            {"text": "Reasoned claim.", "basis": "inference"},
            {"text": "Open claim.", "basis": "unverified"},
        ],
        "evidence": [
            {
                "evidence_id": "e1",
                "source_title": "Example source",
                "locator": "https://example.test/a",
                "observed_at": "2026-07-23T00:00:00Z",
            }
        ],
        "unresolved": ["Open claim needs a second source."],
    }
    draft.update(overrides)
    return draft


def test_valid_draft_normalizes_with_untrusted_provenance() -> None:
    """A well-formed declaration keeps every basis label and provenance entry."""
    artifact = validate_artifact(_draft(), kind="report")

    assert artifact["kind"] == "report"
    assert artifact["title"] == "Plan-first agents"
    assert [claim["basis"] for claim in artifact["claims"]] == [
        "evidence",
        "inference",
        "unverified",
    ]
    assert artifact["claims"][0]["evidence_ids"] == ["e1"]
    assert artifact["evidence"][0]["locator"] == "https://example.test/a"
    assert artifact["unresolved"] == ["Open claim needs a second source."]
    assert artifact["citation_flags"] == []
    assert artifact["version"] == 1
    assert artifact["trust"] == "untrusted"


def test_missing_observed_at_stays_empty_rather_than_invented() -> None:
    """Absent access times are recorded as empty text, never fabricated."""
    draft = _draft(evidence=[{"evidence_id": "e1", "source_title": "Source", "locator": "file.md"}])

    artifact = validate_artifact(draft, kind="document")

    assert artifact["evidence"][0]["observed_at"] == ""


def test_unknown_citation_is_flagged_and_claim_downgraded() -> None:
    """An evidence claim citing an undeclared reference cannot stay cited."""
    draft = _draft(
        claims=[{"text": "Cited claim.", "basis": "evidence", "evidence_ids": ["missing"]}]
    )

    artifact = validate_artifact(draft, kind="report")

    assert artifact["claims"][0]["basis"] == "unverified"
    assert artifact["claims"][0]["evidence_ids"] == []
    assert any("missing" in flag for flag in artifact["citation_flags"])
    assert any("downgraded to unverified" in flag for flag in artifact["citation_flags"])


def test_evidence_claim_without_citations_is_downgraded() -> None:
    """The evidence label requires at least one supported citation."""
    draft = _draft(claims=[{"text": "Cited claim.", "basis": "evidence", "evidence_ids": []}])

    artifact = validate_artifact(draft, kind="report")

    assert artifact["claims"][0]["basis"] == "unverified"
    assert artifact["citation_flags"]


def test_inference_claim_keeps_basis_when_reference_is_unknown() -> None:
    """Non-evidence claims lose the bad reference but keep their honest label."""
    draft = _draft(
        claims=[{"text": "Reasoned claim.", "basis": "inference", "evidence_ids": ["nope"]}]
    )

    artifact = validate_artifact(draft, kind="report")

    assert artifact["claims"][0]["basis"] == "inference"
    assert artifact["claims"][0]["evidence_ids"] == []
    assert any("nope" in flag for flag in artifact["citation_flags"])


@pytest.mark.parametrize(
    ("draft", "match"),
    [
        ("not a mapping", "must be a mapping"),
        (_draft(title="   "), "title must contain non-whitespace"),
        (_draft(title="x" * 201), "title must contain at most 200"),
        (_draft(body=""), "body must contain non-whitespace"),
        (_draft(claims="none"), "claims must be a list"),
        (_draft(claims=[{"text": "x", "basis": "fact"}]), "basis must be evidence"),
        (_draft(claims=[["not a mapping"]]), r"claims\[0\] must be a mapping"),
        (
            _draft(claims=[{"text": "c", "basis": "unverified"} for _ in range(51)]),
            "claims must contain at most 50",
        ),
        (
            _draft(
                evidence=[
                    {"evidence_id": "e1", "source_title": "a", "locator": "b"},
                    {"evidence_id": "e1", "source_title": "c", "locator": "d"},
                ]
            ),
            "duplicate identifier",
        ),
        (
            _draft(
                evidence=[
                    {"evidence_id": f"e{index}", "source_title": "a", "locator": "b"}
                    for index in range(26)
                ]
            ),
            "evidence must contain at most 25",
        ),
        (_draft(evidence=["oops"]), r"evidence\[0\] must be a mapping"),
        (_draft(unresolved=[1]), r"unresolved\[0\] must be text"),
        (_draft(unresolved=["x" * 501]), r"unresolved\[0\] must contain at most 500"),
    ],
)
def test_structural_violations_fail_closed(draft: object, match: str) -> None:
    """Malformed declarations raise instead of producing a partial artifact."""
    with pytest.raises((TypeError, ValueError), match=match):
        validate_artifact(draft, kind="report")


def test_unknown_artifact_kind_is_rejected() -> None:
    """Only the supported report and document kinds are accepted."""
    with pytest.raises(ValueError, match="report or document"):
        validate_artifact(_draft(), kind="dataset")  # type: ignore[arg-type]
