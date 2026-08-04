"""Session-authenticated API acceptance and separate-worker recovery contract."""

import asyncio
import json
import sys
import time
from pathlib import Path

import httpx
import pytest

from deepwork_api import create_app
from deepwork_api.adapters.persistence import SQLiteJobRepository
from deepwork_api.domain import SecurityContext

_KEY_A = "application-key-a-00000000000000000001"
_KEY_B = "application-key-b-00000000000000000002"
_KEY_A_PEER = "application-key-a-peer-0000000000000003"
_CONTEXT_A = SecurityContext("tenant-secret-a", "workspace-a", "actor-a")
_CONTEXT_B = SecurityContext("tenant-secret-b", "workspace-b", "actor-b")
_CONTEXT_A_PEER = SecurityContext("tenant-secret-a", "workspace-peer", "actor-peer")


async def _login(client: httpx.AsyncClient, key: str) -> None:
    response = await client.post("/api/v1/auth/login", json={"accessKey": key})
    assert response.status_code == 200


async def test_authenticated_job_survives_api_restart_and_separate_worker(
    tmp_path: Path,
) -> None:
    database = (tmp_path / "jobs.sqlite3").resolve()
    app = create_app(
        job_database_path=database,
        access_key_contexts={_KEY_A: _CONTEXT_A},
    )

    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="https://jobs.test",
        ) as client:
            unauthenticated = await client.post(
                "/api/v1/jobs/fixture",
                headers={"Idempotency-Key": "request-missing-auth"},
            )
            assert unauthenticated.status_code == 401
            assert unauthenticated.json() == {
                "code": "unauthorized",
                "message": "Authentication required.",
            }
            direct_access_key = await client.post(
                "/api/v1/jobs/fixture",
                headers={
                    "Authorization": f"Bearer {_KEY_A}",
                    "Idempotency-Key": "request-direct-key",
                },
            )
            assert direct_access_key.status_code == 401
            assert _KEY_A not in direct_access_key.text

            await _login(client, _KEY_A)
            accepted_response = await client.post(
                "/api/v1/jobs/fixture",
                headers={"Idempotency-Key": "request-0001"},
            )
            assert accepted_response.status_code == 202
            accepted = accepted_response.json()
            assert accepted == {
                "jobId": accepted["jobId"],
                "kind": "fixture.noop",
                "status": "queued",
                "attempts": 0,
                "maxAttempts": 3,
                "duplicate": False,
                "safeError": None,
                "durability": "local-sqlite-proof",
            }
            assert _KEY_A not in accepted_response.text
            assert _CONTEXT_A.tenant_id not in accepted_response.text

            duplicate = await client.post(
                "/api/v1/jobs/fixture",
                headers={"Idempotency-Key": "request-0001"},
            )
            assert duplicate.status_code == 202
            assert duplicate.json()["jobId"] == accepted["jobId"]
            assert duplicate.json()["duplicate"] is True

    worker = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        "from deepwork_api.bootstrap.worker import main; raise SystemExit(main())",
        "--job-database",
        str(database),
        "--worker-id",
        "worker-after-api-restart",
        "--once",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await worker.communicate()
    assert worker.returncode == 0, stderr.decode()
    worker_result = json.loads(stdout.decode())
    assert worker_result == {
        "status": "succeeded",
        "durability": "local-sqlite-proof",
        "jobId": accepted["jobId"],
    }

    recovered_app = create_app(
        job_database_path=database,
        access_key_contexts={_KEY_A: _CONTEXT_A},
    )
    async with recovered_app.router.lifespan_context(recovered_app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=recovered_app),
            base_url="https://jobs.test",
        ) as client:
            await _login(client, _KEY_A)
            recovered = await client.get(f"/api/v1/jobs/{accepted['jobId']}")

    assert recovered.status_code == 200
    assert recovered.json()["status"] == "succeeded"
    assert recovered.json()["attempts"] == 1


async def test_peer_tenant_session_cannot_observe_existing_job(tmp_path: Path) -> None:
    database = (tmp_path / "jobs.sqlite3").resolve()
    app = create_app(
        job_database_path=database,
        access_key_contexts={_KEY_A: _CONTEXT_A, _KEY_B: _CONTEXT_B},
    )
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="https://jobs.test",
        ) as tenant_a:
            await _login(tenant_a, _KEY_A)
            accepted = (
                await tenant_a.post(
                    "/api/v1/jobs/fixture",
                    headers={"Idempotency-Key": "tenant-isolation-0001"},
                )
            ).json()

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="https://jobs.test",
        ) as tenant_b:
            await _login(tenant_b, _KEY_B)
            denied = await tenant_b.get(f"/api/v1/jobs/{accepted['jobId']}")
            invalid = await tenant_b.get("/api/v1/jobs/not-a-job")

    assert denied.status_code == 404
    assert denied.json() == {
        "code": "job_not_found",
        "message": "Job was not found.",
    }
    assert _CONTEXT_A.tenant_id not in denied.text
    assert _CONTEXT_B.tenant_id not in denied.text

    assert invalid.status_code == 422
    assert invalid.json() == {
        "code": "request_invalid",
        "message": "Request validation failed.",
    }


