---
feature_id: DW-AGENT-005
title: Tools, connectors, permissions, skills, memory, and subagents
release: v1
status: canonical-spec
decision_status: blocked-on-spikes
owners: [agent, api, web, security]
surfaces: [agent-detail, workspace-settings]
runtime_scopes: [classic, mda, fleet]
source_refs: [SRC-LC, SRC-DW, SRC-FE]
dependencies: [DW-AGENT-003, DW-HITL-001]
contract_gates: [SPIKE-MCP-001, SPIKE-CONTEXT-001, SPIKE-MDA-001, SPIKE-FLEET-001]
last_reviewed: 2026-07-23
---

# Tools, connectors, permissions, skills, memory, and subagents

## User outcome

An authorized agent author can understand and constrain what an agent may do, which workspace or user credentials it may reference, when a human decision is required, what reusable instructions it loads, what memory it can read or propose, and how it delegates. A reviewer can distinguish configured intent from runtime-enforced capability before deployment.

## Evidence and confidence

| Claim | Evidence | Classification | Planning consequence |
|---|---|---|---|
| The prototype includes Tools, Permissions, Memory, Subagents, Connectors, Plugins, and Skills sections. | `SRC-FE`, `FE-C08`, `FE-C09`, `FE-C11`, `FE-C12`, `FE-C18`–`FE-C20` | Direct UI/code evidence, mostly simulated | Preserve user intent but rebuild around real ownership and enforcement. |
| Deep Agents supports tool schemas, `interrupt_on`, subagents, skills/memory patterns, and MCP-related integrations. | `SRC-LC` | Documented at feature level; versions and runtime availability vary | Pin the Python package and validate exact project/runtime representation. |
| MDA Context Hub and arbitrary connector routes have the same ownership/API as classic. | Prior plan assumption | Contradicted or unknown | Detect ownership/capability; never invent connector routes. |
| Fleet supports configuration mutation. | Prior plan assumption | Unknown | Fleet is read/invoke-only after its spike; no configuration save. |
| An `Auto`/`Ask` label alone guarantees a tool cannot bypass policy. | Prototype semantics | Contradicted by boundary differences | Show enforcement coverage and keep filesystem, shell, MCP, and custom-tool boundaries explicit. |

Exact tool policy compilation, Context Hub ownership, remote MCP transport/auth, and memory persistence require the pinned-package/live-contract fixtures in `SPIKE-MCP-001` and `SPIKE-CONTEXT-001`. This proposed plan is not implementation-ready until each editable surface has an enforcement test.

## Scope, ownership, and non-goals

| Area | Canonical owner | v1 scope |
|---|---|---|
| Built-in/authored tool declaration | Agent project draft | Name, source, input schema, risk, runtime availability, and verified policy binding. |
| MCP server definition | Workspace/project according to accepted transport contract | Documented remote transports only; endpoint, server metadata, and credential reference. |
| Connector account | Workspace or actor credential broker | Connect, reauthenticate, revoke, inspect granted identity/scopes, and bind to an agent. |
| Tool HITL policy | Agent project draft | Compile only verified `interrupt_on` actions/decisions; preserve exact runtime semantics. |
| Filesystem policy | Agent/environment draft | Ordered path rules with explicit coverage; never presented as shell/MCP/custom-tool control. |
| Skills | Versioned agent project or verified Context Hub owner | Browse, diff, validate, and version `SKILL.md`-style content with provenance. |
| Plugins | Workspace catalog/project manifest | Deferred beyond baseline v1; no opaque executable install/build. |
| User memory | Actor scope | Read/edit only where a verified backend and retention model exist. |
| Organization memory | Workspace review system | Runtime read-only; changes enter the proposal/review flow in `DW-OPS-003`. |
| Subagents | Agent project draft | Declarative identity, purpose, instructions, model reference, tools, concurrency/depth/budget limits, and delegation boundary. |

The Python agent package owns portable declarations and validators. FastAPI/PostgreSQL owns accounts/bindings, authorization, review records, audit, and credential references. The TypeScript SDK/Next.js/Tauri surfaces configuration. The runtime owns actual enforcement and source-native memory; Deep Work records the proof used to claim parity.

Non-goals are an arbitrary code/plugin marketplace, local secret display, connector implementation via inferred MDA routes, Fleet mutation, universal Context Hub write ownership, policy claims beyond enforced boundaries, direct organization-memory writes by agents, unrestricted MCP endpoints, or opaque subagent graphs.

## Primary journeys

### Connect and bind a tool

1. A workspace administrator connects a documented connector or MCP server through the server-side broker.
2. Deep Work shows requested identity/scopes, credential owner, expiry, verified transport, and discovered schemas; no secret is returned.
3. An agent author binds selected tools to a draft and chooses a supported human-review policy based on risk and runtime enforcement.
4. Validate checks credential health, schema version, target capability, policy compilation, and least-privilege warnings.
5. The author reviews the semantic diff and deploys explicitly through `DW-AGENT-003`.

### Configure a skill, memory policy, and subagent

