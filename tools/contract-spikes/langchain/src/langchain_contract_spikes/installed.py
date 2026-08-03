"""Capture deterministic evidence from the pinned installed HITL packages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import langchain.agents.middleware.human_in_the_loop as hitl_module
from langchain.agents.middleware.human_in_the_loop import HumanInTheLoopMiddleware
from langchain_core.messages import AIMessage
from langgraph_sdk import get_sync_client

from langchain_contract_spikes.pins import installed_distributions


def _decisions() -> list[dict[str, Any]]:
    return [
        {"type": "approve"},
        {
            "type": "edit",
            "edited_action": {
                "name": "write_file",
                "args": {"path": "synthetic/b.txt", "content": "synthetic edited"},
            },
        },
    ]


def _capture_middleware_batch() -> dict[str, Any]:
    captured: list[dict[str, Any]] = []
    def synthetic_interrupt(request: dict[str, Any]) -> dict[str, Any]:
        captured.append(request)
        return {"decisions": _decisions()}

    message = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "write_file",
                "args": {"path": "synthetic/a.txt", "content": "synthetic"},
                "id": "synthetic-call-1",
                "type": "tool_call",
            },
            {
                "name": "write_file",
                "args": {"path": "synthetic/c.txt", "content": "synthetic second"},
                "id": "synthetic-call-2",
                "type": "tool_call",
            },
        ],
    )
    middleware = HumanInTheLoopMiddleware(
        interrupt_on={
            "write_file": {"allowed_decisions": ["approve", "edit", "reject"]}
        }
    )
    with patch.object(hitl_module, "interrupt", synthetic_interrupt):
        result = middleware.after_model({"messages": [message]}, SimpleNamespace())
    if len(captured) != 1 or result is None:
        raise RuntimeError("installed HITL middleware did not produce one ordered interrupt")
    revised = result["messages"][0]
    return {
        "request": captured[0],
        "decisions": _decisions(),
        "revised_tool_calls": revised.tool_calls,
    }


def _capture_terminal_decision(decision: dict[str, Any]) -> dict[str, Any]:
    def synthetic_interrupt(_request: dict[str, Any]) -> dict[str, Any]:
        return {"decisions": [decision]}

    message = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "ask_or_delete",
                "args": {"target": "synthetic"},
                "id": f"synthetic-{decision['type']}",
                "type": "tool_call",
            }
        ],
    )
    middleware = HumanInTheLoopMiddleware(
        interrupt_on={
            "ask_or_delete": {
                "allowed_decisions": ["approve", "edit", "reject", "respond"]
            }
        }
    )
    with patch.object(hitl_module, "interrupt", synthetic_interrupt):
        result = middleware.after_model({"messages": [message]}, SimpleNamespace())
    if result is None or len(result["messages"]) != 2:
        raise RuntimeError(f"installed middleware did not emit a {decision['type']} tool message")
    tool_message = result["messages"][1]
    return {"status": tool_message.status, "content": tool_message.content}


def invalid_decision_length_error() -> str:
    """Return the installed middleware's exact malformed-batch rejection."""
    def synthetic_interrupt(_request: dict[str, Any]) -> dict[str, Any]:
        return {"decisions": [{"type": "approve"}]}

    message = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "write_file",
                "args": {"path": "synthetic/a.txt"},
                "id": "synthetic-length-1",
                "type": "tool_call",
            },
            {
                "name": "write_file",
                "args": {"path": "synthetic/b.txt"},
                "id": "synthetic-length-2",
                "type": "tool_call",
            },
        ],
    )
    middleware = HumanInTheLoopMiddleware(interrupt_on={"write_file": True})
    with patch.object(hitl_module, "interrupt", synthetic_interrupt):
        try:
            middleware.after_model({"messages": [message]}, SimpleNamespace())
        except ValueError as error:
            return str(error)
    raise RuntimeError("installed middleware accepted an incomplete decision vector")


def _synthetic_thread(client: Any):
    thread = client.threads.stream(
        "synthetic-thread",
        assistant_id="synthetic-agent",
    )
    thread.interrupts = [
        {
            "interrupt_id": "synthetic-interrupt-1",
            "namespace": ["synthetic", "plan"],
            "value": {"kind": "synthetic"},
        },
        {
            "interrupt_id": "synthetic-interrupt-2",
            "namespace": ["synthetic", "review"],
            "value": {"kind": "synthetic"},
        },
    ]
    return thread


def _capture_protocol_v3_resume() -> dict[str, Any]:
    commands: list[dict[str, Any]] = []

    def capture(command: str, params: dict[str, Any]) -> dict[str, bool]:
        commands.append({"command": command, "params": params})
        return {"accepted": True}

    with get_sync_client(url="https://synthetic.invalid", api_key=None) as client:
        thread = _synthetic_thread(client)
        thread._send_command = capture
        thread.run.respond(
            {"decisions": _decisions()},
            interrupt_id="synthetic-interrupt-2",
        )
    if len(commands) != 1:
        raise RuntimeError("installed SDK did not dispatch exactly one resume command")
    return commands[0]


def ambiguous_resume_error() -> str:
    """Return the installed SDK's fail-closed multi-interrupt error."""
    with get_sync_client(url="https://synthetic.invalid", api_key=None) as client:
        thread = _synthetic_thread(client)
        try:
            thread.run.respond({"decisions": _decisions()})
        except RuntimeError as error:
            return str(error)
    raise RuntimeError("installed SDK accepted an ambiguous interrupt response")


def capture_installed_contract() -> dict[str, Any]:
    """Capture installed middleware and protocol-v3 command behavior without network I/O."""
    return {
        "schema_version": "1.0",
        "synthetic": True,
        "scrub_attestation": (
            "Contains only locally generated action, interrupt, and decision values; "
            "no request was sent to the synthetic.invalid host."
        ),
        "distributions": installed_distributions(),
        "hitl": _capture_middleware_batch(),
        "decision_outcomes": {
            "reject": _capture_terminal_decision(
                {"type": "reject", "message": "Synthetic rejection"}
            ),
            "respond": _capture_terminal_decision(
                {"type": "respond", "message": "Synthetic answer"}
            ),
        },
        "invalid_decision_length_error": invalid_decision_length_error(),
        "protocol_v3_resume": _capture_protocol_v3_resume(),
        "ambiguous_resume_error": ambiguous_resume_error(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(capture_installed_contract(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote sanitized installed contract to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