async def test_peer_workspace_has_separate_idempotency_and_read_scope(tmp_path: Path) -> None:
    database = (tmp_path / "jobs.sqlite3").resolve()
    app = create_app(
        job_database_path=database,
        access_key_contexts={_KEY_A: _CONTEXT_A, _KEY_A_PEER: _CONTEXT_A_PEER},
    )
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="https://jobs.test",
        ) as workspace_a:
            await _login(workspace_a, _KEY_A)
            first = (
                await workspace_a.post(
                    "/api/v1/jobs/fixture",
                    headers={"Idempotency-Key": "shared-workspace-key"},
                )
            ).json()

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="https://jobs.test",
        ) as workspace_peer:
            await _login(workspace_peer, _KEY_A_PEER)
            peer_response = await workspace_peer.post(
                "/api/v1/jobs/fixture",
                headers={"Idempotency-Key": "shared-workspace-key"},
            )
            denied = await workspace_peer.get(f"/api/v1/jobs/{first['jobId']}")

    assert peer_response.status_code == 202
    assert peer_response.json()["jobId"] != first["jobId"]
    assert peer_response.json()["duplicate"] is False
    assert denied.status_code == 404
    assert denied.json()["code"] == "job_not_found"


async def test_worker_error_content_is_not_reflected_by_public_job_read(tmp_path: Path) -> None:
    database = (tmp_path / "jobs.sqlite3").resolve()
    app = create_app(
        job_database_path=database,
        access_key_contexts={_KEY_A: _CONTEXT_A},
    )
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="https://jobs.test",
        ) as client:
            await _login(client, _KEY_A)
            accepted = (
                await client.post(
                    "/api/v1/jobs/fixture",
                    headers={"Idempotency-Key": "safe-public-error-0001"},
                )
            ).json()
            repository: SQLiteJobRepository = app.state.job_repository
            now = int(time.time())
            lease = await repository.lease_next(
                worker_id="worker-failure",
                now=now,
                lease_seconds=30,
            )
            assert lease is not None
            await repository.fail(
                job_id=lease.job.job_id,
                lease_token=lease.lease_token,
                now=now + 1,
                safe_error=f"failed for {_CONTEXT_A.tenant_id}",
                retryable=False,
            )

            response = await client.get(f"/api/v1/jobs/{accepted['jobId']}")

    assert response.status_code == 200
    assert response.json()["safeError"] == "Job execution failed."
    assert _CONTEXT_A.tenant_id not in response.text


def test_durable_job_database_requires_existing_session_authentication(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="session authentication"):
        create_app(job_database_path=(tmp_path / "jobs.sqlite3").resolve())


def test_job_contract_and_schema_never_publish_identity_or_credentials(tmp_path: Path) -> None:
    app = create_app(
        job_database_path=(tmp_path / "jobs.sqlite3").resolve(),
        access_key_contexts={_KEY_A: _CONTEXT_A},
    )
    serialized = json.dumps(app.openapi())
    assert _KEY_A not in serialized
    assert _CONTEXT_A.tenant_id not in serialized
    job_schema = app.openapi()["components"]["schemas"]["JobResponse"]["properties"]
    assert "tenantId" not in job_schema
    assert "workspaceId" not in job_schema
    assert "actorId" not in job_schema

    paths = app.openapi()["paths"]
    fixture_responses = paths["/api/v1/jobs/fixture"]["post"]["responses"]
    read_responses = paths["/api/v1/jobs/{job_id}"]["get"]["responses"]
    assert set(fixture_responses) == {"202", "401", "422"}
    assert set(read_responses) == {"200", "401", "404", "422"}
    for response in (*fixture_responses.values(), *read_responses.values()):
        if "content" not in response:
            continue
        schema = response["content"]["application/json"]["schema"]
        if response in (fixture_responses["202"], read_responses["200"]):
            assert schema["$ref"].endswith("/JobResponse")
        else:
            assert schema["$ref"].endswith("/ProblemResponse")
