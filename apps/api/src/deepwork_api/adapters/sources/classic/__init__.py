"""Dormant classic LangSmith Deployment source qualification."""

from deepwork_api.adapters.sources.classic.source import (
    LIVE_CONTRACT_CAPABILITIES,
    CapabilityObservation,
    ClassicAssistantProjection,
    ClassicQualification,
    ClassicSourceConfigurationError,
    ClassicSourceSettings,
    ClassicSourceSettingsProjection,
    CredentialResolver,
    QualificationState,
    qualify_classic_sources,
    validate_deployment_endpoint,
)

__all__ = [
    "LIVE_CONTRACT_CAPABILITIES",
    "CapabilityObservation",
    "ClassicAssistantProjection",
    "ClassicQualification",
    "ClassicSourceConfigurationError",
    "ClassicSourceSettings",
    "ClassicSourceSettingsProjection",
    "CredentialResolver",
    "QualificationState",
    "qualify_classic_sources",
    "validate_deployment_endpoint",
]
