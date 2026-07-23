# Documentation agent instructions

These instructions apply to documentation under `docs/` in addition to the repository root guidance.

## Document roles

- Root `ARCHITECTURE.md` is the concise canonical deployable-unit, package, layer, state, credential, and dependency map. Detailed rationale lives under `docs/design-docs/`.
- `docs/PRODUCT_SENSE.md` defines the product promise and judgment principles; `docs/PLANS.md` defines the release roadmap and when a living ExecPlan is required.
- `docs/DESIGN.md`, `docs/FRONTEND.md`, `docs/RELIABILITY.md`, `docs/SECURITY.md`, and `docs/QUALITY_SCORE.md` own cross-cutting standards and link to executable evidence.
- `docs/design-docs/` contains indexed durable rationale and accepted decisions with supersession history.
- `docs/product-specs/` contains stable-ID feature outcomes, journeys, states, contracts, metrics, rollout, and acceptance. A product specification is not an implementation work log.
- `docs/exec-plans/active/` contains self-contained living implementation plans; completed work moves to `docs/exec-plans/completed/` with its outcome and retrospective intact. `tech-debt-tracker.md` contains owned debt with consequence and repayment trigger.
- `docs/generated/` contains reproducible machine-owned schema/API/package/architecture/coverage/issue views. Each file identifies its generator, inputs, command, and source commit; hand edits are forbidden.
- `docs/references/` contains pinned external, research, and legacy evidence. References do not silently override an accepted decision.
- `docs/proposals/` contains isolated, non-canonical material awaiting review. A proposal is not implementation authority until its integration map is approved and completed.

Every governed document has a stable ID, status, owner, last-reviewed date,
authoritative sources, last verified commit or governed paths, and supersession
metadata where applicable. Keep historical documents intact unless review
explicitly authorizes replacement.

## Living ExecPlan standard

An active ExecPlan must be understandable from the checkout alone. Include
purpose and observable outcome, context/paths/vocabulary, non-goals, prerequisites
and permissions, independently verifiable milestones, exact commands and expected
observations, interfaces and dependencies, validation, idempotence/rollback/recovery,
and these maintained sections: `Progress`, `Surprises & Discoveries`, `Decision
Log`, and `Outcomes & Retrospective`.

Do not copy stable product scope into an issue plan. Link the owning product spec,
record the bounded implementation approach, and update the plan while work proceeds.

## Source and claim discipline

- Pin repository evidence to a full commit and external behavior to an exact package/API version and access tier.
- Prefer primary sources, generated schemas, and observed contract transcripts. Mark each material external claim as documented, gated/beta, inferred, contradicted, or unknown.
- Distinguish control-plane APIs, deployment data-plane APIs, runtime/harness APIs, and product UI behavior. Never use one plane as evidence for another.
- When sources conflict, describe the conflict and add a decision or spike gate. Do not average incompatible claims into a vague contract.
- Avoid unsupported endpoint and product names. In particular, do not assert public Fleet CRUD, `/v1/deepagents/*`, arbitrary Managed Deep Agents connector routes, global thread search, or application-owned `mda deploy` behavior without accepted live evidence.
- Link every resolved contradiction to its decision entry and every unresolved contract to its spike acceptance criteria.
- Keep two precedence ladders explicit. External behavior uses accepted live contract, installed public API/generated schema, official docs, then reference internals. Engineering practice uses accepted Deep Work decisions/executable config, enforcing tests/generated artifacts, scoped `AGENTS.md`, then pinned reference patterns/prose.
- Treat pinned LangChain/Deep Agents/LangGraph/LangChain.js source as engineering and reuse evidence. It does not authorize private imports or turn an internal implementation into a hosted public contract.

## Feature plan standard

Use stable feature IDs. Each behavior has one owning plan; related plans may reference it but must not redefine it. Every implementation-ready v1 plan must state:

- user outcome and audience;
- source evidence and confidence;
- in-scope and out-of-scope behavior;
- owning app or package and dependencies;
- primary, responsive, keyboard, and recovery journeys;
- loading, empty, error, offline, permission, stale, reconnecting, interrupted, partial, and success states where applicable;
- interfaces, normalized types, data flow, and runtime capability fallback;
- state ownership, persistence, tenancy, credentials, and security boundaries;
- accessibility behavior and supported responsive surfaces;
- success metrics and observable events without sensitive payloads;
- rollout, feature-flag, migration, and rollback behavior;
- executable acceptance scenarios with fixtures and live-contract coverage.

Do not mark a plan ready if it contains `TBD`, unresolved implementation choices, an unowned dependency, an unverified external contract, or acceptance criteria that cannot be executed. Later-release briefs may carry discovery gates, but must identify them explicitly and must not masquerade as v1-ready work.

## Canonical vocabulary

Use the approved glossary consistently. Do not interchange task, thread, run, and checkpoint; agent, assistant, deployment, and source; environment, snapshot, and sandbox; interrupt, approval, and decision; file, artifact, and attachment; or org, workspace, tenant, and actor.

If a new domain term is necessary, add it to the glossary before using it across plans. If an external product uses a conflicting term, name the external term and map it to the Deep Work term.

## Review and integration

- Update the feature catalog, coverage matrix, decision register, and affected canonical plan together when scope changes.
- Every route, tab, settings section, release criterion, and backlog item must map to one owning feature ID or an explicit removal decision.
- Integration must follow the proposal's merge map. Copying a proposal file into a canonical directory without reconciling contradictions is not integration.
- Keep source citations human-readable. Do not leave temporary tool references, unexplained line numbers, or unverifiable claims.
- Run the documentation checker. It must detect broken/orphaned links, duplicate IDs, missing metadata/living sections, stale governed paths, glossary conflicts, invalid state transitions, and generated drift.
- Check relative links, headings, feature IDs, stable feature/program acceptance-scenario IDs, destination paths, generated issue mappings, and table consistency before handoff. A release criterion has exactly one E2E owner; E2E scenarios may compose several feature scenarios without changing feature ownership.
- Recurring documentation gardening may repair bounded drift or open issues; it may not change accepted product scope, lower a quality gate, or self-approve a proposal.
