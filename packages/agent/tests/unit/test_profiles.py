"""Tests for portable, evidence-conscious journey artifacts."""

import pytest
from pydantic import ValidationError

from deepwork_agent import (
    ArtifactClaim,
    BoundedReference,
    ClaimKind,
    FinalArtifact,
    JourneyProfile,
    runtime_capabilities,
)


def test_final_artifact_classifies_claims_and_bounds_references() -> None:
    """Artifacts retain explicit epistemic labels rather than implied truth."""
    reference = BoundedReference(reference="note-1", provenance="caller supplied")
    artifact = FinalArtifact(
        profile=JourneyProfile.RESEARCH,
        body="A bounded research note.",
        claims=(ArtifactClaim(kind=ClaimKind.EVIDENCE, text="The note says X."),),
        evidence=(reference,),
        provenance=(reference,),
    )

    assert artifact.claims[0].kind == ClaimKind.EVIDENCE
    assert artifact.hosted_artifact == "unavailable"


def test_artifact_rejects_unbounded_reference_lists() -> None:
    """The package cannot turn a final artifact into an unbounded evidence store."""
    reference = BoundedReference(reference="note", provenance="caller")
    with pytest.raises(ValidationError, match="at most 12 items"):
        FinalArtifact(
            profile=JourneyProfile.WRITING,
            body="Draft.",
            claims=(),
            evidence=tuple(reference for _ in range(13)),
            provenance=(),
        )


def test_unverified_hosted_artifacts_and_subagents_remain_unavailable() -> None:
    """No capability claim is made without a verified installed contract."""
    capabilities = runtime_capabilities()

    assert capabilities.hosted_artifacts == "unavailable"
    assert capabilities.synchronous_subagents == "unavailable"
