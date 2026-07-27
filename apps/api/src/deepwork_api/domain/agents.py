"""Pure bounds and errors for the source-backed agent registry.

Deep Work does not own agent storage: an "agent" is a LangGraph Assistant
already registered on the configured task source (a hosted classic
deployment or the local Agent Server), sharing the one deployed graph. This
module holds only the shared bounds and the safe errors the transport
boundary maps, so the application layer never invents a local copy of
source-owned truth.
"""

from __future__ import annotations

MAX_AGENT_NAME_LENGTH = 80
MAX_AGENT_DESCRIPTION_LENGTH = 300


class AgentDomainError(Exception):
    """Base error mapped safely at the transport boundary."""


class AgentRegistryUnavailableError(AgentDomainError):
    """No real task source is configured, so there is no agent registry.

    Fixture mode makes no provider calls and owns no agent storage of its
    own, so this reports an honest unavailable state instead of a fabricated
    empty or default agent list.
    """


class DefaultAgentImmutableError(AgentDomainError):
    """The default agent bound to the deployed graph cannot be edited or deleted.

    It is the fallback used whenever no agent is explicitly selected for a
    task, and its persona is governed by the existing workspace system
    prompt setting rather than its own stored config, so editing it here
    would create two conflicting sources of truth for the same behavior.
    """
