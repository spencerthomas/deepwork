"""Pure application-domain value."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Work:
    identifier: str
