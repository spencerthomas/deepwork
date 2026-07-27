"""Mint short-lived GitHub App installation tokens for sandbox git operations.

This is the credential model every major coding agent uses (Copilot, Codex,
Jules, Devin, Renovate, and Anthropic's own ``claude-code-action``): a GitHub
App, installed on the chosen repositories, mints an **installation access
token** that expires after ~1 hour and is scoped to the app's granted
permissions and repositories. We mint one fresh per task and inject it into the
ephemeral sandbox, so no long-lived secret ever reaches agent-visible content.

Only the app id and private key are read from the server environment. The
private key never leaves this process; the minted token is passed straight to
the per-task sandbox and is never logged or returned in task output.

Signing uses ``cryptography`` directly (RS256) to avoid adding a JWT dependency.
"""

from __future__ import annotations

import base64
import binascii
import json
import time
import urllib.error
import urllib.request

__all__ = ["GitHubAppError", "build_app_jwt", "mint_installation_token", "normalize_private_key"]

_GITHUB_API = "https://api.github.com"
_JWT_SKEW_SECONDS = 60
_JWT_TTL_SECONDS = 540  # GitHub rejects app JWTs with exp more than 10 minutes out.


class GitHubAppError(Exception):
    """A recoverable failure minting an installation token; callers fail open."""


def normalize_private_key(raw: str) -> str:
    """Return a PEM private key, accepting either raw PEM or base64-encoded PEM.

    Deployment platforms often make multi-line secrets easier to store as a
    single base64 blob, so accept both forms.
    """
    text = raw.strip()
    if "-----BEGIN" in text:
        return text
    try:
        decoded = base64.b64decode(text, validate=True).decode("utf-8")
    except (binascii.Error, ValueError, UnicodeDecodeError) as error:
        msg = "GitHub App private key is neither PEM nor valid base64-encoded PEM"
        raise GitHubAppError(msg) from error
    if "-----BEGIN" not in decoded:
        msg = "decoded GitHub App private key is not PEM"
        raise GitHubAppError(msg)
    return decoded.strip()


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def build_app_jwt(app_id: str, private_key_pem: str, *, now: int | None = None) -> str:
    """Build a short-lived RS256 app JWT signed with the app's private key."""
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError as error:  # pragma: no cover - cryptography is a pinned dep
        msg = "cryptography is required to sign the GitHub App JWT"
        raise GitHubAppError(msg) from error

    issued = int(now if now is not None else time.time())
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "iat": issued - _JWT_SKEW_SECONDS,
        "exp": issued + _JWT_TTL_SECONDS,
        "iss": app_id,
    }
    signing_input = f"{_b64url(_json(header))}.{_b64url(_json(payload))}".encode("ascii")
    try:
        key = serialization.load_pem_private_key(private_key_pem.encode("utf-8"), password=None)
        signature = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())  # type: ignore[call-arg]
    except Exception as error:  # noqa: BLE001 - normalize any key/sign failure
        msg = "failed to sign GitHub App JWT with the provided private key"
        raise GitHubAppError(msg) from error
    return f"{signing_input.decode('ascii')}.{_b64url(signature)}"


def _json(value: object) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode("utf-8")


def _get(url: str, token: str) -> object:
    request = urllib.request.Request(url)  # noqa: S310 - fixed https api.github.com host
    _auth(request, token)
    return _send(request)


def _post(url: str, token: str) -> object:
    request = urllib.request.Request(url, data=b"", method="POST")  # noqa: S310 - fixed host
    _auth(request, token)
    return _send(request)


def _auth(request: urllib.request.Request, token: str) -> None:
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    request.add_header("User-Agent", "deep-work-agent")


def _send(request: urllib.request.Request) -> object:
    try:
        with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310 - fixed host
            return json.loads(response.read().decode("utf-8") or "null")
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:200]
        msg = f"GitHub API returned HTTP {error.code}: {detail}"
        raise GitHubAppError(msg) from None
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        msg = "GitHub API request failed"
        raise GitHubAppError(msg) from error


def _first_installation_id(app_jwt: str, api_base: str) -> int:
    installations = _get(f"{api_base}/app/installations", app_jwt)
    if not isinstance(installations, list) or not installations:
        msg = "the GitHub App has no installations; install it on the target repositories"
        raise GitHubAppError(msg)
    identifier = installations[0].get("id") if isinstance(installations[0], dict) else None
    if not isinstance(identifier, int):
        msg = "GitHub App installation response was malformed"
        raise GitHubAppError(msg)
    return identifier


def mint_installation_token(
    *,
    app_id: str,
    private_key_pem: str,
    installation_id: int | None = None,
    api_base: str = _GITHUB_API,
    now: int | None = None,
) -> str:
    """Mint a ~1-hour installation access token for the app.

    When ``installation_id`` is omitted, the app's first installation is used
    (the common single-install case). Raises :class:`GitHubAppError` on any
    failure so callers can fall back to no credential rather than crash a task.
    """
    app_jwt = build_app_jwt(app_id, private_key_pem, now=now)
    if installation_id is None:
        installation_id = _first_installation_id(app_jwt, api_base)
    result = _post(f"{api_base}/app/installations/{installation_id}/access_tokens", app_jwt)
    token = result.get("token") if isinstance(result, dict) else None
    if not isinstance(token, str) or not token:
        msg = "GitHub App installation token response was malformed"
        raise GitHubAppError(msg)
    return token
