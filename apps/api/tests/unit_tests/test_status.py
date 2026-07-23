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
