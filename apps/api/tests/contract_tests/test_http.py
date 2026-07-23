"""Contract tests for fixture-only HTTP behavior."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx

from deepwork_api import create_app


@asynccontextmanager
async def _client() -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://fixture.test") as client:
        yield client


async def test_health_is_process_only() -> None:
    async with _client() as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "alive",
        "scope": "process",
        "evidence_class": "fixture",
        "dependencies_checked": [],
    }


async def test_demo_status_cannot_imply_live_capability() -> None:
    async with _client() as client:
        response = await client.get("/api/v1/demo/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "fixture"
    assert payload["evidence_class"] == "fixture"
    assert {item["state"] for item in payload["capabilities"]} == {"unavailable"}
    assert "unavailable" in payload["safe_reason"]


def _field_names(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_field_names(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_field_names(item) for item in value), set())
    return set()


def test_openapi_has_no_secret_or_proxy_shape() -> None:
    schema = create_app().openapi()
    field_names = {name.casefold() for name in _field_names(schema)}
    forbidden_fields = {
        "authref",
        "authorization",
        "credential",
        "endpoint",
        "forwarded",
        "provider_cursor",
        "token",
    }
    assert field_names.isdisjoint(forbidden_fields)
    serialized = json.dumps(schema)
    assert "/v1/deepagents" not in serialized
