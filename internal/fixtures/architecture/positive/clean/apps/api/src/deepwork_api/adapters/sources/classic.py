"""Approved server-side provider adapter."""

import langsmith


def provider_name() -> str:
    return langsmith.__name__
