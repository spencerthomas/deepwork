# Deep Work agent package

`deepwork-agent` is the independent Python package boundary for the future Deep
Work agent graph. This Wave 1 scaffold is deliberately credential-free and has no
application-service dependency.

The runtime contract is currently unavailable behind `SPIKE-CONFIG-001`. Importing
`deepwork_agent` performs no network call, reads no environment variable, and does
not create a model, graph, deployment, or provider client. `create_graph()` raises
the typed `RuntimeCapabilityUnavailable` error until a later reviewed plan pins a
supported public runtime contract. No `langgraph.json` is shipped while that gate
is open.

## Local checks

Python 3.12 and uv are required. From the repository root:

```bash
make -C packages/agent doctor
make -C packages/agent bootstrap
make -C packages/agent check
make -C packages/agent package-check
```

`package-check` is read-only: it builds twice, requires matching artifact hashes,
and compares the fresh result with the reviewed `artifacts.json` manifest. After a
reviewed source change, refresh that manifest deliberately with
`make -C packages/agent update-evidence`, then rerun `check` to prove the checkout
stays clean.

The package owns its `pyproject.toml`, `uv.lock`, environment, commands, source,
tests, and build artifacts. It never relies on a root Python environment or
`PYTHONPATH`.
