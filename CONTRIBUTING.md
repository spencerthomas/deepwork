# Contributing to Deep Work

Deep Work follows the contributor shape used by LangChain and Deep Agents:
small scoped changes, public API discipline, typed boundaries, independently
testable packages, Conventional Commit titles with a scope, and evidence-backed
review.

## Before opening a pull request

1. Search existing issues and discussions. For a non-trivial change, agree the
   outcome and ownership boundary before implementation.
2. Read `AGENTS.md`, the nearest scoped `AGENTS.md`, the owning product
   specification, and the active ExecPlan when one is required.
3. Use a dedicated branch or worktree and keep the change bounded.
4. Add or update tests that fail when the changed behavior is broken.
5. Run the repository checks below and include exact results in the pull request.

```bash
make doctor
make bootstrap
make check
make package-check
```

`make check` is the authoritative local gate. It runs the TypeScript workspaces,
both independently locked Python projects, architecture checks, cross-language
contracts, builds, and canonical documentation validation. `make package-check`
then verifies packed artifacts in clean consumers.

Use package-local commands while iterating:

```bash
pnpm --filter @deepwork/web test
make -C apps/api test
make -C packages/agent test
```

Unit tests do not use the network. Tests requiring an external service,
credential, or live contract need a separately reviewed integration plan and
must never be added to the default unit command.

## Public APIs and dependencies

- Preserve exported names and signatures. Add new parameters as keyword-only
  values with safe defaults in Python.
- Use supported public LangChain, LangGraph, and Deep Agents APIs. Do not import
  private upstream modules.
- Runtime libraries use compatible version ranges; lockfiles own exact resolved
  versions.
- Add a Changeset for a user-visible change to `@deepwork/domain`,
  `@deepwork/sdk`, or `@deepwork/ui`.
- Never weaken an architecture, contract, or generated-drift check to make a
  change pass.

## Pull requests

Use a scoped Conventional Commit title such as:

```text
feat(agent): enforce tool-call approval
fix(sdk): preserve unknown task status
docs(repo): clarify offline validation
```

Explain the user outcome and why the selected boundary is appropriate. Identify
public API, security, privacy, migration, and external-contract effects. Keep
production credentials, private source content, and customer data out of issues,
tests, fixtures, logs, screenshots, and pull requests.

Do not enable an unresolved provider contract, edit generated output directly,
or use a fixture, prototype, or green build as proof of authenticated production
behavior.

Security issues should follow [SECURITY.md](SECURITY.md), not a public issue.
