# Deep Work agent package

`deepwork-agent` is an independently installable local agent runtime with a
caller-injected model. It composes a typed LangGraph workflow with a Deep Agents
executor:

```text
task -> plan -> approval interrupt -> execute, reject, or revise -> final answer
```

The caller must inject an initialized `BaseChatModel`; this package never chooses
a provider, reads credentials, or creates an HTTP client. The default
`InMemorySaver` supports pause/resume and reopening completed state during the
same local process. Hosted deployment, durable checkpointing, provider
credentials, API sessions, and application persistence remain outside this
package. `runtime_capabilities().managed_external_providers` is explicitly
`"unavailable"`: a caller may inject a reviewed model, but this package does not
select providers or manage provider credentials.

Model-generated plans and final answers are marked `untrusted`. Approval is
required by default before the protected `execute_plan` action. The interrupt
payload preserves the ordered `approve`, `reject`, `respond` decision vocabulary.
`respond` requires a bounded comment, replans through the injected model, and
pauses on a fresh authoritative LangGraph interrupt before execution.

## Public factory

```python
from deepwork_agent import create_graph, initial_state, validate_approval_response
from langgraph.types import Command

graph = create_graph(model=injected_chat_model, tools=[optional_tool])
run = {"configurable": {"thread_id": "local-demo"}}

paused = graph.invoke(initial_state("Research the topic and write a short note."), run)
assert paused["__interrupt__"][0].value["action"] == "execute_plan"

completed = graph.invoke(
    Command(resume=validate_approval_response({"decision": "approve"})),
    run,
)
print(completed["final_answer"])
```

Validate before constructing `Command`: LangGraph checkpoints a malformed resume,
so callers must not submit an unvalidated value and then attempt to correct it on
the same thread.

Plan editing is separate from `respond`. Bound the edit with
`validate_plan_edit(...)`, then use only the public checkpoint sequence below:

```python
from deepwork_agent import validate_plan_edit

edited = validate_plan_edit(["Inspect the supplied evidence.", "Return a concise note."])
graph.update_state(
    run,
    {
        "plan": edited,
        "plan_revision": paused["plan_revision"] + 1,
        "plan_trust": "untrusted",
        "approval": "pending",
        "status": "planned",
    },
    as_node="plan",
)
repaused = graph.invoke(None, run)
assert repaused["__interrupt__"][0].id != paused["__interrupt__"][0].id
```

The `as_node="plan"` argument and re-invocation are mandatory. Omitting
`as_node`, or updating as the approval node, can bypass review of the edited
state.

Use a unique `thread_id` for each independent local run. An application can
inspect `plan`, `status`, `approval`, and the final answer in graph state without
depending on private LangChain internals.

## Research and writing journeys

`create_journey_graph` runs the same plan-first flow with a journey profile
around the injected model. The two v1 profiles are `research_profile()`
(report artifact) and `writing_profile()` (document artifact); the coding
journey is deliberately unavailable. The journey executor reuses pinned public
Deep Agents APIs only: `create_deep_agent` executes, the beta `RubricMiddleware`
(pinned at deepagents 0.6.12, construction emits its official beta warning)
grades and repairs, and profile subagents run synchronously through the
`task` tool that `create_deep_agent`'s `SubAgentMiddleware` stack provides.
Subagent declarations carry only a name, description, and instructions, so
they always inherit the injected model and caller tools; no provider string or
credential can enter through them.

```python
from deepwork_agent import (
    create_journey_graph,
    initial_state,
    research_profile,
    validate_approval_response,
)
from langgraph.types import Command

graph = create_journey_graph(
    model=injected_chat_model,
    profile=research_profile(),
    tools=[optional_search_tool],
    verifier_model=optional_injected_grader_model,  # defaults to model
)
run = {"configurable": {"thread_id": "journey-demo"}}

paused = graph.invoke(initial_state("Research the topic and report."), run)
assert paused["__interrupt__"][0].value["kind"] == "deepwork-plan-approval"

completed = graph.invoke(
    Command(resume=validate_approval_response({"decision": "approve"})),
    run,
)
artifact = completed["artifact"]        # validated, bounded, marked untrusted
verification = completed["verification"]  # rubric verdicts and repair history
```

The executor must declare exactly one structured `JourneyArtifactDraft`;
working files never become the artifact implicitly. `validate_artifact` bounds
the title, body, claims, evidence, and unresolved lists, and every claim keeps
an explicit basis label: `evidence` (cited), `inference` (reasoned), or
`unverified`. A claim citing an unknown or missing evidence reference is
downgraded to `unverified` and recorded in `citation_flags` — citations are
provenance coverage, never a truth claim.

Verification is owned by the pinned `RubricMiddleware`: each profile carries an
immutable `RubricSpec` version with identified criteria and a per-run
`max_iterations` bounded by `HARD_VERIFICATION_ITERATION_CAP` (5). The
`verification` record preserves the full ordered verdict history — including
failed iterations after a later pass — with per-criterion outcomes, bounded
rationale summaries, `VERIFIER_REF` identity, and a terminal status of
`passed`, `failed`, `capped`, or `error`. Execution status and verification
status stay separate: a run can complete while verification is failed, capped,
or errored, and nothing rewrites a failed verdict to passed.

`journey_capabilities()` reports the truthful boundary: artifacts exist only as
structured run output owned by the caller (no hosted storage or transfer),
subagents are synchronous and in-process only (no async subagents), the coding
journey is unavailable, verification is never ground truth, and no provider
credentials are managed.

## Local checks

Python 3.12 and uv are required. From the repository root:

```bash
make -C packages/agent doctor
make -C packages/agent bootstrap
make -C packages/agent check
make -C packages/agent package-check
```

The test suite uses an official-compatible deterministic fake chat model, denies
outbound sockets, and requires no API key. It proves plan production, the
LangGraph pause/resume contract, approve, reject, respond/replan, and plan-edit
paths, caller-tool identity binding alongside built-in Deep Agents tools, the
final answer, and same-process state restoration. For journeys it additionally
proves structured artifact declaration and validation, claim-basis labeling,
citation downgrade flags, rubric pass/repair/cap/grader-error histories, the
synchronous subagent path, and truthful capability reporting.

`package-check` builds twice, requires matching artifact hashes, installs the
wheel with locked dependencies from the package-local uv cache in offline mode,
and compares the fresh result with the reviewed `artifacts.json` manifest. After
a reviewed source change, refresh that manifest deliberately with
`make -C packages/agent update-evidence`, then rerun `check`.

The package owns its `pyproject.toml`, `uv.lock`, environment, commands, source,
tests, and build artifacts. It never relies on a root Python environment or
`PYTHONPATH`.
