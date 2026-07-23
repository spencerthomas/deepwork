"""Structured journey artifacts with bounded evidence and provenance references.

The executor declares exactly one structured artifact per run through the public
Deep Agents ``response_format`` contract. This module owns the declaration
schema, the normalized artifact record, and fail-closed validation. Claims are
explicitly labeled ``evidence``, ``inference``, or ``unverified``; a citation is
provenance coverage, never a truth claim. Unsupported citations are flagged and
downgraded rather than fabricated or silently passed through.
"""

from __future__ import annotations

from typing import Literal, NotRequired, cast

from typing_extensions import TypedDict

ArtifactKind = Literal["report", "document"]
ClaimBasis = Literal["evidence", "inference", "unverified"]

MAX_ARTIFACT_TITLE_LENGTH = 200
MAX_ARTIFACT_SUMMARY_LENGTH = 2_000
MAX_ARTIFACT_BODY_LENGTH = 20_000
MAX_ARTIFACT_CLAIMS = 50
MAX_CLAIM_TEXT_LENGTH = 1_000
MAX_EVIDENCE_REFERENCES = 25
MAX_EVIDENCE_FIELD_LENGTH = 500
MAX_UNRESOLVED_ITEMS = 25
MAX_UNRESOLVED_TEXT_LENGTH = 500
_CLAIM_BASES: tuple[ClaimBasis, ...] = ("evidence", "inference", "unverified")
_ARTIFACT_KINDS: tuple[ArtifactKind, ...] = ("report", "document")


class EvidenceDraft(TypedDict):
    """One evidence reference as declared by the executor."""

    evidence_id: str
    """Short identifier claims cite through ``evidence_ids``."""

    source_title: str
    """Human-readable source name exactly as a tool or input supplied it."""

    locator: str
    """URL, file path, or citation locator exactly as supplied; never invented."""

    observed_at: NotRequired[str]
    """Access time as supplied by the tool, empty when unknown."""


class ClaimDraft(TypedDict):
    """One claim as declared by the executor, labeled by its basis."""

    text: str
    """The claim itself."""

    basis: ClaimBasis
    """``evidence`` (cited), ``inference`` (reasoned), or ``unverified``."""

    evidence_ids: NotRequired[list[str]]
    """Evidence references supporting the claim; required for ``evidence``."""


class JourneyArtifactDraft(TypedDict):
    """Structured final artifact the executor must declare.

    This TypedDict is passed as the public ``response_format`` of the pinned
    Deep Agents executor, so the model declares the artifact through a
    verified structured-output contract instead of free text.
    """

    title: str
    """Artifact title."""

    summary: str
    """Short reviewer-facing summary; may be empty."""

    body: str
    """Full report or document text."""

    claims: list[ClaimDraft]
    """Every substantive claim, labeled evidence, inference, or unverified."""

    evidence: list[EvidenceDraft]
    """Bounded provenance references gathered during the run."""

    unresolved: list[str]
    """Open questions or claims the run could not resolve."""


class ArtifactClaim(TypedDict):
    """Normalized claim with a validated basis label."""

    text: str
    basis: ClaimBasis
    evidence_ids: list[str]


class EvidenceReference(TypedDict):
    """Normalized bounded provenance reference."""

    evidence_id: str
    source_title: str
    locator: str
    observed_at: str


class JourneyArtifact(TypedDict):
    """Validated final artifact record for one journey run.

    ``citation_flags`` records every citation the validator could not support
    (unknown or missing evidence references); the affected claims are
    downgraded to ``unverified`` rather than passed through as cited.
    """

    kind: ArtifactKind
    title: str
    summary: str
    body: str
    claims: list[ArtifactClaim]
    evidence: list[EvidenceReference]
    unresolved: list[str]
    citation_flags: list[str]
    version: int
    trust: Literal["untrusted"]


def _require_text(
    value: object,
    *,
    field: str,
    max_length: int,
    allow_empty: bool = False,
) -> str:
    """Return bounded stripped text or fail closed with the field name."""
    if not isinstance(value, str):
        msg = f"artifact {field} must be text"
        raise TypeError(msg)
    text = value.strip()
    if not text and not allow_empty:
        msg = f"artifact {field} must contain non-whitespace text"
        raise ValueError(msg)
    if len(text) > max_length:
        msg = f"artifact {field} must contain at most {max_length} characters"
        raise ValueError(msg)
    return text


def _require_list(value: object, *, field: str, max_items: int) -> list[object]:
    """Return a bounded list or fail closed with the field name."""
    if not isinstance(value, list):
        msg = f"artifact {field} must be a list"
        raise TypeError(msg)
    if len(value) > max_items:
        msg = f"artifact {field} must contain at most {max_items} items"
        raise ValueError(msg)
    return list(value)


