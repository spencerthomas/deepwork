"""Credential-free tests for GitHub App JWT signing and key normalization.

No network: an RSA keypair is generated in-process, the app JWT is built and
then verified against the public key, so the signing path is exercised end to
end without contacting GitHub.
"""

from __future__ import annotations

import base64
import json

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from deepwork_agent.github_app import (
    GitHubAppError,
    build_app_jwt,
    normalize_private_key,
)


def _keypair() -> tuple[str, object]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    return pem, key.public_key()


def _b64url_decode(segment: str) -> bytes:
    padding_needed = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding_needed)


def test_build_app_jwt_produces_a_verifiable_rs256_token() -> None:
    pem, public_key = _keypair()
    now = 1_700_000_000

    token = build_app_jwt("123456", pem, now=now)

    header_b64, payload_b64, signature_b64 = token.split(".")
    header = json.loads(_b64url_decode(header_b64))
    payload = json.loads(_b64url_decode(payload_b64))

    assert header == {"alg": "RS256", "typ": "JWT"}
    assert payload["iss"] == "123456"
    assert payload["iat"] == now - 60
    assert payload["exp"] == now + 540
    # exp must be within GitHub's 10-minute ceiling.
    assert payload["exp"] - payload["iat"] <= 600

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    # Raises InvalidSignature if the signature does not verify.
    public_key.verify(  # type: ignore[union-attr]
        _b64url_decode(signature_b64), signing_input, padding.PKCS1v15(), hashes.SHA256()
    )


def test_normalize_private_key_accepts_raw_pem() -> None:
    pem, _ = _keypair()
    assert normalize_private_key(pem) == pem.strip()
    assert normalize_private_key(f"  {pem}  ") == pem.strip()


def test_normalize_private_key_accepts_base64_encoded_pem() -> None:
    pem, _ = _keypair()
    encoded = base64.b64encode(pem.encode("utf-8")).decode("ascii")
    assert normalize_private_key(encoded) == pem.strip()


def test_normalize_private_key_rejects_garbage() -> None:
    with pytest.raises(GitHubAppError):
        normalize_private_key("not a key and not base64 !!!")


def test_build_app_jwt_rejects_an_invalid_key() -> None:
    with pytest.raises(GitHubAppError):
        build_app_jwt("123456", "-----BEGIN PRIVATE KEY-----\nnope\n-----END PRIVATE KEY-----")
