# F15 · Task-type templates

*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M1–M2 · Depth: implementation-ready*

Sources: [02 · architecture §2–§4](../02-architecture.md) · [08 · feature map (use-case guides, Profiles, Interpreters, Models rows)](../08-deepagents-feature-map.md) · [07 · org intelligence §Layer 4](../07-org-intelligence.md) · [research 02 · deepagents harness](../../research/02-deepagents-harness.md) · [research 01 · MDA & deployment](../../research/01-managed-deep-agents.md) · [research 10 · open-swe/Fleet](../../research/10-openswe-fleet.md) · [research 20 · MDA API](../../research/20-gapfill-mda-api.md) · [01 · vision](../01-vision.md) · [04 · roadmap](../04-roadmap.md) · [decision log](../decisions.md) · live docs.langchain.com (profiles / interpreters / assistants API pages), verified 2026-07-22 — cited inline where a fact comes only from there.

## 1. Scope

**Owned here.** The v1 template catalog — **Coding**, **Research**, **Writing** — as *data over one agent* (D-014): per-template prompt overlay, tool allowlist, middleware flags, sandbox on/off, rubric defaults, model defaults, `interrupt_on` defaults, plan-approval defaults, and HarnessProfile overlays. Plus the mechanics that make a template real: the template config schema, how template **assistants** are provisioned/versioned/reconciled per deployment, how the composer's template picker resolves to an assistant, per-task override precedence, Fleet-export round-trip of template-configured agents, and the beta-flag policy for the beta harness features templates lean on (Profiles, Interpreters, Rubrics).

