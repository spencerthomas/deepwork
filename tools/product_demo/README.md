# Product-demo isolation driver

`worktree_driver.py` is the credential-free, loopback-only implementation behind
the repository worktree harness. It starts two complete local cells using the
real Deep Work API and designed Next.js shell. Each cell owns a PostgreSQL
cluster, task/settings stores, worker, object service, telemetry service, browser
origin, logs and proof artifacts.

The contract is deliberately sealed in two commits. The candidate commit contains
the exact reviewed driver and browser-oracle bytes; its descendant seal changes only
`reviewed_repository_commit` in `worktree-driver-contract.json`. The canonical
entry point is always `tools/worktree/harness.py exercise`; running the driver
directly does not create an acceptance receipt.

Requirements are local PostgreSQL binaries, the bootstrapped API environment,
Node 24, offline-installed web dependencies in both checked-out roots, and the
pinned Playwright browser already used by the repository browser gates.
