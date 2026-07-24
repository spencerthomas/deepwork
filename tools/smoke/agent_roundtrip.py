#!/usr/bin/env python3
"""Unfakeable smoke gate: drive the real local agent graph end to end.

Runs the actual :mod:`deepwork_agent` graph through plan -> interrupt ->
decision -> terminal state with the keyless deterministic model. It asserts the
real interrupt contract and both terminal branches. It goes green only when the
real engine turns; it cannot be satisfied by fixture UI state.

Usage (from repo root, with the agent package installed):

    DEEPWORK_AGENT_FAKE=1 python tools/smoke/agent_roundtrip.py

Set ``DEEPWORK_AGENT_MODEL`` (and unset ``DEEPWORK_AGENT_FAKE``) to run the exact
same journey against a real provider model.
"""

from __future__ import annotations

import sys

from langgraph.types import Command

from deepwork_agent.runtime import make_graph


def _fail(message: str) -> None:
    print(f"SMOKE FAIL: {message}")
    raise SystemExit(1)


def main() -> int:
    graph = make_graph()

    # 1) Start a task: the real graph must plan and pause on the real interrupt.
    approve_cfg = {"configurable": {"thread_id": "smoke-approve"}}
    paused = graph.invoke({"task": "Summarize the two supplied inputs."}, approve_cfg)
    interrupts = paused.get("__interrupt__")
    if not interrupts:
        _fail("start did not produce a plan-approval interrupt")
    payload = interrupts[0].value
    if payload.get("kind") != "deepwork-plan-approval" or payload.get("action") != "execute_plan":
        _fail(f"interrupt contract mismatch: {payload!r}")
    if not payload.get("plan") or payload.get("plan_revision") != 1:
        _fail(f"interrupt plan/revision invalid: {payload!r}")
    print(f"OK  plan proposed -> {payload['plan']} (revision {payload['plan_revision']})")

    # 2) Approve: the real deepagents executor must run and complete with a result.
    completed = graph.invoke(Command(resume={"decision": "approve"}), approve_cfg)
    if completed.get("status") != "completed" or not completed.get("final_answer"):
        _fail(f"approve did not reach a completed result: {completed!r}")
    print(f"OK  approved -> completed with result: {completed['final_answer']!r}")

    # 3) Reject on a fresh thread: the run must end honestly rejected, no result claim.
    reject_cfg = {"configurable": {"thread_id": "smoke-reject"}}
    graph.invoke({"task": "Summarize the two supplied inputs."}, reject_cfg)
    rejected = graph.invoke(Command(resume={"decision": "reject"}), reject_cfg)
    if rejected.get("status") != "rejected":
        _fail(f"reject did not reach a rejected state: {rejected!r}")
    print(f"OK  rejected -> status {rejected['status']!r}")

    print("\nSMOKE PASS: the real local agent engine turns end to end.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
