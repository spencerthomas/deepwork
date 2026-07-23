"""Use case depending inward on a port."""

from deepwork_api.ports.work import WorkRepository


def exists(repository: WorkRepository, identifier: str) -> bool:
    return repository.get(identifier) is not None
