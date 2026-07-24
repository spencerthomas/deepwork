"""Contract tests for login and guarded task routes over HTTP."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest
from fastapi import FastAPI

from deepwork_api import create_app

ACCESS_KEY = "s3cret-operator-key"


@asynccontextmanager
async def _app(**kwargs: object) -> AsyncIterator[httpx.AsyncClient]:
    app: FastAPI = create_app(**kwargs)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        # https base URL so the Secure session cookie is sent back by the client.
        async with httpx.AsyncClient(transport=transport, base_url="https://auth.test") as client:
            yield client


async def test_no_access_key_leaves_tasks_open() -> None:
    async with _app() as client:
        # Fixture mode with no access key: task routes stay open, no auth routes.
        assert (await client.get("/api/v1/tasks")).status_code == 200
        assert (await client.post("/api/v1/auth/login", json={"accessKey": "x"})).status_code == 404


async def test_tasks_require_a_session_when_auth_enabled() -> None:
    async with _app(access_key=ACCESS_KEY) as client:
        unauth = await client.get("/api/v1/tasks")
        assert unauth.status_code == 401
        assert unauth.json() == {"code": "unauthorized", "message": "Authentication required."}


async def test_login_then_access_tasks_with_bearer_and_cookie() -> None:
    async with _app(access_key=ACCESS_KEY) as client:
        bad = await client.post("/api/v1/auth/login", json={"accessKey": "wrong"})
        assert bad.status_code == 401
        assert bad.json()["code"] == "unauthorized"

        ok = await client.post("/api/v1/auth/login", json={"accessKey": ACCESS_KEY})
        assert ok.status_code == 200
        body = ok.json()
        token = body["token"]
        assert body["actorId"] == "operator"
        assert "deepwork_session" in ok.headers.get("set-cookie", "")

        # Bearer token works.
        with_bearer = await client.get(
            "/api/v1/tasks", headers={"Authorization": f"Bearer {token}"}
        )
        assert with_bearer.status_code == 200

        # The cookie set by login also authorizes (httpx keeps it on the client).
        with_cookie = await client.get("/api/v1/tasks")
        assert with_cookie.status_code == 200

        # /session reports the current actor.
        session = await client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {token}"})
        assert session.status_code == 200
        whoami = await client.get(
            "/api/v1/auth/session", headers={"Authorization": f"Bearer {token}"}
        )
        assert whoami.status_code == 200
        assert whoami.json()["actorId"] == "operator"


async def test_logout_revokes_the_session() -> None:
    async with _app(access_key=ACCESS_KEY) as client:
        token = (await client.post("/api/v1/auth/login", json={"accessKey": ACCESS_KEY})).json()[
            "token"
        ]
        auth_header = {"Authorization": f"Bearer {token}"}
        assert (await client.get("/api/v1/tasks", headers=auth_header)).status_code == 200
        assert (await client.post("/api/v1/auth/logout", headers=auth_header)).status_code == 200
        assert (await client.get("/api/v1/tasks", headers=auth_header)).status_code == 401


async def test_access_key_never_appears_in_the_schema() -> None:
    import json

    app = create_app(access_key=ACCESS_KEY)
    assert ACCESS_KEY not in json.dumps(app.openapi())
    # Auth routes are present when enabled.
    assert "/api/v1/auth/login" in app.openapi()["paths"]
