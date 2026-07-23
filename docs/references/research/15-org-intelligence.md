# Organizational intelligence layer — research

*Condensed findings (agent-researched 2026-07-22, verified against live docs/PyPI/GitHub). Grounds [plan doc 07](../plan/07-org-intelligence.md). CONFIRMED = read from primary source; INFERRED = synthesis.*

## KEY FACTS

- CONFIRMED — **LangSmith Insights** (Plus/Enterprise): auto-clusters traces hierarchically with per-category stats and executive summaries (clickable trace refs); custom attributes; saved configs; **scheduled reports (cron)**; beta REST `POST /api/v1/sessions/{id}/insights[/configs][/configs/generate]` (generate config from natural language); SDK `client.generate_insights()` works even over external chat histories. ~$1–4 per 1,000 threads; 1,000-trace sample cap; models enum openai|anthropic.
- CONFIRMED — `POST /runs/query` rate limits tiered: 10/10s (≤7d window), 3/10s (>7d), 1/10s (full-text/child-runs on large windows); **Bulk Export** (Plus/Enterprise) ships Parquet to S3-compatible destinations on schedules for warehouse-scale analysis.
- CONFIRMED — official **langsmith-mcp-server** (hosted option available): runs/traces, thread stats, datasets, experiments, prompts, billing usage — the direct path for an agent to read "what all our agents did this week."
- CONFIRMED — **Automations**: filter + sample + {add-to-dataset, annotation queue, webhook, extend retention} + online evaluators; backfill supported.
- CONFIRMED — deepagents docs ship a complete **background consolidation ("sleep time compute") recipe**: second deep agent + `crons.create(schedule="0 */6 * * *")` with lookback == interval; org-level memory namespaces documented **read-only to agents** ("prevents prompt injection via shared state").
- CONFIRMED — **MDA memory** = Context Hub files: hot `/memories/user/AGENTS.md` injected per turn; cold files on demand; per-actor/tenant slices; org memory mounts read-only at `/memories/org` (Hub `org-memory/**`), agent writes runtime-denied; deploys never overwrite memories.
- CONFIRMED — **Context Hub commit webhooks** (`context_hub.commit.created.v1`, HMAC-signed) fire on every commit — the hook for a memory-change review pipeline.
- CONFIRMED — Fleet documents "**memory synthesis**" as a first-class scheduled-agent use case; Fleet memory writes are approval-gated by default.
- CONFIRMED — **OKF** (Open Knowledge Format): Google Cloud open spec (2026-06-12) — markdown bundles, typed YAML frontmatter, link-based relationships; **openwiki** (MIT, LangChain) emits OKF v0.1 from connectors (git, Gmail, Notion hosted MCP, X, web, HN) via a deepagents documentation agent.
- CONFIRMED — **langmem** 0.0.30 (Oct 2025): alive, MIT, pre-1.0, slow — not absorbed into langgraph; file-based deepagents memory is the blessed pattern. **Zep CE dead** (Apr 2025; OSS successor is Graphiti). **Mem0** (Apache-2.0, self-hostable, LangChain integration) viable but opaque-store philosophy.
- CONFIRMED — **Graphiti** (`graphiti-core` 0.29.2, Apache-2.0): bi-temporal knowledge-graph agent memory on Neo4j/FalkorDB/Neptune (Kuzu deprecated); **ontology = Pydantic entity/edge types** on `add_episode`; in-repo MCP server; LangGraph integration guide exists.
- CONFIRMED — **langchain-neo4j 0.10.0** (MIT, 2026-06) is the maintained graph package and now owns `LLMGraphTransformer` (ex-langchain-experimental, which is unmaintained); `neo4j-graphrag` 1.18.0 (Apache-2.0) is Neo4j's official GraphRAG pipeline. No first-class GraphRAG concept in current LangChain v1 docs. No RDF/OWL tooling in practice anywhere in the ecosystem.
- CONFIRMED — v1-era SQL guidance = hand-rolled tools over the driver (not SQLDatabaseToolkit); deepagents `examples/text-to-sql-agent`: `list_tables`/`get_schema`/`query_checker`/`execute_query` + `query-writing`/`schema-exploration` skills — ready-made data-analyst template shape.
- CONFIRMED — DB MCP landscape: Anthropic's reference Postgres server **archived with an unpatched SQL-injection issue** (do not use); maintained: Supabase official MCP, `mcp-server-pg`, Postgres MCP Pro; **dbt-mcp** (dbt Labs official) exposes the Semantic Layer to agents.
- CONFIRMED — Fleet tool packs are proprietary hosted OAuth integrations; Fleet's extensibility = **Arcade MCP gateways** (per-user auth); `langchain-arcade` formally unmaintained (Arcade went MCP-first); Composio SDK is MIT but its platform is closed. **LangSmith Agent Auth** (`langchain-auth`, beta, works self-hosted) brokers per-user OAuth.
- CONFIRMED — Prior art convergence: **Devin** splits Knowledge (reviewable, agent-*proposed*, human-approved) from Playbooks (workflows); **Cowork** memory is project-scoped files; **ChatGPT company knowledge** (Oct 2025) is permission-aware connector-RAG with mandatory citations (its non-inspectable reference-history memory is the cautionary counterexample); **Dust.tt** core is MIT; **Glean** leads with a permission-aware graph.
- INFERRED — Recommended spine: Context Hub files (OKF-shaped) as canonical org memory; traces → Insights/digests → proposed commits → approvals-inbox review as the learning loop; MCP-first connectors; Graphiti as opt-in v3 graph; Deep Work builds only review UX, templates, and provisioning glue.

## OPEN QUESTIONS

- Insights beta REST: full report payload readable via API, or UI-only? (M1 probe.)
- Context Hub write scopes under LangSmith OAuth (review loop commits via Hub API).
- OKF v0.1 stability (~6 weeks old); markdown+frontmatter degrades gracefully.
- openwiki-in-sandbox connector auth design (local-CLI-shaped today).
- Multi-workspace orgs: Insights/automations are per-workspace; whole-org view needs iteration under org-scoped keys.

## SOURCES (primary)

docs.langchain.com: `/langsmith/insights`, `/langsmith/rules`, `/langsmith/export-traces`, `/langsmith/data-export`, `/langsmith/managed-deep-agents-memory`, `/langsmith/context-hub-webhooks`, `/langsmith/semantic-search`, `/langsmith/agent-auth`, `/langsmith/fleet/{essentials,schedules,tools,arcade}`, `/oss/python/deepagents/memory`, `/oss/python/langchain/sql-agent` · PyPI/npm version pages for langchain-neo4j, neo4j-graphrag, graphiti-core, langmem, mem0ai, langchain-mcp-adapters, openwiki · langchain-ai/{openwiki,deepagents,langsmith-mcp-server} · getzep/graphiti · LangChain blog "Insights Agent" (2025-10-23) · OpenAI "Introducing company knowledge" · docs.devin.ai (Knowledge) · dust-tt/dust · docs.getdbt.com (dbt-mcp) · modelcontextprotocol/servers-archived.
