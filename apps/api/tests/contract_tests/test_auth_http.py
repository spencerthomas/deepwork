"""Contract tests for login and guarded task routes over HTTP."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from deepwork_api import create_app
from deepwork_api.adapters.auth import InMemorySessionStore
from deepwork_api.application import AuthService
from deepwork_api.domain import DEFAULT_WORKSPACE_ID, SecurityContext
from deepwork_api.transport import build_auth_router

ACCESS_KEY = "s3cret-operator-key"


@asynccontextmanager
async def _app(*, access_key: str | None = None) -> AsyncIterator[httpx.AsyncClient]:
    app: FastAPI = create_app(access_key=access_key)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        # https base URL so the Secure session cookie is sent back by the client.
        async with httpx.AsyncClient(transport=transport, base_url="https://auth.test") as client:
            yield client


@asynccontextmanager
async def _mapped_auth_app(
    access_key_contexts: Mapping[str, SecurityContext],
) -> AsyncIterator[httpx.AsyncClient]:
    app = FastAPI()
    auth = AuthService(
        store=InMemorySessionStore(),
        access_key_contexts=access_key_contexts,
        now=lambda: 1000.0,
        token_factory=lambda: "mapped-token",
    )
    app.include_router(build_auth_router(auth))
    transport = httpx.ASGITransport(app=app)
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


async def test_runtime_status_honors_auth_while_health_stays_public() -> None:
    async with _app(access_key=ACCESS_KEY) as client:
        assert (await client.get("/health")).status_code == 200
        for path in ("/api/v1/runtime/status", "/api/v1/demo/status"):
            unauthenticated = await client.get(path)
            assert unauthenticated.status_code == 401
            assert unauthenticated.json() == {
                "code": "unauthorized",
                "message": "Authentication required.",
            }

        assert (
            await client.post("/api/v1/auth/login", json={"accessKey": ACCESS_KEY})
        ).status_code == 200
        for path in ("/api/v1/runtime/status", "/api/v1/demo/status"):
            authenticated = await client.get(path)
            assert authenticated.status_code == 200
            assert authenticated.json()["runtime_kind"] == "fixture"


async def test_login_returns_only_session_projection_and_supports_cookie_auth() -> None:
    async with _app(access_key=ACCESS_KEY) as client:
        bad = await client.post("/api/v1/auth/login", json={"accessKey": "wrong"})
        assert bad.status_code == 401
        assert bad.json()["code"] == "unauthorized"

        ok = await client.post("/api/v1/auth/login", json={"accessKey": ACCESS_KEY})
        assert ok.status_code == 200
        body = ok.json()
        assert body == {
            "storageScope": body["storageScope"],
            "actorId": "operator",
            "workspaceId": DEFAULT_WORKSPACE_ID,
            "expiresAt": body["expiresAt"],
        }
        assert len(body["storageScope"]) == 64
        assert "tenantId" not in body
        assert "token" not in body
        assert "deepwork_session" in ok.headers.get("set-cookie", "")

        # The cookie set by login also authorizes (httpx keeps it on the client).
        with_cookie = await client.get("/api/v1/tasks")
        assert with_cookie.status_code == 200

        # /session reports the current actor.
        whoami = await client.get("/api/v1/auth/session")
        assert whoami.status_code == 200
        assert whoami.json()["actorId"] == "operator"
        assert whoami.json()["workspaceId"] == DEFAULT_WORKSPACE_ID
        assert whoami.json()["storageScope"] == body["storageScope"]
        assert "tenantId" not in whoami.json()


async def test_mapped_access_keys_project_only_their_actor_and_workspace() -> None:
    contexts = {
        "key-a": SecurityContext("tenant-secret-a", "workspace-a", "actor-a"),
        "key-b": SecurityContext("tenant-secret-b", "workspace-b", "actor-b"),
    }

    async with _mapped_auth_app(contexts) as client:
        response = await client.post("/api/v1/auth/login", json={"accessKey": "key-b"})

        assert response.status_code == 200
        assert response.json() == {
            "storageScope": response.json()["storageScope"],
            "actorId": "actor-b",
            "workspaceId": "workspace-b",
            "expiresAt": 44200.0,
        }
        assert len(response.json()["storageScope"]) == 64
        serialized = response.text
        assert "tenant-secret-a" not in serialized
        assert "tenant-secret-b" not in serialized
        assert "key-a" not in serialized
        assert "key-b" not in serialized

        session = await client.get("/api/v1/auth/session")
        assert session.json() == response.json()


async def test_storage_scope_changes_when_only_the_tenant_changes() -> None:
    contexts = {
        "key-a": SecurityContext("tenant-secret-a", "workspace-shared", "actor-shared"),
        "key-b": SecurityContext("tenant-secret-b", "workspace-shared", "actor-shared"),
    }

    async with _mapped_auth_app(contexts) as client:
        first = await client.post("/api/v1/auth/login", json={"accessKey": "key-a"})
        second = await client.post("/api/v1/auth/login", json={"accessKey": "key-b"})

    assert first.json()["actorId"] == second.json()["actorId"]
    assert first.json()["workspaceId"] == second.json()["workspaceId"]
    assert first.json()["storageScope"] != second.json()["storageScope"]
    assert "tenant-secret" not in first.text + second.text


async def test_logout_revokes_the_session() -> None:
    async with _app(access_key=ACCESS_KEY) as client:
        await client.post("/api/v1/auth/login", json={"accessKey": ACCESS_KEY})
        assert (await client.get("/api/v1/tasks")).status_code == 200
        assert (await client.post("/api/v1/auth/logout")).status_code == 200
        assert (await client.get("/api/v1/tasks")).status_code == 401


async def test_access_key_never_appears_in_the_schema() -> None:
    import json

    app = create_app(access_key=ACCESS_KEY)
    assert ACCESS_KEY not in json.dumps(app.openapi())
    # Auth routes are present when enabled.
    assert "/api/v1/auth/login" in app.openapi()["paths"]
