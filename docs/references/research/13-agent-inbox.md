# Research: langchain-ai/agent-inbox (agent a4d6328d559d9442c, completed 2026-07-21)

## What it is
Client-only Next.js 16.2.10 / React 19 / Tailwind 3.4 / shadcn-ui (new-york, Radix) inbox over LangGraph threads paused on interrupt(). No server/DB: one React context + URL query params + localStorage. MIT, ~1k stars, alive but maintenance-mode (Jul 2026 commits = dependency repair, partly authored by Open SWE agent). Hosted at dev.agentinbox.ai. **Absent from docs.langchain.com** — official HITL guidance now points to HumanInTheLoopMiddleware + useStream `stream.interrupt` review cards / Agent Chat UI / Studio.

## Mechanics
- List: `threads.search({limit≤100, offset, status, metadata:{graph_id|assistant_id}})` (UUID→assistant_id else graph_id); sort client-side created_at desc; tabs = thread status: interrupted | idle | busy | error | human_response_needed | all.
- Act: `runs.stream(threadId, graphId, {command:{resume:[HumanResponse]}, streamMode:"events"})` — streams node names live during resume.
- "Ignore" = resume {type:"ignore"} (agent decides) vs "Mark as Resolved" = `threads.updateState(threadId,{values:null, asNode:END})` (force-end, no resume) — two dismissal semantics.
- Config: localStorage `inbox:agent_inboxes` = [{id, graphId, deploymentUrl, name?, selected, tenantId?, createdAt}] (multi-inbox first-class) + `inbox:langchain_api_key` → `x-api-key` header (only required for us.langgraph.app URLs). tenantId → "Open in Studio" deep links.

## ⚠️ CRITICAL: the interrupt contract has MIGRATED
- **Legacy (agent-inbox native)**: `HumanInterrupt = {action_request:{action,args}, config:{allow_ignore,allow_respond,allow_edit,allow_accept}, description?}`; resume = one-element array `[{type:"accept"|"ignore"|"response"|"edit", args:null|string|ActionRequest}]`. DEPRECATED in langgraph v1.
- **Current (what deepagents emits via langchain HumanInTheLoopMiddleware)**: `HITLRequest = {action_requests:[{name, args|arguments, description?}], review_configs:[{action_name, allowed_decisions:("approve"|"edit"|"reject"|"respond")[], args_schema?}]}`; resume = `Command(resume={"decisions":[{type:"approve"|"edit"|"reject"|"respond", ...}]})` (one per action_request; JS keyed by interrupt id). deepagents adds a filesystem-interrupt predicate middleware.
- agent-inbox `normalizeInterrupt()` maps new→legacy for DISPLAY only (approve→accept, reject→respond, ignore disabled, FIRST action_request only; reads `arguments` so Python `args` → {}), but resume path still sends legacy list → **NOT round-trip compatible with deepagents HITL today**.
- **Deep Work verdict: build the approvals surface natively on HITLRequest/decisions (+ useStream stream.interrupt); treat agent-inbox as UX reference only.**

## UX patterns to steal
- 12-col fixed-height (71px) inbox rows: unread dot | bold action title + 65-char truncated description | capability chip | MM/dd h:mm a timestamp; hover bg-gray-50/90.
- Capability-derived status pills (rounded-full border-1.5 + 6px dot): "Requires Action" (green) vs "Ignore" (gray); thread status: gray idle / yellow busy / red error / green interrupted.
- Action buttons derived from config; combined Edit⇄Accept panel (accept auto-becomes edit when a field is dirtied); segmented toggle for multiple submit types; per-arg editable fields prefilled (non-strings JSON-stringified).
- Schema-tolerant parsing: ~6 payload shapes handled; malformed → synthetic `improper_schema` interrupt (ignorable, copyable thread ID) — never crash the inbox.
- URL-as-state: inbox tab, pagination, `view_state_thread_id` all query params → shareable, back-button works.
- Live streaming of current langgraph_node during resume; raw state inspector view.

## Open questions
- deepagents-JS 1.11 resume parsing end-to-end (docs show Command({resume:{decisions}}) matching Python).
- `arguments` vs `args` normalizer mismatch: bug or JS-only intent.
