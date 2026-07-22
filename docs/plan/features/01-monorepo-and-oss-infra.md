# F01 · Monorepo & OSS infrastructure

*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M0 · Depth: implementation-ready*

Sources: [05 · OSS setup](../05-oss-setup.md) · [04 · Roadmap](../04-roadmap.md) (M0, M4, v1 criteria) · [02 · Architecture](../02-architecture.md) (§8, §11) · [06 · Frontend implementation](../06-frontend-implementation.md) (Phase A) · [research 07 · OSS v1 setup](../../research/07-oss-v1-setup.md) · [research 05 · Cross-platform arch](../../research/05-crossplatform-arch.md) · [research 10 · open-swe/Fleet](../../research/10-openswe-fleet.md)

Stack corrections applied throughout: frontend is Next.js (D-022); the server-side glue (OAuth callbacks, key proxy, GitHub-token proxy-callback, push fan-out) is a **Python FastAPI service `apps/server`** in the uv workspace shared with `packages/agent` (P-005, provisional). Where [02](../02-architecture.md) §1/§11 and [05](../05-oss-setup.md) say "Next.js server routes", P-005 supersedes. Every place this spec relies on that is marked *(P-005)*.

## 1. Scope

### In scope

- Greenfield scaffold of the `spencerthomas/deepwork` monorepo: pnpm 10 + Turborepo + changesets; workspaces `apps/{web,desktop,mobile,server}` + `packages/{agent,sdk,ui}`; pnpm catalogs for shared dependencies.
- Python-in-monorepo mechanics: one uv workspace covering `packages/agent` **and** `apps/server` *(P-005)*; ruff + pytest; Turborepo task wrappers so `turbo run lint|test` spans JS and Python (open-swe v2 precedent: Python agent + TS dashboard in one repo, [research 10](../../research/10-openswe-fleet.md)).
- Toolchain pins: lint/format choice (recommendation below), semantic PR titles with per-package scopes, all GitHub Actions pinned to SHAs.
- CI: Node 22/24 matrix, format → lint → typecheck → test → build; Python jobs (ruff, pytest, `langgraph dev` contract tests owned by [F02](./02-m0-spikes.md)); Vercel Git-integration previews for `apps/web`.
- Renovate/dependabot policy (weekly, `@langchain/*` grouped) and the scaffold-time version pins from [05](../05-oss-setup.md).
- Releases: changesets + `changelog-github` + npm provenance; the published-vs-app-only split.
- Community files (staged v1 set), the "not accepting feature PRs yet" posture, licensing/trademark hygiene (MIT + NOTICE block, non-affiliation disclaimer, no-LangChain-assets audit).
- One-time import of the v0 frontend concept as the `apps/web` seed — the *scaffold* portion only: import, rename, lockfile regeneration, strict TS, remove `ignoreBuildErrors` ([06](../06-frontend-implementation.md) Phase A; P-001/D-012).

### Out of scope

- Everything the imported `apps/web` *does* after import — token consolidation into `packages/ui`, data layer, screens: P-001/D-012 territory, see the [feature catalog](./README.md).
- The M0 spikes themselves (OAuth probe, MDA loop, stream-contract golden transcripts): [F02](./02-m0-spikes.md). This spec only provides the CI slots they run in.
- Any `apps/server` route behavior (OAuth, key proxy, GitHub token callback, push fan-out) — other specs per the catalog; here only the FastAPI skeleton, tests harness, and CI.
- Agent composition in `packages/agent` (middleware, tools, templates), `packages/sdk` design, `packages/ui` component build-out.
- Tauri/PWA implementation (roadmap M4); this spec only reserves the workspace directories.
- Docs site tooling (Mintlify is explicitly post-v1, [05](../05-oss-setup.md) §Docs).

## 2. Dependencies & seams

