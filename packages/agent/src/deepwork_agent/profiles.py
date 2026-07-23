"""Bounded, local-only research and writing journey contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

MAX_EVIDENCE_REFERENCES = 12
MAX_PROVENANCE_REFERENCES = 12
MAX_CLAIMS = 24


class JourneyProfile(StrEnum):
    """The deliberately small set of supported non-coding journeys."""

    RESEARCH = "research"
    WRITING = "writing"


class ClaimKind(StrEnum):
    """How a statement in the artifact should be interpreted."""

    EVIDENCE = "evidence"
    INFERENCE = "inference"
    UNVERIFIED = "unverified"


class BoundedReference(BaseModel):
    """A caller-supplied, local reference; never a fetched hosted artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    reference: str = Field(min_length=1, max_length=500)
    provenance: str = Field(min_length=1, max_length=500)


class ArtifactClaim(BaseModel):
    """A classified statement rather than an implied truth assertion."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    kind: ClaimKind
    text: str = Field(min_length=1, max_length=2_000)
    reference_indexes: tuple[int, ...] = Field(default=(), max_length=MAX_EVIDENCE_REFERENCES)


class FinalArtifact(BaseModel):
    """Portable local result with bounded evidence and provenance links."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    profile: JourneyProfile
    body: str = Field(min_length=1, max_length=20_000)
    claims: tuple[ArtifactClaim, ...] = Field(max_length=MAX_CLAIMS)
    evidence: tuple[BoundedReference, ...] = Field(max_length=MAX_EVIDENCE_REFERENCES)
    provenance: tuple[BoundedReference, ...] = Field(max_length=MAX_PROVENANCE_REFERENCES)
    hosted_artifact: str = "unavailable"


PROFILE_PROMPTS: dict[JourneyProfile, str] = {
    JourneyProfile.RESEARCH: (
        "You are the Deep Work research profile. State evidence, inference, and "
        "unverified claims separately. Do not claim that supplied references were fetched "
        "or verified unless the transcript proves it."
    ),
    JourneyProfile.WRITING: (
        "You are the Deep Work writing profile. Produce a clear bounded draft and label "
        "evidence, inference, and unverified claims rather than presenting assumptions as fact."
    ),
}


PROFILE_RUBRICS: dict[JourneyProfile, str] = {
    JourneyProfile.RESEARCH: (
        "Required criteria: (1) distinguish evidence, inference, and unverified claims; "
        "(2) do not invent provenance; (3) produce a concise research artifact."
    ),
    JourneyProfile.WRITING: (
        "Required criteria: (1) provide a coherent draft; (2) distinguish evidence, "
        "inference, and unverified claims; (3) do not invent provenance."
    ),
}
