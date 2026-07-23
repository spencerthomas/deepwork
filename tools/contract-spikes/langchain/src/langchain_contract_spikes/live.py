"""Fail-closed profile gate for opt-in live classic-sandbox probes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class LiveProfile:
    name: str
    base_url: str
    account_tier: str
    region: str
    server_revision: str


def load_live_profile(arguments: Mapping[str, str]) -> LiveProfile:
    """Load only explicit non-production profile arguments, never environment dumps."""
    required = ("profile", "base_url", "account_tier", "region", "server_revision")
    missing = [key for key in required if not arguments.get(key)]
    if missing:
        raise RuntimeError(f"live profile unavailable: missing {', '.join(missing)}")
    if arguments["profile"] != "classic-sandbox":
        raise RuntimeError("live profile must be classic-sandbox")
    if not arguments["base_url"].startswith("https://") or "prod" in arguments["base_url"].lower():
        raise RuntimeError("live base URL must be an explicit non-production HTTPS sandbox")
    return LiveProfile(
        name=arguments["profile"],
        base_url=arguments["base_url"],
        account_tier=arguments["account_tier"],
        region=arguments["region"],
        server_revision=arguments["server_revision"],
    )