| Direction | Spec | What crosses the seam |
|---|---|---|
| provides → | [F02 · M0 spikes](./02-m0-spikes.md) | Working `uv` workspace + pytest harness + CI job slot for the `langgraph dev` golden-transcript contract tests (Spike 3); `packages/agent` dir that F02's `mda init/dev/deploy` loop (Spike 2) must keep valid as an `mda` project root |
| needs ← | [F02 · M0 spikes](./02-m0-spikes.md) | Confirmation that monorepo metadata inside `packages/agent` (pyproject/tests) does not break `mda deploy` compilation into `.mda/build` ([research 07](../../research/07-oss-v1-setup.md)) |
| provides → | apps/web spec (P-001/D-012, see [catalog](./README.md)) | Imported, renamed, strict-TS `apps/web` seed with regenerated lockfile and CI wiring; `lib/data.ts` kept intact for the fixtures move ([06](../06-frontend-implementation.md) Phase A) |
| provides → | server-glue specs *(P-005)* (see [catalog](./README.md)) | `apps/server` FastAPI skeleton inside the uv workspace, ruff/pytest/CI wiring; no routes |
| provides → | all specs | Workspace layout, catalogs/pins, CI gates, release pipeline, community-file posture, PR conventions |
| depends on | P-005 (provisional) | If glue reverts to Next.js server routes, delete `apps/server` and its CI job; nothing else in this spec changes |
| depends on | D-022 | `apps/web` is Next.js (the imported concept is Next 16.2.6, [06](../06-frontend-implementation.md) §1) |

## 3. Design

**Shape.** One pnpm workspace, one uv workspace, one task graph. JS packages are first-class pnpm workspace members; the two Python projects ride along as non-JS workspace members with thin `package.json` wrappers whose scripts shell out to `uv run …`, so Turborepo remains the single task runner and cache ([05](../05-oss-setup.md) §Repo structure). This mirrors open-swe v2's Python-agent/TS-dashboard pairing ([research 10](../../research/10-openswe-fleet.md)).

**Layout** ([05](../05-oss-setup.md), [02 §11](../02-architecture.md), amended per P-005):

```
deepwork/
  apps/
    web/        # Next.js 16 App Router (Turbopack) — UI only; no server glue (P-005)
    desktop/    # Tauri v2 shell (M4; placeholder at M0)
    mobile/     # PWA assets/config v1 (M4; placeholder at M0); Expo post-v1
    server/     # Python FastAPI glue: OAuth, key-proxy, gh-token callback, push (P-005)
  packages/
    agent/      # deepagents project — MUST remain a valid `mda` project root
    sdk/        # TS: agent-source registry, control-plane client, stream adapters, types
    ui/         # tokens.css + tailwind preset (already committed) + components later
  docs/         # plan/ design/ research/ (already committed)
  .github/workflows/
```

A useful side effect of P-005: with no server routes in `apps/web`, the Next app can satisfy Tauri v2's static-export requirement without a Node sidecar ([research 05](../../research/05-crossplatform-arch.md)) — record this as a constraint the desktop spec inherits.

**Python mechanics.** Root `pyproject.toml` declares a uv workspace with members `packages/agent` and `apps/server`; single `uv.lock` at the root; shared ruff + pytest config at the root. Python ≥3.11 (deepagents floor, [05](../05-oss-setup.md)). `packages/agent`'s wrapper scripts also expose `dev` → `langgraph dev` / `mda dev` for F02. Turborepo tasks for Python declare `inputs` (`pyproject.toml`, `uv.lock`, `**/*.py`) so caching is correct.

**Lint/format recommendation: biome.** [05](../05-oss-setup.md) leaves "biome (or oxlint/oxfmt to mirror deepagentsjs)" open; [06](../06-frontend-implementation.md) Phase A already assumes biome. Recommendation: **biome** — one tool for format+lint (oxlint/oxfmt is two), and Phase A hygiene work is specced against it. Trade-off: deepagentsjs uses oxlint/oxfmt ([research 07](../../research/07-oss-v1-setup.md)), so we diverge from the org we hope adopts the repo — accepted; a later mechanical switch is cheap. Ratify in §9-Q1.

**PR discipline.** `amannn/action-semantic-pull-request` with per-package scopes (`web`, `desktop`, `mobile`, `server`, `agent`, `sdk`, `ui`, `docs`, `ci`), SHA-pinned like every other action (deepagentsjs pattern, [research 07](../../research/07-oss-v1-setup.md)). Squash-merge so PR titles become commit history. DCO per [05](../05-oss-setup.md) community list; no CLA unless LangChain adoption requires one.

**CI** (per [05](../05-oss-setup.md) §Toolchain):

