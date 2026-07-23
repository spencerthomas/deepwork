# Decision log

*Deep Work planning docs · started 2026-07-22. The single source of truth for decisions and open questions across the strategic plan ([01–08](./)) and the [feature specs](features/README.md). Specs cite IDs from this log.*

Status values: **decided** · **provisional** (working assumption — specs are written against it, pending Tom's explicit ratification) · **open** (unresolved question with a named resolution path).

Process: new decisions land here first (or are recorded here when made during spec review); ratifying a provisional item flips its status and updates any contradicting spec in the same commit; each feature spec's §9 open questions roll up into the Open questions table as they are triaged.

## Decided

| ID | Decision | Source |
|---|---|---|
| D-001 | Product name **Deep Work**; repo `spencerthomas/deepwork`; no `lang*` in name/domain/npm scope; nominative fair use + non-affiliation disclaimer; no LangChain logo assets or commercial fonts in-repo | [05](05-oss-setup.md) |
| D-002 | License **MIT** (matches langchain-ai org norm; adoption-friendly), NOTICE-style attribution in README; DCO not CLA | [05](05-oss-setup.md) |
| D-003 | Deep Work is a **wrapper over the LangChain platform** — no backend/database of its own in v1; the user's LangSmith org is the source of truth | [01](01-vision.md), [02](02-architecture.md) |
| D-004 | **Managed Deep Agents is the primary runtime target**; classic LangSmith Deployment + `langgraph dev` are the fully-public fallback tiers; agent definition stays runtime-agnostic (no backend/store/checkpointer in agent code) | [02 §2](02-architecture.md) |
| D-005 | **Compose on the deepagents harness, never fork it**; OSS-first dependency policy — no forks, no vendoring, gaps go upstream | [02 §3/§8](02-architecture.md) |
| D-006 | Mobile is **PWA-first**; native Expo app is post-v1 (architecture keeps the door open — `packages/sdk` + tokens reuse) | [01](01-vision.md), [03 §6](03-ui-spec.md) |
| D-007 | **GitHub only** in v1 (no GitLab — open-swe precedent); GitHub App with zero-token-in-sandbox proxy pattern | [01](01-vision.md), [02 §4](02-architecture.md) |
| D-008 | `packages/agent` is **Python-first** (mirroring open-swe v2), riding in the pnpm monorepo as a uv-managed workspace | [02 §11](02-architecture.md), [05](05-oss-setup.md) |
| D-009 | Design language is a deliberate **docs.langchain.com carbon copy** via swappable tokens; Inter/IBM Plex Mono as font stand-ins | [03 §1](03-ui-spec.md) |
| D-010 | Approvals build **natively on the v1 HITL contract** (`HITLRequest` → `decisions`, `respond()/respondAll()`); never the legacy agent-inbox resume path | [03 §3.3](03-ui-spec.md), research 13/21 |
| D-011 | Casing normalized **once at the SDK boundary** — wire snake_case → camelCase canonical, single documented exception (`reviewConfigs` inner keys read both ways) | [02 §7](02-architecture.md), [03 §5](03-ui-spec.md) |
| D-012 | The v0 frontend concept (`spencerthomas/deep-work-frontend`) is **adopted as the seed of `apps/web`** — rendering layer kept, data layer built underneath | [06](06-frontend-implementation.md) |
| D-013 | Deep Work builds **no CLI** — `dcode` is the local companion (sandbox-id handoff, shared AGENTS.md/skills/plugins conventions) | [02 §9](02-architecture.md) |
| D-014 | Task-type templates (coding / research / writing) are **assistant configs over one agent**, not separate codebases | [02 §3](02-architecture.md) |
| D-015 | Sandboxes are **thread-scoped** (one per thread, `idle_ttl`, auto-recreate); environments = named snapshots + `setup.sh`; **zero secrets inside the sandbox** (auth-proxy callback pattern) | [02 §4](02-architecture.md) |
| D-016 | Curated **~15 task tools** (tool curation beats tool count); MCP-first connector strategy | [02 §3/§6](02-architecture.md) |
| D-017 | Verification engine is the harness's **`RubricMiddleware`** (≥0.6.5) — an include, not new machinery; dcode's goal lifecycle is the UX reference layered on later | [08](08-deepagents-feature-map.md) |
| D-018 | Org-intelligence stack selections: **OKF + openwiki** (L3), **dbt-mcp / Supabase MCP / mcp-server-pg** (L4), **Graphiti** with Pydantic ontology-as-code (L5, opt-in). Rejected: langmem, Mem0, Zep CE, langchain-kuzu, RDF/OWL, any in-house connector platform, the archived Anthropic Postgres MCP server | [07 §3–4](07-org-intelligence.md) |
| D-019 | Staging: **build to v1 first, then announce** (Codex-CLI pattern); repo public from day one with "not accepting feature PRs yet" posture until v1 | [04](04-roadmap.md), [05](05-oss-setup.md) |
| D-020 | Scope-creep contract: **the cut line in [01](01-vision.md) is binding** — anything not listed needs a roadmap PR | [04](04-roadmap.md) |
| D-021 | Feature-spec layer lives in **`docs/plan/features/`** (one spec per feature area, fine-grained 28 specs); v1 specs implementation-ready incl. task breakdowns, post-v1 specs design-complete (no task breakdowns); drafted in full then reviewed in batches | this session, 2026-07-22 |
| D-022 | **Frontend = Next.js (React)** for web; desktop = Tauri v2 wrapping the same app; mobile = PWA (per D-006). Justified by stack, not preference: `@langchain/react` `useStream` is React-only, and all first-party ecosystem UIs (agent-chat-ui, OAP, open-swe v2 dashboard) are Next.js | Tom delegated frontend choice, 2026-07-22 |

## Provisional (pending ratification)

Working assumptions; specs are written against them and mark the dependency. Flip to Decided (or reverse them) during batch review. P-001–P-004 originate from [06 §4](06-frontend-implementation.md).

| ID | Working assumption | Consequence if reversed |
|---|---|---|
| P-001 | Monorepo is canonical; the v0 repo stays a design sandbox (one-way manual porting, never merged blind) | Two-way sync process + lockfile/drift management needed |
| P-002 | IA consolidates to **6 tabs** — Config folds into Settings + Agent detail; Observability slims to counts + LangSmith deep links | App-shell nav, sidebar contents, and route map change (F07) |
| P-003 | Browser/computer-use card ships **feature-flagged off**; terminal pane ships **read-only** in v1 | Interactive terminal adds real M2 scope; browser card needs a backing capability that doesn't exist in the harness today |
| P-004 | The ~1,100-line mock dataset is kept **permanently** as fixtures powering demo mode + tests/Storybook | No zero-credential demo mode; weaker OSS onboarding; test fixtures built separately |
| P-005 | **Backend/glue = Python FastAPI service (`apps/server`)** in the uv workspace shared with `packages/agent` — owns OAuth token exchange, key/streaming proxy (incl. `trusted_backend` forwarding), GitHub App token minting + sandbox auth-proxy callback, push fan-out, and future webhook consumers (L2 review loop, Insights glue). Next.js keeps only browser-flow pages. Supersedes the "Next.js server routes as glue" description in [02 §1/§11](02-architecture.md), [05](05-oss-setup.md), and [06 Phase B](06-frontend-implementation.md) — amend those docs when ratified. Rationale: Tom's Python lean + concentrating all LangSmith-platform logic in the agent's language (`deepagents`, `langsmith`, `langchain-auth`, `mda` are Python-first); trade-off is two deployables (mitigated: docker-compose, and demo mode needs zero server) | Reverting to Next-routes glue is cheap **before M0 only**; after M0 it's a migration |

Note on repo state (2026-07-22): the monorepo is **not scaffolded yet** and the v0 frontend has **not been imported** — this repo contains docs + the `packages/ui` token seed only. P-001/D-012 describe the intended relationship once the import happens (an M0 task), not current state.

## Open questions

| ID | Question | Resolution path | Blocks |
|---|---|---|---|
| O-001 | LangSmith OAuth `scopes_supported` reality — does the OAuth 2.1 server cover control plane + data plane (`*.langgraph.app`) bearer acceptance? | M0 Spike 1 (probe + memo) | F05 auth posture |
| O-002 | OAuth-first vs key-first at launch | Output of Spike 1 memo | F05, F06 onboarding order |
| O-003 | MDA thread/run invocation acceptance for non-beta orgs (`deployment_type: managed_deep_agent`) | M0 Spike 2 with the beta account; deploy wizard detects + falls back | F04, F06 |
| O-004 | Does Fleet self-config-via-chat work over the public run API? (would enable richer Fleet management without CRUD APIs) | Probe post-M3 | F17 (nice-to-have) |
| O-005 | MDA quotas/pricing at GA | External — LangChain publishes | cost guidance docs only |
| O-006 | Does LangChain want Deep Work upstreamed? | External conversation | naming/branding timeline, not architecture |
| O-007 | Insights beta REST: can full report payloads (categories, exec summaries) be read back via API, or UI-only? | M1 probe with the beta account | F22 Layer 1 provisioning |
| O-008 | Context Hub **write** scopes under "Sign in with LangSmith" OAuth (the L2 review loop commits via the Hub API) | Extends Spike 1 | F23 |
| O-009 | OKF v0.1 → v0.2 stability | Watch upstream; markdown+frontmatter degrades gracefully | F24 |
| O-010 | openwiki-in-sandbox connector auth design | v2 design task | F24 |
| O-011 | Multi-workspace orgs: Insights/automations are per-workspace — does the "whole org" view need org-scoped iteration? | Iterate under org-scoped keys at M3 | F22 |

Spec-level §9 questions roll up here as they are triaged during batch review.
