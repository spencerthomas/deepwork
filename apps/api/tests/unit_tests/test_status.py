"""Unit tests for fixture status behavior."""

from deepwork_api.adapters.fixture import FixtureStatusProvider
from deepwork_api.application import StatusService
from deepwork_api.domain import CapabilityState, EvidenceClass, WorkerDurability


def test_fixture_status_is_explicitly_unavailable() -> None:
    service = StatusService(provider=FixtureStatusProvider())

    demo = service.demo()

    assert demo.mode is EvidenceClass.FIXTURE
    assert {capability.name for capability in demo.capabilities} == {
        "authentication",
        "durable_jobs",
        "sources",
        "task_stream",
    }
    assert all(capability.state is CapabilityState.UNAVAILABLE for capability in demo.capabilities)
    assert service.worker().durability is WorkerDurability.UNAVAILABLE