| Job | Matrix | Steps |
|---|---|---|
| js | Node 22, 24 | format-check → lint → typecheck → test → build (all via `turbo run`, cached) |
| python | single (Python 3.11 floor) | `uv sync` → ruff check + format-check → pytest (`packages/agent` + `apps/server`) |
| contract | single | `langgraph dev` golden-transcript tests against `packages/agent` — test content owned by [F02](./02-m0-spikes.md) Spike 3; this spec provides the job |
| pr-lint | — | semantic PR title |

Vercel previews come from the Vercel Git integration, **not** Actions (open-agent-platform precedent, [research 07](../../research/07-oss-v1-setup.md)) — no Vercel tokens in CI. `apps/server` has *no* preview/deploy story in any source doc — §9-Q4.

**Dependency updates.** Weekly Renovate or dependabot with `@langchain/*` grouped — v1-line SDKs release weekly; policy is pinned-but-fresh ([05](../05-oss-setup.md), [02 §8](../02-architecture.md)). Lean Renovate for richer grouping rules; deepagentsjs precedent is dependabot ([research 07](../../research/07-oss-v1-setup.md)) — §9-Q2. The chosen bot must also cover `pyproject.toml`/`uv.lock`; verify at scaffold time. `managed-deepagents` tracks the **dev channel** (0.4.0-dev) deliberately ([05](../05-oss-setup.md)); exclude it from auto-bumping and track via the F02 canary instead ([04](../04-roadmap.md) risk table).

**Releases.** changesets + `changelog-github`, published via `changesets/action` (v1.9.0, SHA-pinned) on push to `main`, `NPM_CONFIG_PROVENANCE=true`, workflow permissions `contents: write / pull-requests: write / id-token: write` (deepagentsjs release.yml pattern, [research 07](../../research/07-oss-v1-setup.md)). Published to npm: `@deepwork/ui` (name already seeded in [packages/ui/README](../../../packages/ui/README.md)) and the SDK package (proposed `@deepwork/sdk` — same scope; confirm §9-Q3). App-only, never published: `apps/*` (`private: true`) and `packages/agent` (a deployable `mda` project, not a library; changesets ignores it — Python release tooling, if ever needed, is release-please per the Python deepagents precedent, §9-Q3).

**Community files & posture.** v1 set: LICENSE, README, CONTRIBUTING (dev setup + PR conventions + DCO), SECURITY (private reporting), CODE_OF_CONDUCT (Contributor Covenant), bug + feature issue forms, PR template, CODEOWNERS. Deferred until traction: FUNDING, stale-bots, labelers, translations, CLA, GOVERNANCE ([05](../05-oss-setup.md)). Repo public from day one with a "**not accepting feature PRs yet — see roadmap**" banner in README + CONTRIBUTING until v1 (Codex-CLI pattern, [05](../05-oss-setup.md)).

**v0 concept import** ([06](../06-frontend-implementation.md) Phase A; P-001/D-012). One-way, one-time: copy `spencerthomas/deep-work-frontend` @ `c46b994` into `apps/web`; the monorepo becomes canonical and the v0 repo stays a design sandbox. Scaffold-scope hygiene: rename package from `my-project`; enable strict TS and delete `ignoreBuildErrors: true`; regenerate the lockfile under pnpm (the v0 lockfile pins a <24h-old `react-is` that trips pnpm `minimumReleaseAge`); wire into biome/CI. Keep `lib/data.ts` untouched for the later fixtures move (neighbor scope).

## 4. Contracts

Everything below is fixed by the source docs; deviations need a decision-log entry.

**Version pins at scaffold time** (verified 2026-07-21, [05](../05-oss-setup.md) + [research 07](../../research/07-oss-v1-setup.md); JS pins live in the pnpm catalog):

| Dependency | Pin |
|---|---|
| `deepagents` (PyPI) | 0.6.12 (watch 0.7.0; open-swe v2 already runs 0.7.0a7) |
| `deepagents` (npm) | ^1.11.1 |
| `@langchain/core` | ^1.2.0 |
| `@langchain/langgraph` | ^1.4.4 |
| `@langchain/langgraph-checkpoint` | ^1.1.2 |
| `@langchain/langgraph-sdk` | ^1.9.23 |
| `langchain` (npm) | ^1.5.0 |
| `langsmith` (npm) | ^0.7.1 |
| `@langchain/react` | ^1.0.28 |
| `managed-deepagents` | dev channel (0.4.0-dev) — renovate-excluded |
| `langchain-core` (PyPI) | >=1.4.8,<2 |
| Python | >=3.11 |
| pnpm | 10.x |
| turbo | ^2.10 |
| Node (CI + engines) | 22, 24 |
| `@changesets/config` | 3.1.1 |
| apps/web seed | Next 16.2.6 · React 19.2.4 · Tailwind v4 · shadcn on `@base-ui/react` ([06](../06-frontend-implementation.md) §1) |

