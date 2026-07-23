# Agent package agent instructions

These instructions apply to `packages/agent` in addition to the repository root guidance.

## Runtime boundary

`packages/agent` is an independently deployable Python deepagents project. It owns graph composition, instructions, tools, middleware, subagents, schedules, skills, sandbox declaration, and agent-runtime tests.

It is not the FastAPI application service. Do not import `apps/api`, web code, UI code, TypeScript SDK internals, or application persistence models. Communicate with the application and clients only through verified deployment, stream, connector, webhook, and artifact contracts.

Keep the project valid for the supported classic LangSmith Deployment baseline. Managed Deep Agents additions must be capability-gated and must not make the baseline graph invalid. Do not configure a backend, store, or checkpointer in graph code when the target runtime owns those facilities.

## Composition and dependencies

- Compose on pinned upstream harnesses; do not fork or vendor deepagents, LangGraph, or provider packages.
- Prefer public upstream components over parallel implementations. Pin and conformance-test exported Deep Agents middleware such as beta `RubricMiddleware`; use or hand off to official deployment CLI and sandbox/ACP packages. Do not import private modules from Deep Agents Code, Talon, the CLI, or SDK internals.
- Keep task-type differences in explicit assistant configuration, tools, middleware, or templates rather than duplicate graphs.
- Make optional or beta middleware isolated and capability-detected. The graph must fail with an actionable configuration error when a required version or runtime capability is missing.
- Keep tools narrow, typed, bounded, and independently testable. Tool names and schemas are public runtime contracts once a client or approval rule depends on them.
- Keep model and provider selection configuration-driven. Validate incompatible model, tool, middleware, and structured-output combinations at startup.

## Python package method

- Keep a package-local `pyproject.toml`, `uv.lock`, `Makefile`, README, source package, tests, explicit `__all__`, and `py.typed`. Use `uv` for install/run/lock/build and never rely on `apps/api` or a shared implicit virtual environment.
- Use one reviewed, explicit layout rather than a collection of top-level scripts:

  ```text
  packages/agent/
  ├── pyproject.toml
  ├── uv.lock
  ├── langgraph.json
  ├── Makefile
  ├── README.md
  ├── src/deepwork_agent/
  │   ├── __init__.py
  │   ├── py.typed
  │   ├── graph.py          # exported graph factory/entry point
  │   ├── config.py         # typed environment and assistant configuration
  │   ├── state.py          # reviewed graph input/state/output schemas
  │   ├── prompts/
  │   ├── tools/
  │   ├── middleware/
  │   └── templates/
  ├── tests/{unit,contract,integration}/
  └── evals/{datasets,graders}/
  ```

  The distribution name, import package, `langgraph.json` graph target, public
  exports, supported state/input/output schemas, and deployment validation command
  are reviewed contracts. Keep `.env` files local and ignored; commit only a
  redacted `.env.example` when configuration discovery needs one.
- Use Ruff formatting/linting, `ty`, absolute imports, complete production annotations, and Google-style docstrings. Prefer exact justified inline suppressions; do not weaken the package configuration for one exception.
- Package commands expose `format`, `lint`, `typecheck`, `test`, `contract`, `integration`, `eval`, `build`, and deployment validation with distinct semantics. Unit tests disable sockets; hosted/runtime tests are explicit and pinned.
- New public parameters are keyword-only. Exported signatures, state fields, tool schemas, and middleware behavior receive compatibility review, tests, and migration/deprecation notes.
- Keep deterministic unit/contract tests separate from stochastic model/runtime evals. Evals record dataset, model/profile, agent commit, grader, repetition, cost, and trace metadata and do not silently run under `make test`.

## State and contract invariants

- Use the canonical task, thread, run, checkpoint, actor, tenant, and source meanings. Do not create a second application task lifecycle inside graph state.
- Define state channels and reducers explicitly. Make retry, replay, checkpoint restore, and concurrent updates deterministic.
- Emit client-visible values through documented schemas with versioned tests. Do not put arbitrary Python objects or secret-bearing provider responses into state.
- Preserve ordered HITL action requests and review configuration. Permission rules for filesystem access do not replace `interrupt_on` for execution, MCP, GitHub, or other tools.
- Treat queued steering, submit behavior, and multitask strategy as verified runtime capabilities. Do not recreate scheduler or queue semantics in middleware without an accepted plan.
- Keep schedule declarations and runtime cron resources distinct. A definition in source is not proof that a hosted schedule was reconciled.

## Tools, sandbox, and credentials

- Validate tool inputs and bound output size, execution time, retries, recursion, and network access.
- Treat repository files, prompts, MCP results, web pages, terminal output, and artifacts as untrusted. Defend against prompt injection at tool boundaries and preserve provenance in outputs.
- Default sandbox network and filesystem access to least privilege. Enforce path containment and deny secret locations even when a model asks explicitly.
- Never embed API keys, installation tokens, ingress secrets, or user credentials in graph state, prompts, environment snapshots, artifacts, logs, traces, or exceptions.
- Obtain short-lived scoped credentials through the approved auth proxy or platform broker. Fail closed if actor, tenant, host, repository, or scope does not match.
- Destructive and externally visible tools require explicit policy, auditable HITL behavior, idempotency where possible, and a safe failure result the model can reason about.

## Reliability and verification

- Distinguish retryable model/tool errors, policy denials, user rejections, budget or call limits, cancellation, and terminal defects. Do not hide them behind a successful text response.
- Bound model retries, tool retries, fallbacks, subagent fan-out, execution time, and rubric loops. Surface exhaustion through stable state and trace metadata.
- Unit-test tools, middleware, reducers, identity scoping, and configuration validation. Add runtime contract tests for graph invocation, streaming projections, interrupts and ordered resume, checkpoints, cancellation, and failure recovery.
- Test supported runtime tiers against pinned versions. A local graph test does not establish hosted control-plane behavior.
- Use synthetic repositories and redacted payloads. Never place customer files or credentials in fixtures, snapshots, or recorded traces.
- Keep `uv`, Ruff, pytest, and deployment validation green. Do not loosen types, lint, permission rules, or test assertions to accommodate an upstream drift; verify and adapt at the boundary.

## Documentation

- Document every tool's purpose, side effects, input bounds, credential needs, approval policy, and failure behavior.
- Document all state fields emitted for clients and link them to SDK contract tests.
- Record required deployment capabilities and explicit fallbacks. Mark beta-only features as beta in configuration, docs, and acceptance tests.