1. The author adds a versioned skill with source/provenance and reviews untrusted content before enabling it.
2. They select which verified user/agent memory scope may be read and whether the agent may submit organization-memory proposals.
3. They define a subagent purpose, limits, tools, model reference, and delegation rules.
4. Static validation rejects cycles, ambiguous names, unavailable tools, excessive depth/concurrency, and privilege escalation relative to the parent.
5. Deployment and later task detail preserve which version and policy executed.

### Revoke or recover a connector

1. Revocation disables future token use immediately at the broker.
2. Affected agents, schedules, and drafts show a scoped degraded state while retaining declarations.
3. Reauthentication produces a new credential reference/version and requires revalidation before future deploy/invoke.

## Complete state matrix

| State | Required behavior |
|---|---|
| Loading catalog/bindings | Preserve section structure and draft state; do not flash tools as absent. |
| Empty tool catalog | Explain package/source requirements and safe authored-tool path; no fake examples. |
| No connector accounts | Show administrator setup path and ownership implications. |
| Connected/healthy | Show account identity, scopes, owner scope, expiry, discovered tools, and revoke action. |
| OAuth/API auth pending | Show resumable server-owned state and expiry; never poll or store verifier secrets in browser persistence. |
| Auth denied/cancelled | Return to disconnected state without creating a credential binding. |
| Credential expired/revoked | Disable dependent invocation, preserve project declaration, and offer authorized reauthentication. |
| Schema discovery running | Keep tool disabled for Auto and deployment until a complete verified schema arrives. |
| Schema absent/changed | Mark binding stale; require review and revalidation; never retain unsafe Auto silently. |
| Tool unsupported by runtime | Show source/package requirement and portable preservation policy; block target deploy if required. |
| Permission policy valid | State exactly which tool/action is covered and what decisions are supported. |
| Policy conflict/ambiguous rule | Show evaluation order/first match and block deploy until deterministic. |
| High-risk tool set to Auto | Default blocked or require explicit risk acknowledgement only if accepted policy permits; always audit. |
| Filesystem policy configured | Display path order plus a permanent notice that shell/MCP/custom tools need separate controls. |
| Skill valid | Show version, source, checksum, trust/provenance, and included files. |
| Skill untrusted/invalid | Render safely, block enable/deploy, and identify violated limits. |
| Plugin entry | Read-only deferred status; no Install/Build mutation. |
| Memory backend unavailable | Explain scope unavailable and prevent claims of persistence. |
| Org-memory proposal pending | Runtime continues reading last approved version; show diff/reviewer state. |
| Context Hub ownership unknown | Read-only or absent until the spike proves owner and write semantics. |
| Subagent graph valid | Show reachable graph, inherited limits, and effective tool ceiling. |
| Subagent cycle/limit/privilege error | Block deploy with node/edge-specific remediation. |
| Fleet-bound agent | Read-only export/deep link after spike; no fake Save or connector mutation. |
| MDA capability absent | Preserve portable draft/export and offer official CLI/source-native guidance only. |
| Offline | Allow read of cached non-sensitive manifests; connection, discovery, validation, and deployment disabled. |
| Reconnecting/stale | Recheck credential/schema/capability versions before enabling dependent actions. |
| Permission revoked mid-edit | Preserve non-secret draft, reject mutation, refresh role, and identify affected sections. |
| Mobile | Use grouped labelled policies and graph summaries; complex skill file editing may hand off with a durable link, not an inert editor. |

## Interfaces and state ownership

The proposed `/api/v1` application contract separates workspace connector-account queries/mutations, safe MCP/schema discovery, agent-draft tool bindings, permission policy validation, skill content/version operations, memory policy/proposals, and subagent validation. Exact resource paths remain API-review outputs. OAuth callbacks and secret exchange terminate at the FastAPI service/credential broker, not Next.js client code or Tauri webview.

Required normalized records include `ConnectorAccount`, `CredentialRef`, `ToolDescriptor` with source/schema/risk/provenance, `ToolBinding`, `PolicyRule` with enforcement boundary and verified decision set, `SkillRevision`, `MemoryBinding/Proposal`, and `SubagentDefinition/GraphValidation`. All source-native fields are retained with source/adapter version.

PostgreSQL owns non-secret accounts, bindings, draft policies, skill metadata/revisions, memory proposals, subagent graphs, validation evidence, and audit events. The secret broker owns tokens/keys. Approved object storage may own versioned skill files. Runtime/Context Hub owns effective runtime memory and tool execution state according to accepted contracts.

## Runtime capability and fallback rules

- Classic is editable only for tool, HITL, connector, skill, memory, and subagent declarations that round-trip through the pinned Python project and verified runtime fixture.
- MDA configuration is shown only when beta capability and ownership are detected; deployment remains CLI-first and no arbitrary connector/custom route is called.
- Fleet remains read/invoke-only after `SPIKE-FLEET-001`; configuration is never inferred from readable fields.
- `interrupt_on` policy preserves the exact runtime action request/review config/decision semantics owned by `DW-HITL-001`; unsupported decisions are not offered.
- If schema discovery fails, high-risk tools default unavailable, not Auto.
- If Context Hub ownership is unknown, Deep Work offers portable file export/read-only provenance rather than writes.
- Missing capability never disables unrelated safe tools or other source adapters.

