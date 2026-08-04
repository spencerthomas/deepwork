"""Unit tests for fixture and configured-source status behavior."""

import pytest

from deepwork_api.adapters.fixture import FixtureStatusProvider
from deepwork_api.adapters.sources.status import SourceStatusProvider
from deepwork_api.application import StatusService
from deepwork_api.domain import (
    CapabilityState,
    EvidenceClass,
    JobDurability,
    RuntimeKind,
    WorkerDurability,
)


def test_fixture_status_is_explicitly_unavailable() -> None:
    service = StatusService(provider=FixtureStatusProvider())

    demo = service.demo()

    assert demo.mode is EvidenceClass.FIXTURE
    assert demo.runtime_kind is RuntimeKind.FIXTURE
    assert {capability.name for capability in demo.capabilities} == {
        "authentication",
        "durable_jobs",
        "external_providers",
        "local_task_loop",
        "sources",
        "task_stream",
    }
    states = {capability.name: capability.state for capability in demo.capabilities}
    assert states["local_task_loop"] is CapabilityState.AVAILABLE
    assert states["task_stream"] is CapabilityState.AVAILABLE
    assert states["external_providers"] is CapabilityState.UNAVAILABLE
    assert service.worker().durability is WorkerDurability.UNAVAILABLE


def test_runtime_status_reports_the_composed_build_identity() -> None:
    service = StatusService(provider=FixtureStatusProvider(), build_sha="abc1234")

    assert service.demo().build_sha == "abc1234"


def test_classic_status_identifies_the_configured_runtime_without_claiming_health() -> None:
    service = StatusService(
        provider=SourceStatusProvider(
            runtime_kind=RuntimeKind.CLASSIC_DEPLOYMENT,
            authentication_enabled=True,
        )
    )

    demo = service.demo()

    assert demo.mode is EvidenceClass.LOCAL_SOURCE
    assert demo.runtime_kind is RuntimeKind.CLASSIC_DEPLOYMENT
    states = {capability.name: capability.state for capability in demo.capabilities}
    assert states["local_task_loop"] is CapabilityState.AVAILABLE
    assert states["task_stream"] is CapabilityState.AVAILABLE
    assert states["authentication"] is CapabilityState.AVAILABLE
    assert states["sources"] is CapabilityState.AVAILABLE
    assert states["external_providers"] is CapabilityState.AVAILABLE
    assert states["durable_jobs"] is CapabilityState.UNAVAILABLE
    assert "readiness" in demo.safe_reason
    assert service.health().evidence_class is EvidenceClass.LOCAL_SOURCE


def test_source_status_rejects_the_fixture_runtime_kind() -> None:
    with pytest.raises(ValueError, match="source-backed runtime kind"):
        SourceStatusProvider(
            runtime_kind=RuntimeKind.FIXTURE,
            authentication_enabled=False,
        )


def test_postgres_outbox_upgrades_only_the_durable_job_capability() -> None:
    service = StatusService(
        provider=FixtureStatusProvider(authentication_enabled=True),
        job_durability=JobDurability.POSTGRES_OUTBOX,
    )

    demo = service.demo()
    states = {capability.name: capability.state for capability in demo.capabilities}
    assert states["durable_jobs"] is CapabilityState.AVAILABLE
    assert states["authentication"] is CapabilityState.AVAILABLE
    assert states["external_providers"] is CapabilityState.UNAVAILABLE
    assert "PostgreSQL transactional job/outbox" in demo.safe_reason
