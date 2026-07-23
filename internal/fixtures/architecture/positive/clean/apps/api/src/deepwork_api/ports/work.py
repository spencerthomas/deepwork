"""Port expressed in terms of the domain."""

from typing import Protocol

from deepwork_api.domain.work import Work


class WorkRepository(Protocol):
    def get(self, identifier: str) -> Work | None: ...
