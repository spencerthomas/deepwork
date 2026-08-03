"""Bounded-cache tests for the server-side trace locator."""

from __future__ import annotations

import httpx

from deepwork_api.adapters.trace import langsmith


async def test_trace_locator_uses_a_bounded_lru_cache() -> None:
    calls: list[str] = []

    def resolve(request: httpx.Request) -> httpx.Response:
        run_id = request.url.path.rsplit("/", maxsplit=1)[-1]
        calls.append(run_id)
        return httpx.Response(200, json={"app_path": f"/o/example/r/{run_id}"})

    locator = langsmith.LangSmithTraceLocator(api_key="server-key")
    await locator._client.aclose()
    locator._client = httpx.AsyncClient(
        base_url="https://api.smith.langchain.com",
        transport=httpx.MockTransport(resolve),
    )
    try:
        for index in range(langsmith._MAX_CACHE_ENTRIES + 1):
            run_id = f"run-{index}"
            assert (
                await locator.locate(run_id) == f"https://smith.langchain.com/o/example/r/{run_id}"
            )

        assert len(locator._cache) == langsmith._MAX_CACHE_ENTRIES
        assert "run-0" not in locator._cache

        calls_before_cached_read = len(calls)
        assert await locator.locate("run-1") == "https://smith.langchain.com/o/example/r/run-1"
        assert len(calls) == calls_before_cached_read

        assert await locator.locate("run-0") == "https://smith.langchain.com/o/example/r/run-0"
        assert calls.count("run-0") == 2
        assert len(locator._cache) == langsmith._MAX_CACHE_ENTRIES
    finally:
        await locator.close()