**Root files:**

- `pnpm-workspace.yaml`: `packages: [apps/*, packages/*]` + `catalog:` holding the `@langchain/*` pins, react, typescript.
- `turbo.json`: pipeline `format → lint → typecheck → test → build`; Python tasks with explicit `inputs`.
- Root `pyproject.toml`: `[tool.uv.workspace] members = ["packages/agent", "apps/server"]`; ruff + pytest config.
- `.changeset/config.json`: changelog `@changesets/changelog-github`, `access: public`, `ignore: ["apps/*", "packages/agent"]` (deepagentsjs ignores examples; ours ignores non-published members).
- `.github/workflows/`: `ci.yml` (jobs per §3 table), `release.yml` (changesets/action v1.9.0 SHA-pinned, provenance env + permissions per §3), `pr_lint.yml`. Every `uses:` pinned to a full commit SHA.
- Renovate/dependabot config: weekly schedule; group `@langchain/*`; uv/pyproject coverage.

**`packages/agent` layout invariant** ([05](../05-oss-setup.md), [02 §3](../02-architecture.md)): must stay a valid `mda` project root — `agent.py` exporting `agent`, `instructions.md`, `tools/`, `middleware/`, `connectors/`, `schedules/`, `skills/`, `sandbox/`, `identity.py`. F01 creates the directory + wrapper only; contents are F02/M1 scope.

**Licensing/trademark contract** ([05](../05-oss-setup.md)):

- LICENSE = MIT; README carries a NOTICE-style attribution block ("Portions Copyright (c) LangChain, Inc. (MIT)" per [research 07](../../research/07-oss-v1-setup.md)) and an explicit non-affiliation disclaimer.
- README licensing section states the Elastic-2.0 boundary: `langgraph-api` is talked to over HTTP, never vendored or redistributed.
- No `lang*` in product name, domain, or npm scope; nominative fair use only ("built on LangChain deepagents").
- No LangChain wordmark/logo assets; no TWK Lausanne / Aeonik Mono font files (heading font ships as Inter/OFL per [packages/ui/README](../../../packages/ui/README.md)).

## 5. Edge cases & failure modes

- **v0 lockfile poisoning**: the imported lockfile's <24h-old `react-is` trips pnpm `minimumReleaseAge` ([06](../06-frontend-implementation.md) §2.5). Mitigation: never import the v0 lockfile; regenerate from `package.json` inside the workspace.
- **`mda deploy` vs monorepo metadata**: extra files (`pyproject.toml`, wrapper `package.json`, tests) in `packages/agent` could break the `.mda/build` compile. Unverified — F02 Spike 2 must run against the *in-monorepo* layout before M0 exits.
- **Turborepo caching Python wrong**: missing `inputs` on Python tasks yields stale green. Contract: cache keys include `pyproject.toml`, `uv.lock`, `**/*.py`; CI runs one uncached `--force` pass weekly (cheap insurance).
- **Strict-TS wall on import**: the v0 app was built with `ignoreBuildErrors: true`; enabling strict TS may surface a large error batch. Budget for it in the import task; do not land the seed with the flag still on ([06](../06-frontend-implementation.md) Phase A).
- **Dev-channel churn**: `managed-deepagents` 0.4.0-dev can shift weekly ([04](../04-roadmap.md) risk table). Excluded from auto-bumps; breakage is caught by the F02 canary/contract jobs, not by renovate noise.
- **changesets can't version Python**: `apps/server`/`packages/agent` are outside changesets; a release PR touching both stacks versions only the JS side. Acceptable while Python members are unpublished (§9-Q3).
- **P-005 reversal**: if the glue moves back into Next.js routes, `apps/server` + its CI job are deleted; the uv workspace shrinks to `packages/agent`; the Tauri static-export benefit (§3) is lost and the desktop spec must revisit the sidecar question.
- **Semantic-scope drift**: adding a workspace member without updating the pr-lint scope list silently blocks contributors; CONTRIBUTING documents the list and the CI error message links to it.

