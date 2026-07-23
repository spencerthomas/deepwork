"""Explicitly enabled acceptance against a real loopback Agent Server."""

from __future__ import annotations

import asyncio
import os

import pytest

from deepwork_api.adapters.sources.local import (
    LocalAgentServerSource,
    LocalSourceStaleInterruptError,
)

_URL_ENV = "DEEPWORK_TEST_LOCAL_AGENT_SERVER_URL"
_ASSISTANT_ENV = "DEEPWORK_TEST_LOCAL_AGENT_SERVER_ASSISTANT"


async def test_explicit_loopback_agent_server_round_trip() -> None:
    """Prove official client, stream, interrupt, and safe reject when configured."""

    endpoint = os.environ.get(_URL_ENV)
    assistant_id = os.environ.get(_ASSISTANT_ENV)
    if not endpoint or not assistant_id:
        pytest.skip(f"set {_URL_ENV} and {_ASSISTANT_ENV} to run loopback acceptance")

    source = LocalAgentServerSource.from_official_sdk(
        endpoint=endpoint,
        assistant_id=assistant_id,
    )
    try:
        status = await source.status()
        assert status.available is True
        assert status.code == "ready"

        initial_run = await source.start("Prepare a two-step local plan, then wait for review.")
        async with asyncio.timeout(60):
            initial_events = [event async for event in source.stream(initial_run)]
        assert initial_events

        paused = await source.get_state(initial_run.thread_id)
        assert paused.interrupt is not None
        assert paused.interrupt.plan
        assert "reject" in paused.interrupt.allowed_decisions

        edited_steps = ["Inspect only supplied inputs.", "Return a concise result."]
        edited = await source.update_plan(
            initial_run.thread_id,
            interrupt_id=paused.interrupt.interrupt_id,
            expected_revision=paused.interrupt.plan_revision,
            steps=edited_steps,
        )
        assert edited.interrupt_id != paused.interrupt.interrupt_id
        assert edited.plan_revision == paused.interrupt.plan_revision + 1

        updated = await source.get_state(initial_run.thread_id)
        assert updated.interrupt is not None
        assert updated.interrupt.interrupt_id == edited.interrupt_id
        assert list(updated.interrupt.plan) == edited_steps
        with pytest.raises(LocalSourceStaleInterruptError):
            await source.resume(
                initial_run.thread_id,
                interrupt_id=paused.interrupt.interrupt_id,
                decision="reject",
            )

        rejected_run = await source.resume(
            initial_run.thread_id,
            interrupt_id=edited.interrupt_id,
            decision="reject",
        )
        async with asyncio.timeout(60):
            rejected_events = [event async for event in source.stream(rejected_run)]
        assert rejected_events

        rejected = await source.get_state(initial_run.thread_id)
        assert rejected.status == "rejected"
        assert rejected.interrupt is None
    finally:
        await source.close()
