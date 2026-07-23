---
feature_id: DW-ONB-002
title: Source connection, classic deployment, and first-task onboarding
release: v1
status: proposed
decision_status: blocked-on-spikes
owners: [source-platform, application-platform, web, agent-runtime]
surfaces: [web, pwa, desktop, api, agent]
runtime_scopes: [classic, mda, fleet, local, fixture]
source_refs: [SRC-FE, SRC-LC, SRC-DW, SRC-DP]
evidence_pins:
  frontend: 8866d39
  langchain_docs: 7b9215d
  canonical_plan: 06f0515
dependencies: [DW-ONB-001, DW-FND-003, DW-FND-004, DW-FND-005]
contract_gates:
  - SPIKE-SOURCE-001
  - SPIKE-DEPLOY-001
  - SPIKE-MDA-001
last_reviewed: 2026-07-22
---

# Source connection, classic deployment, and first-task onboarding

## User outcome

A newly authenticated user can connect an existing compatible agent or deploy the Deep Work starter agent through a supported classic LangSmith Deployment path, prove that it can be read and invoked, and reach a completed first task within 15 minutes. Managed Deep Agents (MDA) appears only when a capability probe proves the private-beta adapter is usable; the product never recreates `mda deploy` or promises public Fleet CRUD.

## Evidence and confidence

| Evidence | Classification | Planning consequence |
|---|---|---|
| The prototype contains a source/deployment-shaped setup story but no real connection or deployment state. | Prototype evidence at `8866d39`; simulated | Reuse layout cues only; build explicit verification and recovery states. |
| Classic LangSmith Deployments expose the public Agent Server baseline used by assistants, threads, and runs. | Documented at `7b9215d` | Classic deployment and explicit URL + assistant identity are the supported v1 baseline. |
| MDA is private beta and some internal-looking routes in the existing plan are not established public contracts. | Gated/contradicted | Detect MDA as an optional adapter and never call assumed `/v1/deepagents/*` routes. |
| Fleet agents may be readable/invokable without public create/update APIs. | Partly documented; creation unknown | Support a verified read/invoke connection only; link to LangSmith for unsupported management. |
| The vision sets a 15-minute sign-in-to-first-PR goal. | Internal product target at `06f0515` | Instrument every onboarding stage and offer the shortest deterministic connection path. |

## Scope and ownership

### In scope

- A source registry supporting classic LangSmith Deployment, local `langgraph dev`, verified Fleet read/invoke, and capability-gated MDA.
- Connection by deployment URL plus explicit assistant ID/graph identity.
- Discovery only when the source exposes a verified discovery operation.
- Classic starter-agent deployment through an accepted public control-plane workflow or an explicit handoff to LangSmith.
- Source verification for authentication, assistant access, thread/run operations, streaming, HITL, trace links, and optional capabilities.
- A resumable onboarding checklist ending in a small real or fixture task.
- Timing and diagnostics for the 15-minute first-task objective.

### Out of scope

- Reimplementing the `mda deploy` CLI or depending on undocumented upload choreography.
- Public Fleet create/update/delete until such a contract is verified.
- Assuming one org-wide endpoint can search all sources.
- Masking missing capabilities with simulated success.
- Building the agent configuration editor; that belongs to agent/configuration plans.

### Ownership

- FastAPI owns source validation, endpoint policy, capability probes, deployment orchestration, secrets, health checks, and onboarding state.
- Postgres owns normalized source records, capability manifests, probe evidence, assistant mappings, health history, and onboarding checkpoints.
- The separate Python Deep Agents package owns the starter agent artifact and its compatibility tests; it is deployable independently of the application service.
- Next.js/Tauri render the wizard and call identical application APIs.
- LangSmith remains authoritative for deployments, assistants, threads, runs, and provider-side health.

## Primary journeys

### Connect an existing source

1. The wizard asks for source kind, deployment URL, and assistant ID. It explains where each value comes from.
2. The service normalizes and validates the URL, binds the selected credential reference, and rejects private-network targets outside explicit local-development policy.
3. A read-only probe confirms endpoint reachability and assistant access.
4. A capability probe records supported operations and the exact package/server evidence used.
5. The user names the source and selects whether it is the default for new tasks.
6. The wizard launches a minimal first task or a non-mutating connection check if invocation permission is absent.

### Deploy the starter agent

