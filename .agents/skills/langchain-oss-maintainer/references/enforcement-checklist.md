# Deep Work LangChain/OSS enforcement checklist

## Package boundaries

- [ ] `packages/domain` is pure, client-safe, framework-free, and owns canonical
      identity, status, event, reducer, and capability semantics.
- [ ] `packages/sdk` maps transport data into domain values and imports no UI,
      provider SDK, server secret, or application internals.
- [ ] `packages/ui` is presentational, imports no SDK, performs no I/O, and
      exposes reusable loading, empty, error, unavailable, and success states.
- [ ] Applications compose public package entries and do not recreate a
      competing durable contract.
- [ ] Boundary tests fail on forbidden import direction.

## Agent runtime

- [ ] `packages/agent` can build and install independently.
- [ ] Model selection and credentials are caller-owned.
- [ ] Only supported public Deep Agents, LangChain, and LangGraph APIs are used.
- [ ] Plan approval and caller-tool authorization are distinct, fail-closed
      controls.
- [ ] Interrupt request/config/decision ordering and checkpoint identity survive
      pause, resume, edit, rejection, and recovery.
- [ ] Nested execution exposes sanitized progress through public streaming APIs.
- [ ] Model, tool, repository, file, web, and task content remains untrusted.

## Tests and compatibility

- [ ] Python suites use `tests/unit_tests`, `tests/integration_tests`,
      `tests/evaluation`, and `tests/benchmarks` according to purpose.
- [ ] Default gates require no credentials and deny outbound sockets.
- [ ] Tool-use tests perform a real fake-model tool call and prove no execution
      happens before approval.
- [ ] Coverage has an explicit threshold; evaluations have deterministic
      datasets; benchmarks are separated from correctness CI.
- [ ] Runtime dependencies use compatible ranges and a lockfile.
- [ ] CI exercises every supported Python and Node version claimed in metadata.

## Repository and community

- [ ] One root command checks TypeScript, all Python projects, architecture,
      contracts, docs, builds, and package consumers.
- [ ] Contract tasks execute real tests and cannot succeed vacuously.
- [ ] CI actions use immutable SHA pins and least-privilege permissions.
- [ ] Pull-request and issue templates, private security reporting,
      dependency-update automation, pre-commit hooks, and change metadata exist.
- [ ] Contributor docs name the exact local/CI commands and public API policy.
- [ ] Generated docs and active ExecPlans are current.

## Remote-enforcement safety

- [ ] The inspected commit is the latest fetched `origin/main`.
- [ ] Existing user work and protected branches are unchanged.
- [ ] Corrections use a fresh, scoped branch/worktree and a pull request.
- [ ] No merge, release, deployment, credential change, or destructive cleanup
      occurs without explicit authority.
