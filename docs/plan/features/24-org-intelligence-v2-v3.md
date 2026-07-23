# F24 · Org intelligence v2–v3 (Layers 3–5)

*Deep Work feature spec · 2026-07-22 · Status: draft · Horizon: v2–v3 · Depth: design-complete*

Sources: [07 · Org intelligence §3–§4](../07-org-intelligence.md) · [research 15 · org intelligence](../../research/15-org-intelligence.md) · [research 09 · openwiki/opengpts](../../research/09-openwiki-opengpts.md) · [02 · Architecture §3/§5/§6/§10](../02-architecture.md) · [04 · Roadmap post-v1](../04-roadmap.md) · [decisions](../decisions.md) (D-005, D-015, D-016, D-018; P-005; O-008/O-009/O-010) · neighbors [F22](./22-org-intelligence-v1.md) · [F23](./23-org-intelligence-v1x-consolidation.md)

## 1. Scope

The top three rungs of the org-intelligence ladder ([07 §3](../07-org-intelligence.md)), each gated by its own demand signal (§8):

- **Layer 3 · Org knowledge base (v2)** — adopt **OKF** (Open Knowledge Format, Google's open spec, 2026-06-12: markdown bundles + typed YAML frontmatter + link-based relationships; v0.1) as the org-brain format and **openwiki** (MIT, LangChain-staff-maintained, deepagents-JS-based CLI) as the generator. Pipeline: connectors (Gmail, Notion hosted MCP, GitHub, web; upstream also ships X/HN) → OKF bundle in Context Hub/git → scheduled refresh → read-only agent mount → human diff review. Deep Work builds the **wiki browse/review surface** and the **sandboxed-scheduler auth design** (O-010) — nothing else; missing connectors are contributed upstream, never forked (D-005).
- **Layer 4 · Structured data plane (v2)** — MCP-first (D-016) access to the org's databases and metrics: **dbt-mcp** flagship (Semantic Layer governed metrics beat raw text-to-SQL), operational DBs via **Supabase official MCP / `mcp-server-pg` / Postgres MCP Pro**, plus the **data-analyst task template**. Deep Work builds the template and the credential UX only — **zero integrations in-house**.
- **Layer 5 · Temporal graph (v3, opt-in)** — **Graphiti** (`graphiti-core`, Apache-2.0) on a user-provisioned Neo4j/FalkorDB/Neptune, with a shipped Pydantic **ontology-as-code preset**. **Deferred entirely if Layers 1–3 satisfy demand** ([07 §1](../07-org-intelligence.md) principle 4).

Out of scope (neighbors): Layers 0–1 templates, tracing conventions, Insights glue → [F22](./22-org-intelligence-v1.md); the Layer 2 consolidation agent and the propose/review/commit loop mechanics (Hub webhook consumer, approvals payload, merge semantics) → [F23](./23-org-intelligence-v1x-consolidation.md) — L3 review **rides F23's rails**, it does not redefine them; approvals rendering → [F10](./10-approvals-inbox.md); diff/file-viewer components → [F13](./13-files-diff-and-review.md); MCP connector CRUD, Agent Auth provider config, Auto/Ask matrix → [F17](./17-fleet-manager.md); schedule surface/CronEditor → [F18](./18-schedules-and-activity.md); sandbox/environment machinery → [F11](./11-execution-and-environments.md); template catalog plumbing → [F15](./15-task-templates.md) (see [catalog](README.md)).

## 2. Dependencies & seams

| Dependency / seam | Direction | What crosses it |
|---|---|---|
| [F23](./23-org-intelligence-v1x-consolidation.md) review loop | consumes | Proposal→`context_hub.commit.created.v1` (HMAC) webhook→approvals-diff→merge/reject pipeline ([research 15](../../research/15-org-intelligence.md)); L3 adds a `wiki_refresh` proposal kind; Hub write scopes = O-008 |
| [F22](./22-org-intelligence-v1.md) Layer 0/1 | consumes | `org-memory/` Hub repo + read-only `/memories/org` mount (writes runtime-denied — [research 15](../../research/15-org-intelligence.md)); digests as L5 episode source; tracing metadata on refresh runs |
| openwiki CLI (pinned release) | consumes | One-shot generation runs, OKF middleware, git-hash skip-if-unchanged, CI auto-PR templates ([research 09](../../research/09-openwiki-opengpts.md)). Consumed as a **CLI artifact in a sandbox** — never composed into Python-first `packages/agent` (D-008); Node ≥22 required in the environment snapshot |
| [F11](./11-execution-and-environments.md) + [F18](./18-schedules-and-activity.md) | consumes | `wiki-refresh` schedule template → task → sandbox run of openwiki; egress allow-list for connector hosts; D-015 zero-secrets rule constrains connector auth (O-010, §3.1) |
| [F17](./17-fleet-manager.md) MCP registry + Agent Auth | consumes | `/v1/deepagents/mcp-servers` CRUD registers dbt-mcp / DB MCPs / Arcade-Composio gateways / Graphiti MCP; `langchain-auth` (beta) brokers per-user tokens — never stored by Deep Work ([02 §5](../02-architecture.md)) |
| [F15](./15-task-templates.md) + `packages/agent` (see [catalog](README.md)) | provides | `data-analyst` template joins coding/research/writing (D-014: assistant config, not a codebase) |
| [F10](./10-approvals-inbox.md) / [F13](./13-files-diff-and-review.md) | consumes | Wiki-refresh proposals render as F13 diffs inside F10 cards; wiki browse reuses F13 file-viewer components |
| `apps/server` (P-005 → [F28](./28-backend-glue-service.md)) | consumes | Hosts the F23 webhook consumer L3 reuses; no new L4/L5 server state (D-003: no Deep Work store) |
| Graphiti + `langchain-neo4j` (v3) | consumes | `graphiti-core` on org-provisioned Neo4j/FalkorDB/Neptune (Kuzu deprecated); in-repo MCP server; `langchain-neo4j` 0.10.0 owns `LLMGraphTransformer` for extraction-from-text ([research 15](../../research/15-org-intelligence.md)) |

## 3. Design

### 3.1 Layer 3 — org knowledge base

**Storage & mount (working assumption):** the wiki lives at `org-memory/wiki/**` in the existing Hub repo — it inherits the read-only `/memories/org` mount, runtime write-denial, and F23's review loop for free. Agents navigate it with `grep`/`read_file` over cold files on demand; the typed frontmatter is the "poor man's ontology" — **no new query infrastructure** (no vector store, no graph, no search service). Bundle-size limits → §9-Q3.

**Refresh paths, primary first:**

1. **Deep Work-native (sandboxed scheduler):** an F18 schedule template fires a `wiki-refresh` task; the thread sandbox (F11 environment with Node ≥22 + pinned openwiki) runs openwiki one-shot per connector set; openwiki's git-hash gate skips unchanged sources; the resulting OKF delta is committed as a **proposal** via the Hub API (staging mechanism owned by F23; write scopes O-008). Approve = merge to live `wiki/`; reject = discarded, live wiki untouched.
2. **Self-managed CI (degraded/DIY):** openwiki's shipped GitHub-Actions/GitLab/Bitbucket auto-PR templates run in the org's own CI against a git repo synced to Hub; review happens in the forge. Deep Work only renders the bundle. Zero Deep Work infra; documented, not built.

**Connector auth in the sandbox (O-010 — design sketch, not resolved):** D-015 forbids secrets inside the box, but openwiki's local shape is "MCP stdio with credential-isolated child envs" ([research 09](../../research/09-openwiki-opengpts.md)) — a direct tension. Candidate resolution per connector: Notion hosted MCP = remote HTTPS bearer via sandbox auth-proxy header-injection rules; GitHub = [F12](./12-github-and-git-flow.md) installation-token callback; web = unauthenticated; Gmail = Agent Auth-brokered per-user Google token fetched by a proxy callback at request time (the genuinely new design work). Until O-010 closes, connectors that only work as stdio-with-local-env are excluded from the native path.

**Wiki browse surface** (`/wiki` in `apps/web`): tree + page view rendered from the bundle (F13 viewer components); type facets and backlinks derived from frontmatter/links; per-page provenance rail (source connector, source URL, last-refresh commit, Hub file version — [02 §10](../02-architecture.md) provenance-everywhere). **Review takeover**: pending `wiki_refresh` proposals open the F13 diff with approve/reject via the F10 card. States: *loading* skeleton tree; *empty* teaches "connect a source and run the first generation" (link to schedule template); *error* full-bleed retry; *degraded* — stale banner when the last refresh failed or a proposal has been pending > refresh interval, with the live wiki still browsable.

**OKF instability fallback (O-009):** the surface treats the bundle as *markdown tree + optional typing*. Frontmatter types enrich navigation; their absence never breaks rendering. If OKF v0.2 breaks v0.1, plain markdown + frontmatter degrades gracefully — parsing of OKF-specific structures is isolated behind one adapter module.

### 3.2 Layer 4 — structured data plane

- **Warehouse/metrics — flagship:** **dbt-mcp** (dbt Labs official), exposing Semantic Layer metric queries + model discovery. Governed metrics are preferred over raw text-to-SQL for anything a metric covers; the template's skills encode this preference. Exact dbt-mcp tool names/config pinned at implementation from docs.getdbt.com (§9-Q4).
- **Operational DBs:** Supabase official MCP, `mcp-server-pg`, Postgres MCP Pro — all registered through the F17 MCP registry (they are connectors, not integrations we build). The **archived Anthropic reference Postgres server is never used or recommended — unpatched SQL injection** (D-018).
- **Data-analyst task template** — the deepagents `examples/text-to-sql-agent` shape **verbatim** ([research 15](../../research/15-org-intelligence.md)): tools `list_tables` / `get_schema` / `query_checker` / `execute_query` + skills `query-writing` / `schema-exploration`. Two connection modes, one contract (§4.2): *MCP mode* mounts a registered server's tools (query-executing tools flagged into `interrupt_on` — [02 §3](../02-architecture.md): any MCP tool the user flags); *DSN mode* uses the example's hand-rolled tools over a driver against a **read-only role**, DSN held as a deployment env var, never by Deep Work. Defense in depth: `interrupt_on` gates `execute_query` (approve/edit/reject in the F10 inbox); read-only credentials are the hard backstop — `query_checker` is advisory only.
- **Credential UX:** per-user tool credentials broker through **LangSmith Agent Auth** (`langchain-auth`, beta, works self-hosted); tokens fetched at runtime, never stored by Deep Work ([02 §5](../02-architecture.md)). Long-tail SaaS = **user-supplied Arcade/Composio MCP gateways** — both platforms proprietary, both *just MCP servers to us*; no SDK dependency (`langchain-arcade` is formally unmaintained; Arcade went MCP-first — [research 15](../../research/15-org-intelligence.md)).

### 3.3 Layer 5 — temporal graph (opt-in)

- **Engine:** Graphiti on a graph DB the **org provisions** (Neo4j/FalkorDB/Neptune) — Deep Work hosts nothing (principle 2, [07 §1](../07-org-intelligence.md)). Bi-temporal edges (event time vs ingestion time; invalidation instead of deletion) + hybrid retrieval come from Graphiti itself.
- **Ontology-as-code preset** shipped in `packages/agent` (§4.3): Pydantic entity types `Person, Team, Project, System, Decision, Policy` and edge types `OWNS, DECIDED, DEPENDS_ON`, passed on `add_episode`; orgs extend by subclassing — this is the ecosystem's working ontology pattern; **RDF/OWL is explicitly out** (D-018).
- **Ingestion:** a `graph-ingest` schedule template turns task completions, F22 digests, and OKF wiki pages into Graphiti episodes (idempotent episode ids derived from thread/commit ids, §5). `langchain-neo4j`'s `LLMGraphTransformer` covers extraction-from-text where Graphiti's own extraction needs help.
- **Access:** Graphiti's in-repo MCP server, registered as **just another connector** in the F17 registry — no bespoke query surface, no graph UI in Deep Work.
- **Degradation:** graph absent/unreachable ⇒ graph tools absent from configs; agents fall back to wiki grep + traces. Nothing in the task loop may hard-depend on L5.

### 3.4 Explicit rejections (D-018) — restated so they are not relitigated

| Rejected | Reason ([07 §4](../07-org-intelligence.md), [research 15](../../research/15-org-intelligence.md)) |
|---|---|
| langmem as foundation | Pre-1.0 (0.0.30), slow-moving, not absorbed into langgraph; file-based deepagents memory is the blessed pattern |
| Mem0 | Opaque-store philosophy conflicts with principle 1 — knowledge is reviewable files, not vectors |
| Zep CE | Dead (Apr 2025); its OSS successor *is* Graphiti |
| langchain-kuzu | Stale; Kuzu deprecated in Graphiti too |
| RDF/OWL | No practical tooling anywhere in this ecosystem; working patterns are Pydantic types + typed frontmatter |
| In-house connector platform | Violates consume-don't-build (D-005) and MCP-first (D-016); Deep Work builds zero integrations |
| Archived Anthropic Postgres MCP server | Unpatched SQL-injection issue; archived upstream |

## 4. Contracts

### 4.1 Wiki page + proposal (L3; illustrative — field set pinned against OKF v0.1 at implementation, O-009)

```yaml
# org-memory/wiki/systems/billing-service.md — YAML frontmatter (typed = navigable)
title: Billing service
type: system            # Deep Work convention aligns with the L5 preset: person|team|project|system|decision|policy
owner: [[teams/payments]]        # link-based relationship (OKF)
sources: [{connector: github, ref: "acme/billing#README"}]
refreshed: 2026-11-03            # last generation touching this page
```

`wiki_refresh` proposal (F23 payload, new `kind`): `{kind: "wiki_refresh", hub_repo, base_commit, proposal_ref, stats: {added, changed, removed}, run_id}` — rendered as an F13 diff; `removed > threshold` triggers the mass-deletion guard (§5).

### 4.2 Data-analyst template config (L4; assistant config per D-014)

```yaml
template: data-analyst
connection:
  kind: mcp | dsn
  mcp_server_id: <F17 registry id>     # dbt-mcp, Supabase MCP, mcp-server-pg, Postgres MCP Pro, Arcade/Composio gateway
  dsn_env: DATABASE_URL_RO             # dsn mode: deployment env var; read-only role REQUIRED (§6)
limits: {row_cap: 1000, statement_timeout_s: 30}
interrupt_on:                          # compiled by F17's Auto/Ask matrix
  execute_query: {allowed_decisions: [approve, edit, reject]}
  # + every flagged query-executing MCP tool in mcp mode
skills: [query-writing, schema-exploration]   # verbatim from the deepagents example
```

### 4.3 Graphiti ontology preset (L5; `packages/agent/graph/ontology.py`)

```python
class Person(BaseModel): ...   # Team, Project, System, Decision, Policy — entity types
class OWNS(BaseModel): ...     # DECIDED, DEPENDS_ON — edge types
PRESET = Ontology(entities=[Person, Team, Project, System, Decision, Policy],
                  edges=[OWNS, DECIDED, DEPENDS_ON])   # passed to add_episode; orgs extend by subclassing
```

Graph config (org-supplied, stored as deployment config, never Deep Work-side): `{backend: neo4j|falkordb|neptune, uri_env, mcp_server_id}`.

## 5. Edge cases & failure modes

- **Refresh lands while a proposal is pending** — new run supersedes: the pending proposal is marked stale in F10 (regenerated against the same base); never two live proposals per wiki.
- **Mass deletion in a refresh** (source connector broke, auth expired mid-crawl): proposal auto-flagged when `removed` exceeds a threshold; approvals card leads with the warning; partial-crawl results are proposed, never auto-merged (review gate is the control).
- **Connector auth expiry mid-run**: openwiki run fails per-connector; the task surfaces which connector failed; other connectors' output still proposed.
- **OKF v0.1 → v0.2 break** (O-009): adapter module quarantines the breakage; browse degrades to plain markdown tree; generation pins the openwiki release until the adapter is updated.
- **`query_checker` passes a mutating statement**: expected — it is advisory; the read-only role rejects at the DB and the error ToolMessage feeds back ([02 §3](../02-architecture.md) reliability stack). A write *succeeding* means the org supplied a writable credential — surfaced in template docs and the connect flow warning.
- **Metric answer vs raw-SQL answer disagree**: template skill prefers the Semantic Layer number and says why (governed definitions); the task cites which path produced the answer.
- **Graph DB down / not provisioned**: L5 tools absent; no task fails for lack of the graph (§3.3 degradation rule).
- **Duplicate episode ingestion** (re-fired schedule, retried run): episode ids derived from `thread_id`/commit sha make `add_episode` idempotent; corrections use Graphiti's bi-temporal invalidation, never deletes.
- **Pure-OSS tier**: crons are absent ([02 §2](../02-architecture.md)) — native refresh degrades to the CI path (§3.1-2); the browse surface works everywhere.

## 6. Security & privacy

- **Injection via generated knowledge**: wiki content derives from emails and external docs — a prompt-injection carrier once mounted into agent context. Controls: human review gate on every merge (nothing enters `wiki/` unreviewed); read-only mount (runtime write-denial already exists to "prevent prompt injection via shared state" — [research 15](../../research/15-org-intelligence.md)); the openwiki generation run itself is sandboxed with egress allow-listed to declared connector hosts and write access only to its output dir (openwiki's own write-restricted backend pattern). Residual risk stays in §10.
- **PII**: Gmail-derived pages can carry personal data into an org-visible wiki. The review diff is the checkpoint; per-connector include/exclude scoping is configured at schedule setup; upstream redaction options unknown → §9-Q6.
- **Zero secrets in sandboxes** (D-015) holds for L3 refresh runs — the O-010 design must pass this bar, fail-closed.
- **DB credentials**: read-only roles mandated and documented as the hard control (`interrupt_on` is UX, not security); DSNs live in deployment env vars, MCP secrets are write-only fields in the F17 registry, Agent Auth tokens never transit Deep Work ([F05 §3.5](./05-auth-and-identity.md)).
- **Graph data** is derived org knowledge living in the org's own DB — org security perimeter, org retention rules; Deep Work stores nothing (D-003).
- **Access scope**: wiki and graph are workspace-scoped like org memory; multi-workspace iteration follows O-011.

## 7. Acceptance criteria

1. **L3**: connect ≥1 connector → first openwiki generation → proposal diff in the approvals inbox → approve → pages browsable at `/wiki` with type facets, backlinks, and per-page provenance; agents cite wiki paths in answers. Rejecting a refresh leaves the live wiki byte-identical.
2. **L3 fallback**: a bundle with unknown/absent frontmatter types renders as a plain markdown tree — no crash, no blocked review (O-009 drill).
3. **L4**: a metric question over dbt-mcp is answered via the Semantic Layer with zero raw SQL; over a Postgres MCP, `execute_query` interrupts, an edited query runs, and a mutating statement fails at the DB with the error surfaced. No DB credential is ever client-readable or Deep Work-stored (code audit, mirroring v1 criterion 5).
4. **L5**: with the shipped preset on an org-provisioned graph, ingested episodes from completed tasks answer "who decided X, when, and what changed since?" through Graphiti MCP tools with temporal validity attached; removing the graph config leaves every non-graph task functional.
5. **Rejections hold**: §3.4 list present in contributor docs; no dependency on any rejected component appears in the lockfiles.

## 8. Adoption triggers & sequencing

Doctrine: **each layer earns its way in** ([07 §1](../07-org-intelligence.md) principle 4 generalized) — a layer starts only when its demand signal shows up in real usage, never on the calendar. High-level order only (design-complete: no task breakdown).

| Layer | Demand signal that starts it | Prereqs | High-level order |
|---|---|---|---|
| **L3** (v2) | Insights categories / F22 digests show recurring agent questions unanswerable from curated `org-memory/`; admins hand-pasting Notion/Gmail content into memory | F23 review loop live (v1.x); O-008 + O-010 resolved | OKF adapter + browse surface (read-only, over a hand-made bundle) → manual one-shot openwiki run → review-loop wiring (`wiki_refresh` kind) → sandboxed scheduled refresh → upstream connector contributions as gaps appear |
| **L4** (v2, independent of L3) | Users dispatch data/metric questions as tasks; orgs with a dbt Semantic Layer ask for governed answers | F17 MCP registry + Agent Auth surfacing (M3); F15 template plumbing | dbt-mcp connect flow + data-analyst template (MCP mode, interrupts wired) → DSN mode + read-only-role docs → operational-DB MCP options → Arcade/Composio gateway documentation |
| **L5** (v3) | Cross-entity, time-aware questions that grep-over-wiki demonstrably fails ("who decided X, when, what changed since?") — observed in L3 usage, not hypothesized | L3 in production (episode source); org willing to provision a graph DB | Ontology preset + graph config → `graph-ingest` schedule template → Graphiti MCP registration + template exposure. **If the signal never arrives, L5 never starts** |

Within v2, L3 and L4 ship independently and in either order per org; neither blocks the other.

## 9. Open questions

| # | Question | Path |
|---|---|---|
| Q1 | O-009 — OKF v0.1→v0.2 stability; which frontmatter/bundle structures are load-bearing for the browse surface | Watch upstream; adapter isolates; pin at implementation |
| Q2 | O-010 — sandboxed openwiki connector auth: per-connector shapes (esp. Gmail/Google OAuth via proxy callback + Agent Auth) under D-015 zero-secrets | v2 design task before L3 native refresh; CI path is the interim |
| Q3 | Context Hub repo size/file-count limits vs realistic wiki bundles; if exceeded, wiki moves to a git repo with Hub holding an index | Probe with a large generated bundle at L3 start |
| Q4 | Exact dbt-mcp tool names/config, and which dbt plans expose the Semantic Layer through it | docs.getdbt.com + a connect probe at L4 start |
| Q5 | Hub staging mechanism for proposals (branch? prefix path?) — owned by F23 (O-008); L3 inherits whatever it lands | F23 resolution |
| Q6 | openwiki upstream: PII redaction/scoping options per connector; non-interactive headless flags sufficient for cron use | Upstream issue if missing (D-005: gaps go upstream) |
| Q7 | Graphiti MCP server transport/auth requirements when registered via `/v1/deepagents/mcp-servers` | v3 probe |
| Q8 | Episode-id convention robust across thread forks/re-runs (branching creates sibling threads) | Design with L5 ingest template |

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| OKF spec churn (weeks old) | High | Low-Med | O-009 fallback: markdown+frontmatter degrades gracefully; single adapter module; pinned openwiki release |
| openwiki API/CLI churn (young, daily commits) | Med | Low | Consumed as a pinned CLI artifact in a sandbox — no library coupling; upstream relationship (D-005) |
| O-010 unsolvable within D-015 for some connector | Med | Med | Per-connector opt-in; CI refresh path needs no Deep Work sandbox; worst case a connector stays CI-only |
| Injection via reviewed-but-missed wiki content | Med | Med | Review gate + read-only mount + provenance links for spot-checks; residual risk documented honestly |
| Orgs supply writable DB creds despite docs | Med | High | Connect-flow warning + a template smoke test that attempts a write and expects failure |
| L5 built ahead of demand (cost without value) | Med | Med | §8 trigger discipline: defer entirely absent the signal; opt-in, org-provisioned |
| Proprietary drift (Arcade/Composio gateways change terms) | Low | Low | They are user-supplied MCP endpoints; no SDK or platform dependency to unwind |