1. The wizard offers **Deploy with classic LangSmith** as the supported path.
2. If `SPIKE-DEPLOY-001` validates an application-driven public workflow, FastAPI creates and monitors that deployment from the versioned Python agent artifact.
3. Otherwise, Deep Work opens a precise LangSmith deployment handoff and waits for the user to paste or confirm the resulting URL and assistant ID.
4. After health and invocation probes pass, the new deployment is stored as an `AgentSource`.
5. MDA is offered only if `SPIKE-MDA-001` returns an allowed capability for this org; failure falls back to classic without losing progress.

### Fifteen-minute first task

1. The checklist shows elapsed time and the remaining steps: authenticate, select workspace, connect/deploy, verify, run, review result.
2. A safe starter task is prefilled for the selected template. Coding can be chosen only after GitHub and environment prerequisites are healthy.
3. The user dispatches, sees live or fallback progress, and reaches a completed task with a trace link. The draft-PR target is measured separately once coding prerequisites are configured.

## State matrix

| State | Required behavior | Recovery / transition |
|---|---|---|
| No source | Explain connect versus deploy and required values. | Choose a path or enter demo. |
| Validating URL | Show the exact host and read-only nature of the probe. | Success, cancel, or specific failure. |
| Invalid/unsafe URL | Reject malformed, credential-bearing, disallowed-scheme, or prohibited private targets. | Edit URL; local targets require local-development mode. |
| Authentication failed | Preserve non-secret form values and identify the failed plane. | Replace credential or switch workspace. |
| Assistant not found | Distinguish missing ID from insufficient permission. | Edit ID or use verified discovery. |
| Capability probing | Show per-capability pending states, not one indefinite spinner. | Persist manifest when complete. |
| Connected, full baseline | Mark read, invoke, thread, run, and stream capabilities individually. | Run first task. |
| Connected, partial | Disable unsupported controls with an explanation. | Use read-only mode, choose another source, or reprobe. |
| Source stale/unreachable | Keep last-known metadata visibly stale and block unsafe mutation. | Retry, update URL/key, or remove source. |
| Classic deploy preparing | Validate artifact version and prerequisites before mutation. | Start provider deployment or cancel. |
| Classic deploy building | Poll using the verified contract and show provider status. | Continue, retry from provider-safe point, or open LangSmith. |
| Deploy failed | Show sanitized build/revision diagnostics and preserve handoff details. | Retry, download logs/link out, or connect another source. |
| MDA unavailable | Do not show a product error; explain beta unavailability if the user requested it. | Fall back to classic. |
| Fleet invoke-only | Label the source read/invoke only and hide unsupported configuration/deploy actions. | Run supported tasks or open LangSmith. |
| Local source offline | Explain that the local server must be running and who can reach it. | Retry from the same device; never proxy in hosted mode by default. |
| First task running | Show elapsed onboarding time and a route to task detail. | Complete, cancel, or recover stream. |
| First task failed | Keep source health separate from task failure. | Retry task, inspect trace, or select fixture starter. |
| Offline during onboarding | Persist completed local steps; block new provider probes/mutations. | Resume automatically when online. |
| Demo source | Clearly mark fixtures and bypass external deployment. | Run fixture task or convert to real setup. |

## Proposed interfaces and runtime fallback

```ts
type SourceKind = "langsmith_deployment" | "fleet_invoke" | "local" | "mda_beta" | "demo";

interface AgentSource {
  id: string;
  kind: SourceKind;
  label: string;
  endpoint: string;
  assistantId: string;
  credentialRef?: string;
  workspaceContext?: { organizationId: string; workspaceId: string };
  capabilities: {
    assistantsRead: boolean;
    threadsRead: boolean;
    runsCreate: boolean;
    stream: "protocol_v2" | "legacy_verified" | "none";
    hitl: boolean;
    traces: boolean;
    sandbox: boolean;
    configuration: "read" | "read_write" | "none";
  };
  probedAt: string;
  evidenceVersion: string;
}
```

Proposed application-service operations:

- `POST /api/v1/sources/probes` validates a candidate without saving it.
- `POST /api/v1/sources` stores a successful normalized source.
- `POST /api/v1/sources/{id}/reprobe` refreshes capability evidence.
- `POST /api/v1/deployments/classic` exists only if `SPIKE-DEPLOY-001` accepts the exact public workflow.
- `GET /api/v1/onboarding` and `PATCH /api/v1/onboarding` make the wizard resumable.