**Not owned** (link, don't duplicate): agent composition, middleware implementation, and the tool-gating mechanism → [F14](./14-agent-package.md); rubric mechanics and the verification panel → [F16](./16-verification-and-rubrics.md); composer chrome and creation flow → [F08](./08-task-inbox.md) §3.5; thread rendering incl. interpreter code cards → [F09](./09-task-detail-and-streaming.md); sandboxes/environments → [F11](./11-execution-and-environments.md); GitHub flow and the auto-PR path → [F12](./12-github-and-git-flow.md); artifact/file viewing → [F13](./13-files-diff-and-review.md); the template gallery UI and config editor → [F17](./17-fleet-manager.md). **Data-analyst is v2** — the deepagents `text-to-sql-agent` shape with dbt/Postgres MCP connectors is designed in [F24](./24-org-intelligence-v2-v3.md) per [07 §Layer 4](../07-org-intelligence.md); this spec only reserves its template id and flags (§4) and does not spec it. Org-analyst/consolidation *schedule* templates are [F22](./22-org-intelligence-v1.md)/[F23](./23-org-intelligence-v1x-consolidation.md) territory.

**Design driver.** >90% of Cowork usage is non-coding ([02 §3](../02-architecture.md)); vision makes non-coding flows first-class v1 scope ([01](../01-vision.md)). Hence: Research and Writing ship **first** (M1, no sandbox — [04](../04-roadmap.md) M1), Coding lands M2, and non-coding outputs are real artifacts (report/document files in the thread filesystem, surfaced in the run panel's artifacts list → [F13](./13-files-diff-and-review.md)) — not chat transcripts.

## 2. Dependencies & seams

| Dependency / seam | Direction | Contract |
|---|---|---|
| D-014 | governs | Templates are assistant configs over **one** agent (`packages/agent`), never separate codebases; this spec must add zero template-specific code paths outside F14's declared gates |
| D-004 / D-005 / D-016 | governs | Runtime-agnostic agent (keeps Fleet-export compatibility, [02 §2](../02-architecture.md)); compose-don't-fork; templates select from the curated ~15 tools, never add ad-hoc ones |
| D-015 | consumes | Coding = thread-scoped sandbox + snapshot environments; non-sandbox templates ride the default StateBackend ([02 §4](../02-architecture.md)) |
| D-017 → [F16](./16-verification-and-rubrics.md) | seam | Each template ships `rubricDefault: RubricSpec \| null` (F16 §3.2 defines the seam; **this spec owns the final catalog values**, §3.2) |
| [F14](./14-agent-package.md) | consumes | The composed superset agent (middleware stack, subagents, `interrupt_on` union, curated tools) + the **template gate**: per-run tool-visibility filtering keyed on template context (mechanism owned by F14; requirement stated in §3.1) |
| [F08](./08-task-inbox.md) §3.5 | provides data | Template picker (segmented Research · Writing · Coding), per-template composer field defaults (plan-approval toggle, rubric prefill, environment/repo requirements), `task_type` thread-metadata stamp (F08 §4) |
| [F04](./04-sdk-and-agent-sources.md) | consumes | `assistantsCrud` capability per source (mda ✅ · deployment ✅ · fleet **read-only** · local ✅); provisioning degrades per §3.6 |
| [F11](./11-execution-and-environments.md) | seam | `environment` run-config key (absent ⇒ StateBackend path — F11 §4); coding template requires it in the composer |
| [F12](./12-github-and-git-flow.md) | seam | `commit_and_open_pr` tool + auto-draft-PR middleware are F12's; this spec only flags them on for Coding |
| [F09](./09-task-detail-and-streaming.md) | seam | Interpreter `eval` executions render as **collapsed code cards** in the thread ([08 Interpreters row](../08-deepagents-feature-map.md)); F15 declares the flag, F09 renders |
| [F06](./06-onboarding-and-deploy.md) / [F17](./17-fleet-manager.md) | provides | Provisioning step invoked by the deploy wizard; template gallery, version history + rollback UI |
| O-003 | risk | MDA beta gating of external data-plane calls also covers `POST /assistants` — resolved by M0 Spike 2 |

## 3. Design

### 3.1 What a template IS, mechanically

A template is **(a)** a catalog entry — declarative data + prompt files versioned in `packages/agent/templates/<id>/` — and **(b)** per deployment, an **assistant** on the one Deep Work graph, created via the standard assistants API (`POST /assistants` with `graph_id`, `name`, `metadata`, `context`) ([research 01 L15](../../research/01-managed-deep-agents.md); [assistants docs](https://docs.langchain.com/langsmith/assistants): one graph, many assistants, each a versioned configuration — no code change, no redeploy).

- **One agent, superset composition.** `packages/agent` composes the union once: all curated tools, all middleware (steering, reliability stack, auto-PR, RubricMiddleware, CodeInterpreterMiddleware where installed), all declarative subagents ([02 §3](../02-architecture.md)). The assistant's `context` (matching the agent's `context_schema` — author-controlled per [research 01 L9](../../research/01-managed-deep-agents.md)) carries the template payload (§4); F14's **template gate** filters the *model-visible* tool surface and toggles flagged middleware behavior per run from that context. Dynamic per-request tool filtering is established middleware behavior upstream (e.g. the LLM-tool-selector middleware); the exact F14 mechanism is its spec's contract — this spec only fixes the inputs (§4) and the observable outcomes (§7).
- **Prompts are files, parameters are config.** Each template's prompt overlay lives as `templates/<id>/prompt.md` in `packages/agent` (file-first, Context-Hub-visible/diffable, [02 §6](../02-architecture.md)); the assistant `context` references `template: <id>` + parameter overrides — never embedded prose. Consequence: prompt-text changes ride agent deploys; parameter changes ride assistant versions (§3.5).
- **The default assistant is not a template.** Every deployed graph gets a system default assistant (`metadata.created_by: system`); Deep Work leaves it untouched and creates managed template assistants alongside (metadata convention §4).

### 3.2 The v1 catalog

Prompt-overlay *shapes* come from the use-case-guide mapping ([08](../08-deepagents-feature-map.md): deep-research → Research, content-builder → Writing); tools from the curated set ([02 §3](../02-architecture.md), D-016). Rubric defaults finalize the [F16 §3.2](./16-verification-and-rubrics.md) proposal — **this table is the binding catalog wording**.

| | **Coding** (M2) | **Research** (M1) | **Writing** (M1) |
|---|---|---|---|
| Prompt overlay | Repo conventions, `AGENTS.md` injection expectation, branch/PR discipline, test-before-PR ([02 §3/§4](../02-architecture.md)) | Deep-research workflow: plan todos → save request to file → delegate to research subagent(s) → synthesize with consolidated numbered citations → write `/final_report.md` → verify coverage ([deep-research guide](https://docs.langchain.com/oss/python/deepagents/deep-research)) | Content-builder shape: brief → outline → draft to files → revise; no self-referential meta-commentary |
| Tools (Δ over built-ins: `write_todos`, fs suite, `task`) | + `execute` + `commit_and_open_pr` + `fetch_url` (docs lookup) | + `fetch_url` + `http_request`; **no** `execute`/PR tools | filesystem only — **no** web, `execute`, or PR tools |
| Sandbox | **on** — thread-scoped LangSmith sandbox; composer requires an environment ([F11](./11-execution-and-environments.md), D-015) | **off** — StateBackend (zero infra; files still visible in UI, [02 §4](../02-architecture.md)) | **off** — StateBackend |
| Middleware flags | auto-PR **on** ([F12](./12-github-and-git-flow.md)); interpreter **off, permanently** — sandboxes cover programmatic execution ([08 Interpreters row](../08-deepagents-feature-map.md)) | auto-PR off; interpreter flag present (PTC + dynamic subagents), **default off in v1** (§3.4) | auto-PR off; interpreter off |
| Subagents advertised | review specialization ([02 §3](../02-architecture.md)) + auto GP | research specialization (deep-research shape) + auto GP | auto GP only |
| Rubric default ([F16](./16-verification-and-rubrics.md)) | **off** (available; 1 pass if enabled) — tests/CI/diff already verify | **on**, 2 passes — claims cited, sub-questions answered, ≥2 sources for key claims, uncertainty stated | **on**, 2 passes — brief followed, structure present, consistent tone, no placeholders |
| Model default | `provider:model` string per template ([02 §3 Models](../02-architecture.md)); **values TBD → §9-7**, user-overridable per task | same | same |
| `interrupt_on` defaults | `commit_and_open_pr`: Ask (approve/edit/reject); `execute`: per-environment Auto/Ask via `when` predicate ([02 §3](../02-architecture.md)) | none (no gated tools present; `http_request` posture → §9-6); user-flagged MCP tools respected | none |
| Plan approval default (F08 toggle) | **on** (proposal) | off | off |
| Landed output → artifacts ([F13](./13-files-diff-and-review.md)) | draft PR + diff | `/final_report.md` + offloaded source files | document file(s) |

**Data-analyst (v2, not specced here):** reserved id `data-analyst`; shape per [07 §Layer 4](../07-org-intelligence.md) — `list_tables`/`get_schema`/`query_checker`/`execute_query` + `query-writing`/`schema-exploration` skills, read-only credentials, `interrupt_on` gating query execution, interpreter **on** (PTC + dynamic subagents) per [08](../08-deepagents-feature-map.md). Design and sequencing live in [F24](./24-org-intelligence-v2-v3.md).

### 3.3 HarnessProfile (beta) — model-agnosticism without per-model code

Profiles are the harness's per-model configuration bundles: `base_system_prompt`, `system_prompt_suffix`, tool-description overrides, `excluded_tools`, `excluded_middleware`, general-purpose-subagent edits — registered against `provider` or `provider:model` keys and applied automatically when the matching model is selected ([08 Profiles row](../08-deepagents-feature-map.md); [profiles docs](https://docs.langchain.com/oss/python/deepagents/profiles)).

- **Built-ins used as-is**: Anthropic / OpenAI / NVIDIA profiles ship in deepagents ([research 02 L19](../../research/02-deepagents-harness.md)); `packages/agent` registers nothing that duplicates them.
- **Templates ship overlays as YAML**: optional `templates/<id>/profiles/<key>.yaml` files in the declarative `HarnessProfileConfig` subset (`base_system_prompt`, `system_prompt_suffix`, `excluded_tools`, `excluded_middleware`, `general_purpose_subagent`, tool-description overrides), loaded at agent startup via `HarnessProfileConfig.from_dict` → `register_harness_profile` ([profiles docs — load from config files](https://docs.langchain.com/oss/python/deepagents/profiles#load-profiles-from-config-files)). **Runtime-only profile state (`extra_middleware`, class-form exclusions) is banned in template overlays** — upstream refuses to serialize it (`ValueError` on export), and it would break Fleet-export round-trip (§3.5). Enforced by a lint in F14's CI.
- Because profiles key on the **model**, not the template, a template overlay is namespaced by registration key and applies only when that model family is picked — so a template tuned suffix for OpenAI never leaks into Anthropic runs, and `packages/agent` contains zero `if provider == ...` branches (§7-8 greps for this). Merge order between a template overlay and a built-in profile matching the same model → §9-9.

### 3.4 CodeInterpreterMiddleware (beta, QuickJS) — per-template flags

Facts ([interpreters docs](https://docs.langchain.com/oss/python/deepagents/interpreters); [08 Interpreters row](../08-deepagents-feature-map.md)): the middleware adds an `eval` tool running JS in QuickJS (no host fs/network/shell/clock); **PTC is off until enabled** with an explicit tool allowlist under the `tools` namespace; **dynamic subagent dispatch via `task()` is on by default** when subagents exist (`subagents=False` disables); state persists per thread (`mode="thread"`); requires `langchain-quickjs>=0.2.0`, Python ≥3.11.

- **Template flags** (§4 schema): `interpreter.enabled`, `interpreter.ptcTools[]` (allowlist — read-side tools only: `fetch_url`, `read_file`, `glob`, `grep`), `interpreter.dynamicSubagents`.
- **Coding: off, permanently** — the sandbox already gives real programmatic execution; a second execution surface adds confusion, not capability ([08](../08-deepagents-feature-map.md): "Not in the default coding template").
- **Research (and v2 data-analyst): the intended beneficiaries** — PTC loops/retries/parallel batches over selected tools without model turns; dynamic subagents for code-driven fan-out/verification over many items, keeping intermediate results out of context. Per [08](../08-deepagents-feature-map.md) this is 🔜 flagged/experimental: v1 defaults **off**; the flag exists in the catalog from day one and flips per the beta policy below ([04 backlog](../04-roadmap.md): "interpreter/PTC templates hardening as the beta stabilizes").
- **Gating mechanics**: the middleware composes once in F14 (where installed); the template gate hides `eval` for templates with the flag off — hiding `eval` also removes the `task()` dynamic-dispatch surface, which lives inside interpreter code.
- **UI seam**: `eval` tool calls render as collapsed code cards (code + captured console output) in the thread — [F09](./09-task-detail-and-streaming.md) owns rendering.

**Beta-flag policy** (applies to Profiles, Interpreters, Rubrics, and future betas): (1) exact version pins + renovate grouping ([02 §8](../02-architecture.md)); (2) a beta feature enters a template only behind a catalog flag, default **off** — the single exception is RubricMiddleware, which is an explicit M2 exit line item ([04](../04-roadmap.md)) and D-017-mandated, so it ships pinned + golden-transcript-tested instead of dark; (3) the F02-style canary deployment tracking the 0.7-alpha/dev channel ([08 Changelog row](../08-deepagents-feature-map.md)) must be green on the feature before a default flips; (4) a flag flip is a catalog version bump → assistant reconcile (§3.5), never a hand-edit.

### 3.5 Versioning, migration, Fleet-export round-trip

**Provisioning (idempotent).** For each catalog template × deployment: derive a stable `assistant_id` = UUIDv5(deployment URL, template id); `POST /assistants` with that id, `graph_id: "agent"`, `if_exists: "do_nothing"`, name/description from the catalog, metadata per §4 ([create-assistant API](https://docs.langchain.com/langsmith/agent-server-api/assistants/create-assistant) supports client-supplied `assistant_id` + `if_exists`). Invoked by the F06 deploy wizard and re-runnable from F17.

**Update = new assistant version.** A catalog bump reconciles each **managed** template assistant via `PATCH /assistants/{id}` — which creates version N+1 and activates it. Critical platform rule: **updates replace, they never merge** — the reconciler must always send the *complete* context, built as: fresh catalog payload ⊕ preserved user-owned keys (diffed against the *previous catalog version's* payload so genuine user edits survive) ([configuration docs: "Updates require full configuration"](https://docs.langchain.com/langsmith/configuration-cloud)). Rollback = `POST /assistants/{id}/latest?version=N` ([set-latest API](https://docs.langchain.com/langsmith/agent-server-api/assistants/set-latest-assistant-version)); F17 surfaces version history (`POST /assistants/{id}/versions`) with a rollback action.

**What existing threads experience.** Threads reference the `assistant_id`; the next run on any thread uses the assistant's *active* version — old threads silently pick up template updates on their next turn (correct: bug-fixed prompts should apply). Whether an in-flight run pins the version it started with → §9-5. Prompt-file changes additionally require an agent redeploy (§3.1); the reconciler stamps `templateVersion` + `agentRevision` in assistant metadata so F17 can show drift ("assistant updated, deploy pending").

**Managed vs user-owned.** Only assistants with `metadata.deepwork_managed: "true"` are reconciled. "Duplicate as custom" (F17) clones a template into an unmanaged assistant (managed flag absent) that the reconciler never touches; the composer renders it under Custom (§3.6).

**Fleet-export round-trip (D-004 constraint; v1 release criterion 4, [04](../04-roadmap.md)).** The canonical import/export format is the Fleet-export deepagents project layout — `AGENTS.md`, `config.json`, `tools.json`, `subagents/`, `skills/` ([02 §6](../02-architecture.md); [research 10](../../research/10-openswe-fleet.md)). Round-trip holds because template deltas are **data**: prompt overlays are markdown files, tool allowlists/flags serialize into `config.json`/`tools.json`, profile overlays are the YAML-declarative subset only (§3.3), and the only code is `packages/agent` itself — shared by all templates, runtime-agnostic per D-004 (no backend/store/checkpointer in agent code). Export of a template-configured agent = project layout + the template's resolved config; import maps the same fields back onto a template assistant. CI proves it (§7-7): export → run as a plain deepagents project (fleet-export's generated REPL pattern, [research 10](../../research/10-openswe-fleet.md)) → re-import → deep-equal on the catalog payload.

### 3.6 Composer mapping & per-task overrides

**Picker → assistant.** The F08 composer's segmented template control resolves against the selected source: `POST /assistants/search` with `metadata: {deepwork_template: <id>}` ([search API](https://docs.langchain.com/langsmith/agent-server-api/assistants/search-assistants)) → use the managed assistant (active version). Degradation ladder: (a) source has `assistantsCrud` but no template assistants → composer offers one-click "Provision templates" (runs §3.5); (b) Fleet source (read-only CRUD, [F04 §3.1](./04-sdk-and-agent-sources.md)) → picker lists the source's *existing* assistants only, template control disabled with a link-out; (c) foreign/unmanaged assistant selected → template chip shows **Custom**, no template defaults applied, everything still runs (the inbox's foreign-thread rule, [F08 §4](./08-task-inbox.md)). The chosen `task_type` is stamped into thread metadata at creation (F08 §4 convention; tracing partitions per [02 §10](../02-architecture.md)).

**Per-task overrides ride the run, never mutate the assistant.** Composer-adjustable per task: model pick, rubric attach/edit (`RubricSpec` → [F16](./16-verification-and-rubrics.md)), environment ([F11](./11-execution-and-environments.md) key), plan-approval toggle. These are submitted as run-scoped config on run creation; precedence **run > assistant (template version) > catalog default**. The template payload channel is assistant/run `context` (matching `context_schema`); `config.configurable` is accepted for compatibility — note [F11](./11-execution-and-environments.md) currently specs `config.configurable.environment`; one canonical channel must be picked → §9-3.

## 4. Contracts

**`TemplateSpec`** — catalog format, versioned in `packages/agent/templates/` (source of truth), consumed by the provisioner (`packages/sdk`) and the composer:

```ts
type TemplateId = "coding" | "research" | "writing" | "data-analyst"; // data-analyst reserved, v2 (F24)
type TemplateSpec = {
  id: TemplateId;
  templateVersion: number;              // bumped on any field change; drives reconciliation
  name: string; description: string;
  promptFile: string;                   // templates/<id>/prompt.md (deployed with the agent)
  tools: string[];                      // allowlist over the curated set (D-016); F14 gate input
  sandbox: { enabled: boolean };        // enabled ⇒ composer requires environment (F11)
  middleware: {
    autoPr: boolean;                                                    // F12
    interpreter: { enabled: boolean; ptcTools: string[]; dynamicSubagents: boolean }; // §3.4
  };
  subagents: string[];                  // advertised declarative subagents (F14 catalog names)
  rubricDefault: RubricSpec | null;     // F16 §4 shape; §3.2 values
  modelDefault: string;                 // "provider:model" — value TBD §9-7
  interruptOnDefaults: Record<string, { allowedDecisions: string[] }>;  // compiled with `when` predicates by F14
  planApprovalDefault: boolean;
  profileOverlays: string[];            // templates/<id>/profiles/*.yaml — declarative subset only (§3.3)
};
```

**Assistant payload** (what provisioning writes): `graph_id: "agent"`; `name`/`description` from the spec; `context`: `{ template: TemplateId, templateVersion, taskType, tools, sandbox, middleware, rubricDefault, model, interruptOnDefaults, planApprovalDefault }` (keys mirror `TemplateSpec`, resolved); `metadata`: `{ deepwork_template: TemplateId, deepwork_template_version: string, deepwork_managed: "true" }`. Per-run overrides submit the same context keys run-scoped (§3.6). The `context_schema` in `packages/agent` typing this payload is an F14 contract; F15 owns the key names above.

**Provisioning API sequence** (per deployment; all standard assistants endpoints, available on mda/deployment/local tiers per [F04 §3.1](./04-sdk-and-agent-sources.md)): `search(metadata)` → `create(assistant_id=uuid5, if_exists=do_nothing)` → on catalog bump `patch(full context)` → `versions`/`set_latest` for history/rollback.

**Profile overlay YAML** — exactly the upstream `HarnessProfileConfig` shape ([docs](https://docs.langchain.com/oss/python/deepagents/profiles#load-profiles-from-config-files)); example ceiling of what a template may ship:

```yaml
# templates/research/profiles/openai.yaml — applies only when an openai:* model is selected
system_prompt_suffix: "Prefer parallel tool calls when gathering sources."
excluded_middleware: []          # extra_middleware / class-form entries are banned (§3.3)
```

## 5. Edge cases & failure modes

| Case | Behavior |
|---|---|
| Source has no template assistants (fresh/foreign deployment) | Composer degradation ladder §3.6 — never a dead picker; provisioning is one click where CRUD exists |
| Fleet source (CRUD read-only) | Existing assistants only + link-out; no silent write attempts ([F04](./04-sdk-and-agent-sources.md) capability flag) |
| Reconciler PATCH races a concurrent user edit | Full-config replace means last write wins; reconciler re-reads current context immediately before PATCH and aborts (surfacing a F17 conflict prompt) if `deepwork_template_version` metadata changed since read |
| User edited a managed assistant's context by hand (Studio/API) | Preserved-keys diff (§3.5) keeps their edits for non-catalog keys; catalog keys are overwritten on next bump — documented in F17 ("duplicate as custom to opt out") |
| Assistant deleted out-of-band | Deletion removes **all versions** ([configuration docs](https://docs.langchain.com/langsmith/configuration-cloud)); next provisioning run recreates at catalog defaults (stable UUIDv5 ⇒ same id; old threads reattach) |
| Coding template selected in M1 (no sandbox yet) | Picker gates Coding until M2 ([F08 §3.5](./08-task-inbox.md) already specs this); flag-driven, not build-driven |
| Interpreter flag on, `langchain-quickjs` not installed on deployment | Composition skips the middleware (F14); template gate treats `interpreter.enabled` as false; run proceeds; provisioning surfaces a warning in F17 |
| Sandbox template run on a deployment without sandbox config | `execute` absent from the composed surface (backend-dependent tool hiding is harness behavior, [overview docs](https://docs.langchain.com/oss/python/deepagents/overview)); composer blocks environment-less coding submits anyway (F08 validation) |
| Model override to a provider with no built-in or overlay profile | Runs on harness defaults — profiles are additive tuning, never load-bearing for correctness (§7-8 acceptance protects this) |
| Template overlay YAML fails validation at agent startup | Agent boots without the overlay + logs loudly; a bad overlay must never take the deployment down |
| Thread created under templateVersion N, catalog now N+2 | Next run uses active version (§3.5); task detail shows the assistant version in the provenance rail ([02 §10](../02-architecture.md)) |
| Export of an agent whose profile overlay carries runtime-only state | Cannot happen via CI lint (§3.3); upstream `ValueError` is the backstop |

## 6. Security & privacy

- **Templates are data, not code** (D-014): assistant context can select among F14's composed capabilities but cannot inject new tools, middleware, or prompts outside the deployed files — a compromised composer/API caller can at most re-enable tools already in the curated union for that agent. The gate's fail-mode must be *closed* (unknown template id ⇒ built-ins only, no `execute`/PR/web tools) — F14 requirement.
- **`interrupt_on` defaults are safety floors.** Per-task overrides may *tighten* (Auto→Ask) freely; *loosening* the Coding PR gate (`commit_and_open_pr` Ask→Auto) is an explicit per-agent setting in F17's Auto/Ask matrix, never a silent composer toggle ([02 §3](../02-architecture.md) HITL row).
- **Research egress**: `fetch_url`/`http_request` run in the deployment runtime (no sandbox, no egress proxy — the sandbox allow-list story in [F11](./11-execution-and-environments.md) does not apply). Fetched web content is untrusted input; prompt-injection posture per [02 §10](../02-architecture.md) (untrusted-content boundaries) applies to rendering, and the write-capable `http_request` default posture is §9-6. Writing's filesystem-only toolset makes it the zero-egress template by construction.
- **Interpreter boundary**: QuickJS code has no host filesystem/network/shell access; only the PTC allowlist and (if enabled) `task()` cross the boundary ([interpreters docs](https://docs.langchain.com/oss/python/deepagents/interpreters)) — keep `ptcTools` read-only (§3.4) so PTC can never mint side effects that `interrupt_on` would otherwise gate.
- **No new secrets or storage**: provisioning uses the caller's existing auth planes (F05); template payloads contain no credentials; zero-secrets-in-sandbox (D-015) untouched.

## 7. Acceptance criteria

1. Provisioning a fresh `langgraph dev` + MDA deployment creates exactly three managed assistants with the §4 metadata and stable UUIDv5 ids; re-running is a no-op (`if_exists`).
2. A Research task created via the composer completes on M1 infra with **zero** sandbox API calls; transcript shows `fetch_url`/`http_request` available and `execute`/`commit_and_open_pr` absent from the model's tool list; `/final_report.md` appears in the run panel artifacts list (F13 seam).
3. A Writing task's transcript shows filesystem/todo/task tools only — no web or execution tools visible in any model request.
4. A Coding task (M2) provisions a thread sandbox, fires the `commit_and_open_pr` interrupt with decisions approve/edit/reject, and lands a draft PR via the auto-PR path (F11/F12 integration).
5. Composer prefills per template: rubric defaults exactly per §3.2 (Research/Writing on with 2 passes, Coding off), plan-approval defaults, environment field required only for Coding.
6. Catalog `templateVersion` bump → reconcile produces assistant version N+1 on all managed assistants and never touches unmanaged clones; an existing thread's next run uses the new version; `set_latest` rollback restores prior behavior — all verified against `langgraph dev`.
7. Fleet-export round-trip: export a template-configured agent to the deepagents project layout, run it locally as plain deepagents, re-import; catalog payload survives deep-equal (v1 release criterion 4, [04](../04-roadmap.md)).
8. With an OpenAI-family model selected on the Research template, the shipped overlay's suffix is present in the traced system prompt; with Anthropic selected it is absent; `grep -r "provider ==" packages/agent` (and equivalents) returns nothing.
9. Interpreter flag off ⇒ no `eval` tool in Research transcripts. Flag on (canary deployment) ⇒ `eval` runs render as collapsed code cards (F09 fixture) and PTC calls are limited to the declared allowlist.
10. Selecting a foreign (unmanaged) assistant shows the Custom chip, applies no template defaults, and the run completes without template-gate errors (fail-closed to built-ins verified by transcript).

## 8. Task breakdown

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | `TemplateSpec` schema + catalog data files (`templates/{research,writing,coding}/`) incl. prompt overlays and §3.2 values; `data-analyst` id reserved | F14 layout exists (M1 v0) | Schema validated in CI; F16 seam values match §3.2; prompts reviewed against the deep-research/content-builder shapes |
| 2 | Joint contract with F14: `context_schema` keys (§4) + template gate requirements (tool visibility, fail-closed, interpreter/auto-PR toggles) | 1 | Written contract in both specs' §4; gate behavior demonstrated on `langgraph dev` for research vs writing tool surfaces |
| 3 | Provisioner in `packages/sdk` (search/create/patch/versions/set_latest, UUIDv5 ids, full-config reconcile with preserved-keys diff, managed-flag guard) | 1; F04 client | AC-1, AC-6 green against `langgraph dev`; race-abort path unit-tested |
| 4 | Research template end-to-end on M1 (prompt + research subagent advertised + rubric default wired via F16 task 2) | 1–3 | AC-2, AC-5 (research rows); dogfood release gate ([04 M1](../04-roadmap.md)) |
| 5 | Writing template end-to-end on M1 | 1–3 | AC-3, AC-5 (writing rows) |
| 6 | Composer resolution + override plumbing with F08 (picker→assistant ladder §3.6, run-scoped overrides, precedence, Custom chip) | 3; F08 task 9 | AC-5, AC-10; degradation ladder covered by fixtures incl. Fleet read-only source |
| 7 | Profile overlay loading (YAML → `HarnessProfileConfig` → registration at startup) + banned-state lint + boot-resilience | 1 | AC-8; malformed-overlay boot test |
| 8 | Coding template (M2): sandbox flag, auto-PR on, `interrupt_on` defaults compiled with F14, composer env/repo requirements | 1–3; F11 task 1, F12 | AC-4; loosening-guard (§6) verified |
| 9 | Interpreter flag path on the canary deployment: gate wiring, PTC allowlist, F09 code-card fixture | 2; F14 interpreter composition | AC-9; flip criteria documented per beta policy (§3.4) |
| 10 | Fleet-export round-trip CI test | 3, 4, 7 | AC-7 in CI; failures block release per v1 criterion 4 |

## 9. Open questions

1. **Per-run model override mechanism**: does `create_deep_agent` support context-driven model selection natively, or does F14 need a small model-resolution middleware (wrap-model-call) reading the template/run context? Never guessed here; F14 task-1-class probe resolves. Affects nothing in §4's key names.
2. **Template gate mechanism** (F14): dynamic per-request tool filtering — confirm interaction with prompt caching (does a per-template tool list fragment cache keys?) and with middleware-appended tool guidance in the system prompt.
3. **`context` vs `config.configurable`**: assistants docs push `context` (static context matching `context_schema`); [F11](./11-execution-and-environments.md) specs `config.configurable.environment`. Pick one canonical run-override channel and align both specs (decision-log entry).
4. **MDA beta**: are external `POST /assistants` / `PATCH` calls accepted at MDA deployment URLs during beta, or gated with the rest of the data plane (O-003)? Spike 2 must exercise the provisioning sequence specifically.
5. **Version pinning of in-flight runs**: does a run started under assistant version N finish under N if N+1 activates mid-run? Determines whether reconciliation needs a quiesce step.
6. **`http_request` posture in Research**: it can perform writes (POST) from the deployment runtime with no sandbox egress controls — default Auto (current §3.2), Ask, or a read-only-methods variant? Needs Tom's call + F17 Auto/Ask surfacing.
7. **Model defaults**: per-template `provider:model` values (and whether Fast/Pro-tier naming à la Fleet is worth mirroring, [research 10](../../research/10-openswe-fleet.md)) — Tom's pick; cost guidance blocked on O-005.
8. **Plan-approval defaults**: ratify Coding=on / Research=off / Writing=off (§3.2 proposal).
9. **Profile merge order**: when a template overlay and a built-in provider profile both match the selected model, which wins per field? Upstream documents merge semantics — pin the answer during task 7 and record it.
10. **Interpreter flip criterion**: measurable definition of "beta stabilizes" (N green canary weeks? upstream GA?) and the `langchain-quickjs` pin policy.
11. **Managed-assistant edit rights on shared/team deployments**: should the reconciler respect MDA identity ownership (`metadata.owner`) or a workspace-admin convention before overwriting managed assistants?

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Beta churn — Profiles/Interpreters/Rubrics APIs shift weekly ([research 02](../../research/02-deepagents-harness.md)) | High | Med | Beta-flag policy §3.4; pins + canary; catalog/data seam isolates the UI; upstream issues per D-005 (no forks) |
| Full-config PATCH clobbers user context edits | Med | Med | Preserved-keys diff + pre-PATCH re-read/abort (§5); "duplicate as custom" escape hatch |
| Template gate proves infeasible per-run → pressure to fork per-template agents (violates D-014) | Low | High | Two graduated fallbacks before any fork: profile-level `excluded_tools` keyed by model is not template-aware, but per-template *assistants on separate graph aliases of the same code* keeps one codebase; decision-log entry required either way |
| MDA gating blocks assistant provisioning (O-003 / §9-4) | Med | Med | `langgraph dev` + classic deployment cover every AC; MDA is additive ([02 §12](../02-architecture.md)); link-out degradation already specced |
| Research `http_request` misuse (unsandboxed writes) | Med | Med | §9-6 escalated for ratification before M1 dogfood; untrusted-content rendering boundaries regardless |
| Rubric-on defaults inflate token costs on every non-coding task | Med | Med | Low cap (2), F16 cost copy + per-pass trace links; defaults editable per task; measured via F22 metadata partitions |
| Template sprawl (requests for many niche templates) erodes the curated catalog | Med | Low-Med | D-020 cut line: v1 catalog is fixed; new templates need a roadmap PR; custom assistants absorb one-off needs |
| Fleet-export drift as upstream layout evolves | Low | Med | Round-trip test in CI (task 10) fails loudly; format tracked as the canonical bridge ([02 §6](../02-architecture.md)) |