## 6. Security & privacy

- **Supply chain**: pnpm `minimumReleaseAge` enforced ([06](../06-frontend-implementation.md) §2.5 shows it already caught one incident); all Actions SHA-pinned; npm publishes carry provenance attestations (id-token) — deepagentsjs pattern ([research 07](../../research/07-oss-v1-setup.md)); weekly grouped updates keep pins fresh against the documented `@langchain/*` churn risk ([04](../04-roadmap.md)).
- **Secrets surface is minimal by design**: CI holds only `NPM_TOKEN` (release job). Vercel previews via Git integration mean no Vercel credentials in Actions ([research 07](../../research/07-oss-v1-setup.md)). No LangSmith/GitHub-App secrets exist at M0; when later specs add them they belong to `apps/server`'s deploy target *(P-005)*, never to the repo or client bundles.
- **Fork PRs**: CI jobs must not require secrets, so the full matrix runs on forks; the release workflow triggers only on push to `main`.
- **Vulnerability intake**: SECURITY.md with private reporting at v1 ([05](../05-oss-setup.md)); no public issue template for vulnerabilities.
- **Privacy**: the repo/CI stores no user data — consistent with the product stance that Deep Work stores essentially nothing ([02](../02-architecture.md) §1). Roadmap criterion 5 ("zero secrets in sandboxes") is later scope but the CI slot for its verifying test is this spec's job structure.

## 7. Acceptance criteria

1. `pnpm install && pnpm turbo run format lint typecheck test build` succeeds from a fresh clone on Node 22 and Node 24.
2. `uv sync` at the root resolves one lockfile covering `packages/agent` and `apps/server`; `turbo run lint test --filter=agent --filter=server` executes ruff + pytest through the wrappers and passes.
3. `apps/web` builds with `strict: true` and no `ignoreBuildErrors`; the workspace lockfile contains no `minimumReleaseAge` violations; the package is renamed (no `my-project` anywhere).
4. CI on a PR runs the four jobs of §3 (js matrix 22/24, python, contract slot, pr-lint); a PR titled without a valid type/scope fails pr-lint.
5. `grep -rE 'uses:.*@(v[0-9]|main|master)' .github/workflows/` returns nothing — every action is SHA-pinned.
6. A changeset touching `packages/ui` produces a version PR via `changesets/action`; the release workflow config sets `NPM_CONFIG_PROVENANCE=true` and `id-token: write`; `apps/*` and `packages/agent` are in the changesets ignore list and marked non-publishable.
7. Renovate/dependabot config exists with weekly schedule, a single `@langchain/*` group, and `managed-deepagents` excluded from auto-bumps.
8. Opening a PR against `apps/web` yields a Vercel preview URL via the Git integration; no Vercel token exists in Actions secrets.
9. All nine v1 community files (§3 list) exist; README and CONTRIBUTING carry the "not accepting feature PRs yet — see roadmap" notice.
10. Hygiene audit passes: LICENSE is MIT; README has the NOTICE block, non-affiliation disclaimer, and Elastic-2.0 boundary paragraph; repo-wide search finds no LangChain logo assets and no TWK Lausanne/Aeonik Mono font files.
11. `packages/agent` still satisfies the `mda` project-root layout after scaffolding (verified together with [F02](./02-m0-spikes.md) Spike 2).