`SPIKE-SOURCE-001` must run a pinned SDK against classic deployment, local dev, and a permitted Fleet source, recording authentication, assistant access, thread/run creation, streaming mode, HITL, trace metadata, and error shapes. A failed optional probe sets a capability false; it does not fail the entire source.

`SPIKE-DEPLOY-001` must prove the classic control-plane create/build/status workflow and its headers from a primary contract. If it cannot, the deterministic fallback is provider-console handoff plus explicit URL/assistant connection.

`SPIKE-MDA-001` must use an approved beta account and supported package/CLI surface. If not accepted, `mda_beta` is absent from production manifests. Deep Work never substitutes assumed MDA endpoints.

## Persistence and security

- Store endpoint, assistant ID, workspace context, non-secret display metadata, probe evidence, and encrypted credential reference in Postgres.
- Treat endpoints as SSRF inputs: enforce HTTPS for hosted sources, resolve DNS safely, block link-local/metadata/private networks by default, and revalidate redirects and DNS changes.
- Localhost is allowed only in explicit local-development mode where the requesting client can reach it; hosted FastAPI must not become an open proxy.
- Source probes are rate-limited, timeout-bounded, read-only until the user explicitly authorizes deployment or a first run, and fully audited.
- Deployment artifacts are content-addressed and built from the reviewed Python Deep Agents package; secrets are not embedded in archives or build logs.
- Deleting a source removes local references and credentials but never deletes a provider deployment unless a separate, explicit provider-side deletion plan is approved.

## Responsive and accessible behavior

- The wizard uses one primary decision per screen on mobile, with a persistent step summary and Back that never loses safe form data.
- Probe results are a semantic list with text labels, not only icons; changing status is announced politely.
- Long URLs and assistant IDs wrap and remain copyable without causing horizontal scrolling.
- Provider handoff links identify that they open another site. Focus returns to the confirmation field when the user comes back.
- Timers are informational and never impose a time limit. Reduced-motion mode removes animated build indicators.

## Metrics and guardrails

- Median and p95 time from authenticated session to verified source.
- Median and p95 time from sign-in start to first completed task and, separately, first draft PR.
- Probe success by source kind and capability, plus sanitized failure category.
- Classic deploy completion and handoff-return rates.
- MDA capability-detection rate; it must never be counted as a classic deployment failure.
- Guardrail: zero successful saves for unverified endpoints or assistant identities.

## Dependencies and rollout

- Depends on auth/session, capability-manifest, persistence, secrets, the starter Python agent artifact, and task dispatch.
- Phase 0: accept source, deploy, and MDA spikes with recorded request/response fixtures.
- Phase 1: internal classic existing-source connection and local development.
- Phase 2: provider-console deployment handoff, then application-driven deployment only if verified.
- Phase 3: Fleet read/invoke for validated accounts; keep management links external.
- Phase 4: MDA beta adapter for allow-listed accounts only.
- Roll back an adapter by capability flag without deleting its source record; show it as temporarily unsupported and preserve exportable connection details.

## Executable acceptance scenarios

```gherkin
Scenario: Existing classic deployment becomes a verified source
  Given a test deployment URL, assistant ID, and authorized credential fixture
  When the user runs the connection probe
  Then Deep Work records each baseline capability independently
  And saves the source only after assistant read and invocation checks pass
  And the raw credential is absent from the AgentSource response

Scenario: MDA is unavailable and classic remains usable
  Given an organization without the accepted MDA beta capability
  When the user chooses to deploy the starter agent
  Then the wizard offers the classic LangSmith path
  And sends no request to an assumed deepagents endpoint
  And preserves all onboarding progress

Scenario: Unsupported deployment automation hands off safely
  Given SPIKE-DEPLOY-001 has not accepted public create/build contracts
  When a user chooses "Deploy with classic LangSmith"
  Then Deep Work opens the documented LangSmith deployment handoff
  And asks for the resulting deployment URL and assistant ID
  And does not emulate CLI upload calls

Scenario: A first non-coding task completes inside the onboarding target
  Given a fresh authenticated test account and a healthy classic source
  When the user accepts the starter research prompt
  Then a real task is created and reaches a terminal state
  And its trace link is present
  And the onboarding timing event records every stage without prompt or credential contents
```