## Persistence, security, and privacy

Connector endpoints use the same SSRF protections as source registration plus transport-specific allowlists, redirect controls, DNS revalidation, timeouts, response-size limits, and content-type validation. Tool schemas, descriptions, outputs, skill files, connector metadata, and memory proposals are untrusted content and are escaped/sanitized without executing embedded instructions, HTML, links, or code.

Credentials are encrypted and brokered server-side, least-privileged, revocable, scope-visible, and excluded from exports/logs/analytics. Bindings reference credential IDs, never secret values. High-risk policy changes, connector lifecycle actions, organization-memory reviews, and subagent privilege changes are actor-authorized, reauthenticated where required, idempotent, and audited.

Filesystem rules cannot imply control of shell, MCP, or custom tools. Subagents may not exceed the parent’s effective tool/credential/memory permissions. Skills and plugins cannot introduce undeclared executable files. Organization memory has a separate review-authorized write path and runtime read-only mount.

## Responsive and accessible behavior

Tool and connector lists use semantic headings/tables with text risk labels, scope descriptions, and keyboard-operable selection. Policy builders expose evaluation order, coverage boundary, and reorder controls with announcements. Graphs have an equivalent hierarchical list and error summary. Skill diffs use non-color markers and plain-text fallback. Mobile groups account, tool, policy, and trust information without horizontal clipping; destructive revoke and Auto-risk decisions require clear consequence copy. All flows support 320 CSS px, 200% zoom, reduced motion, and focus recovery.

## Metrics and guardrails

- 100% of enabled external tools have a current authorized credential reference, verified schema, and target capability.
- 100% of high-risk permission changes, connector revocations, and org-memory merges create attributable audit events.
- Zero credential values reach client persistence, project exports, logs, analytics, skills, or memory.
- Zero direct runtime-agent writes to approved organization memory.
- 100% of deployed subagent graphs pass cycle, depth, concurrency, and effective-privilege validation.
- Guardrail: policy UI never claims coverage outside the exact verified enforcement boundary.

## Dependencies and readiness gates

Depends on `DW-AGENT-003`, `DW-HITL-001`, `DW-OPS-003`, credential broker/security foundation, the pinned Python agent schema, and source capability manifests. Readiness requires accepted fixtures for tool/HITL compilation, MCP transport/auth and schema discovery, Context Hub ownership, memory persistence, skill packaging, connector revocation, and subagent limits. Unresolved MDA/Fleet contracts keep their sections gated.

## Rollout and rollback

1. Ship read-only fixture catalogs and risk/ownership displays.
2. Enable classic built-in tool bindings and Ask policies against pinned test agents.
3. Enable connector accounts and remote MCP types one accepted transport at a time.
4. Enable skills, verified memory policies, and subagents independently with per-capability flags.
5. Add MDA read/configuration behavior only after beta ownership fixtures; keep Fleet read-only after its spike.

Rollback revokes or disables the affected binding/capability, prevents new deploy/invoke use, retains non-secret declarations and audit history, and falls back to export/source-native management. Connector rollback can sever credential access immediately without deleting agent drafts.

## Executable acceptance scenarios

1. **Connector to approval:** Given a verified classic MCP fixture, when an administrator connects an account and an author binds a high-risk tool with Ask, validates, deploys, and invokes it, then the exact ordered HITL decision flow runs and no credential reaches the client.
2. **Revocation propagation:** Given one credential bound to two agents and a schedule, when it is revoked, then dependent actions disable, declarations persist, audit records identify impact, and unrelated tools remain usable.
3. **Schema drift:** Given a tool schema changes after deployment, when re-probed, then the binding becomes stale, Auto is not retained silently, and redeploy requires review.
4. **Boundary truth:** Given filesystem allow/deny/interrupt rules and a separately configured shell tool, when the policy summary renders, then it explicitly shows that filesystem rules do not govern shell/MCP/custom-tool execution.
5. **Organization memory:** Given a runtime agent proposes a memory change, when one item is accepted and one rejected, then only the reviewed item enters the next approved version and the runtime never writes directly.
6. **Subagent safety:** Given cyclic, over-depth, over-concurrency, and child-privilege-escalation fixtures, when validation runs, then deployment is blocked with node-specific errors.
7. **MDA/Fleet boundaries:** Given an MDA beta source and an unaccepted Fleet mutation contract, when configuration opens, then MDA uses only accepted capabilities/CLI handoff and Fleet offers no Save or CRUD request.
8. **Offline/mobile:** Given cached connector metadata on a narrow offline client, when opened, then identity/scope/freshness remain readable, mutations are disabled, and reconnect revalidates before enabling tools.
9. **Malicious content:** Given tool/skill/schema strings containing scripts, prompt injection, oversized content, and unsafe links, when displayed and exported, then content is inert, bounded, and no unapproved request or execution occurs.