## 8. Task breakdown

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | Root scaffold: `pnpm-workspace.yaml` + catalog pins (§4), `turbo.json`, root `package.json` (engines 22/24), `.gitignore`, pnpm 10 + `minimumReleaseAge` settings | — | AC-1 skeleton passes with empty packages |
| 2 | Adopt `packages/ui` seed as a workspace member (add `package.json` around existing tokens files) | 1 | `turbo run build --filter=ui` green |
| 3 | uv workspace: root `pyproject.toml` (members: agent, server), ruff/pytest config, `packages/agent` dir stub honoring the `mda` layout, `apps/server` FastAPI skeleton + one boot smoke test, wrapper `package.json`s with Turbo `inputs` | 1 | AC-2 |
| 4 | Toolchain: biome config (pending §9-Q1), `ci.yml` (js matrix + python + contract slot), `pr_lint.yml` with the §3 scope list, all actions SHA-pinned | 1–3 | AC-4, AC-5 |
| 5 | Import v0 concept as `apps/web`: copy @ `c46b994`, rename, strict TS, drop `ignoreBuildErrors`, regenerate lockfile, wire into biome/CI, vitest + RTL scaffold | 1, 4 | AC-3; `lib/data.ts` untouched |
| 6 | Placeholders `apps/desktop` (Tauri v2, M4) and `apps/mobile` (PWA config, M4) with `private: true` and README stubs noting the static-export constraint | 1 | Workspace resolves; no CI tasks registered |
| 7 | Vercel Git integration for `apps/web` previews (dashboard config; document in CONTRIBUTING) | 5 | AC-8 |
| 8 | Releases: `.changeset/config.json` (§4), `release.yml` (changesets/action SHA-pinned, provenance, permissions), `private: true` on apps + agent | 4 | AC-6 |
| 9 | Renovate/dependabot config (pending §9-Q2): weekly, `@langchain/*` group, dev-channel exclusion, uv coverage | 1 | AC-7 |
| 10 | Community files v1 set + contribution-posture notices | 1 | AC-9 |
| 11 | Licensing/trademark hygiene: NOTICE block, disclaimer, Elastic-2.0 paragraph, asset/font audit (scripted grep in CI or a checklist run) | 10 | AC-10 |
| 12 | Joint check with [F02](./02-m0-spikes.md): `mda dev/deploy` from the in-monorepo `packages/agent` | 3, F02 | AC-11 |

## 9. Open questions

1. **Lint/format**: ratify biome (this spec's recommendation) over oxlint/oxfmt, accepting divergence from deepagentsjs? ([05](../05-oss-setup.md) left it open; [06](../06-frontend-implementation.md) assumes biome.)
2. **Renovate vs dependabot**: [05](../05-oss-setup.md) names both. Renovate for grouping flexibility, or dependabot for deepagentsjs parity? Whichever wins must handle `uv.lock`.
3. **Publishing**: is `@deepwork` the confirmed npm scope (is it free?), and are `@deepwork/sdk`/`@deepwork/ui` published from v1 or kept private until post-v1? Does `packages/agent` ever get a PyPI release, or is it strictly a deploy artifact?
4. **`apps/server` hosting** *(P-005)*: no source doc gives it a preview or production deploy target (Vercel previews cover only `apps/web`). What runs it in CI previews and in the v1 self-deploy guide?
5. **CODEOWNERS**: solo `@spencerthomas` on everything at M0, or leave it out until there's a second maintainer? (It's in the v1 community set, [05](../05-oss-setup.md).)
6. **DCO enforcement**: CONTRIBUTING documents DCO ([05](../05-oss-setup.md)) — enforce with a DCO check app/action from day one, or document-only until contributions open at v1?

## 10. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| P-005 is provisional; glue may move back into Next.js routes | `apps/server` scaffold + CI job discarded; desktop static-export assumption breaks | Skeleton kept route-free and thin; §5 documents the reversal path |
| `@langchain/*` weekly v1-line churn breaks builds ([04](../04-roadmap.md) risk table) | Med | Catalog pins + weekly grouped bumps + F02 golden-transcript contract job as the tripwire |
| `mda` project-root constraint conflicts with workspace metadata | Blocks the primary deploy path | Verified at M0 via task 12 before anything is layered on |
| Toolchain divergence from deepagentsjs (biome vs oxlint/oxfmt) adds friction to LangChain adoption ([01](../01-vision.md) success criterion 5) | Low | Config is mechanical to swap; revisit if upstreaming talks start |
| v0 import carries unvetted dependencies | Supply-chain exposure | Lockfile regeneration + `minimumReleaseAge` + import is one-way with review |
| Python tasks silently stale in Turbo cache | False-green CI | Explicit `inputs` + weekly uncached run (§5) |
| deepagents py 0.6.12 ages under us (open-swe already on 0.7.0a7) | Rework in `packages/agent` | "Watch 0.7.0" note is a standing renovate/major review, not an auto-bump |