def _validate_evidence(value: object) -> list[EvidenceReference]:
    """Validate bounded evidence references with unique identifiers."""
    entries = _require_list(value, field="evidence", max_items=MAX_EVIDENCE_REFERENCES)
    references: list[EvidenceReference] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            msg = f"artifact evidence[{index}] must be a mapping"
            raise TypeError(msg)
        evidence_id = _require_text(
            entry.get("evidence_id"),
            field=f"evidence[{index}].evidence_id",
            max_length=MAX_EVIDENCE_FIELD_LENGTH,
        )
        if evidence_id in seen:
            msg = f"artifact evidence contains duplicate identifier {evidence_id!r}"
            raise ValueError(msg)
        seen.add(evidence_id)
        references.append(
            {
                "evidence_id": evidence_id,
                "source_title": _require_text(
                    entry.get("source_title"),
                    field=f"evidence[{index}].source_title",
                    max_length=MAX_EVIDENCE_FIELD_LENGTH,
                ),
                "locator": _require_text(
                    entry.get("locator"),
                    field=f"evidence[{index}].locator",
                    max_length=MAX_EVIDENCE_FIELD_LENGTH,
                ),
                "observed_at": _require_text(
                    entry.get("observed_at", ""),
                    field=f"evidence[{index}].observed_at",
                    max_length=MAX_EVIDENCE_FIELD_LENGTH,
                    allow_empty=True,
                ),
            }
        )
    return references


def _validate_claim_citations(
    *,
    index: int,
    basis: ClaimBasis,
    cited: list[str],
    known_evidence: set[str],
    flags: list[str],
) -> tuple[ClaimBasis, list[str]]:
    """Keep supported citations and downgrade unsupported evidence claims."""
    supported = [evidence_id for evidence_id in cited if evidence_id in known_evidence]
    flags.extend(
        f"claim[{index}] cites unknown evidence reference {evidence_id!r}"
        for evidence_id in cited
        if evidence_id not in known_evidence
    )
    if basis == "evidence" and not supported:
        flags.append(
            f"claim[{index}] was labeled evidence without a supported citation; "
            "downgraded to unverified"
        )
        return "unverified", supported
    return basis, supported


def _validate_claims(
    value: object,
    *,
    known_evidence: set[str],
    flags: list[str],
) -> list[ArtifactClaim]:
    """Validate bounded labeled claims against declared evidence."""
    entries = _require_list(value, field="claims", max_items=MAX_ARTIFACT_CLAIMS)
    claims: list[ArtifactClaim] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            msg = f"artifact claims[{index}] must be a mapping"
            raise TypeError(msg)
        text = _require_text(
            entry.get("text"),
            field=f"claims[{index}].text",
            max_length=MAX_CLAIM_TEXT_LENGTH,
        )
        raw_basis = entry.get("basis")
        if raw_basis not in _CLAIM_BASES:
            msg = f"artifact claims[{index}].basis must be evidence, inference, or unverified"
            raise ValueError(msg)
        basis = cast("ClaimBasis", raw_basis)
        cited_raw = _require_list(
            entry.get("evidence_ids", []),
            field=f"claims[{index}].evidence_ids",
            max_items=MAX_EVIDENCE_REFERENCES,
        )
        cited = [
            _require_text(
                evidence_id,
                field=f"claims[{index}].evidence_ids[{ref_index}]",
                max_length=MAX_EVIDENCE_FIELD_LENGTH,
            )
            for ref_index, evidence_id in enumerate(cited_raw)
        ]
        final_basis, supported = _validate_claim_citations(
            index=index,
            basis=basis,
            cited=cited,
            known_evidence=known_evidence,
            flags=flags,
        )
        claims.append({"text": text, "basis": final_basis, "evidence_ids": supported})
    return claims


def _validate_unresolved(value: object) -> list[str]:
    """Validate the bounded unresolved-items list."""
    entries = _require_list(value, field="unresolved", max_items=MAX_UNRESOLVED_ITEMS)
    return [
        _require_text(
            entry,
            field=f"unresolved[{index}]",
            max_length=MAX_UNRESOLVED_TEXT_LENGTH,
        )
        for index, entry in enumerate(entries)
    ]


def validate_artifact(value: object, *, kind: ArtifactKind) -> JourneyArtifact:
    """Validate a declared artifact draft into a bounded normalized record.

    Structural violations fail closed with ``TypeError`` or ``ValueError``.
    Citation gaps never fail silently and never fabricate support: the claim is
    downgraded to ``unverified`` and the gap is recorded in ``citation_flags``.

    Args:
        value: The ``structured_response`` declared by the executor.
        kind: The journey's artifact kind, ``report`` or ``document``.

    Returns:
        The validated artifact, always marked ``untrusted``.

    Raises:
        TypeError: If the draft or a nested field has the wrong shape.
        ValueError: If a bound, label, or uniqueness rule is violated.

    """
    if kind not in _ARTIFACT_KINDS:
        msg = "artifact kind must be report or document"
        raise ValueError(msg)
    if not isinstance(value, dict):
        msg = "artifact declaration must be a mapping"
        raise TypeError(msg)
    flags: list[str] = []
    evidence = _validate_evidence(value.get("evidence"))
    known_evidence = {reference["evidence_id"] for reference in evidence}
    claims = _validate_claims(value.get("claims"), known_evidence=known_evidence, flags=flags)
    return {
        "kind": kind,
        "title": _require_text(
            value.get("title"),
            field="title",
            max_length=MAX_ARTIFACT_TITLE_LENGTH,
        ),
        "summary": _require_text(
            value.get("summary", ""),
            field="summary",
            max_length=MAX_ARTIFACT_SUMMARY_LENGTH,
            allow_empty=True,
        ),
        "body": _require_text(
            value.get("body"),
            field="body",
            max_length=MAX_ARTIFACT_BODY_LENGTH,
        ),
        "claims": claims,
        "evidence": evidence,
        "unresolved": _validate_unresolved(value.get("unresolved")),
        "citation_flags": flags,
        "version": 1,
        "trust": "untrusted",
    }
