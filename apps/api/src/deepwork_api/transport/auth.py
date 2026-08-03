"""FastAPI authentication routes and the session guard dependency.

Login exchanges the server-held access key for an opaque session token. The
token is returned for bearer clients and also set as an HttpOnly cookie. Task
routes are protected by :func:`build_session_guard` when auth is enabled.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from deepwork_api.application import AuthService
from deepwork_api.domain import (
    InvalidCredentialError,
    Session,
    SessionExpiredError,
    SessionNotFoundError,
)

_COOKIE_NAME = "deepwork_session"


class LoginRequest(BaseModel):
    """Access-key login payload."""

    accessKey: str = Field(min_length=1, max_length=8192)


class SessionResponse(BaseModel):
    """Non-secret session projection returned to the client."""

    actorId: str
    expiresAt: float

    @classmethod
    def from_domain(cls, session: Session) -> SessionResponse:
        return cls(actorId=session.actor_id, expiresAt=session.expires_at)


def _extract_token(request: Request, authorization: str | None) -> str:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return request.cookies.get(_COOKIE_NAME, "")


def _unauthorized(message: str) -> JSONResponse:
    return JSONResponse(status_code=401, content={"code": "unauthorized", "message": message})


def build_auth_router(auth: AuthService) -> APIRouter:
    """Build the /api/v1/auth routes around an injected auth service."""

    router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

    @router.post("/login")
    async def login(body: LoginRequest, response: Response, request: Request) -> JSONResponse:
        try:
            session = await auth.login(body.accessKey)
        except InvalidCredentialError:
            return _unauthorized("Invalid access key.")
        payload = SessionResponse.from_domain(session).model_dump()
        payload["token"] = session.token
        result = JSONResponse(content=payload)
        result.set_cookie(
            _COOKIE_NAME,
            session.token,
            httponly=True,
            samesite="lax",
            # HTTPS deployments retain Secure; loopback HTTP development must
            # be able to return the cookie to its own middleware and API.
            secure=request.url.scheme == "https",
            max_age=max(1, int(session.expires_at - session.issued_at)),
        )
        return result

    @router.get("/session", response_model=SessionResponse)
    async def current_session(
        request: Request,
        authorization: Annotated[str | None, Header()] = None,
    ) -> SessionResponse | JSONResponse:
        token = _extract_token(request, authorization)
        try:
            session = await auth.authenticate(token)
        except (SessionNotFoundError, SessionExpiredError):
            return _unauthorized("Authentication required.")
        return SessionResponse.from_domain(session)

    @router.post("/logout")
    async def logout(
        request: Request,
        response: Response,
        authorization: Annotated[str | None, Header()] = None,
    ) -> Response:
        token = _extract_token(request, authorization)
        await auth.logout(token)
        result = JSONResponse(content={"ok": True})
        result.delete_cookie(_COOKIE_NAME)
        return result

    return router


def build_session_guard(
    auth: AuthService,
) -> Callable[[Request, str | None], Awaitable[Session]]:
    """Return a FastAPI dependency that requires a live session."""

    async def guard(
        request: Request,
        authorization: Annotated[str | None, Header()] = None,
    ) -> Session:
        token = _extract_token(request, authorization)
        try:
            return await auth.authenticate(token)
        except (SessionNotFoundError, SessionExpiredError):
            raise HTTPException(
                status_code=401,
                detail={"code": "unauthorized", "message": "Authentication required."},
            ) from None

    return guard
