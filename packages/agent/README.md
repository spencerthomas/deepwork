# Deep Work agent package

`deepwork-agent` is an independently installable injected-model bridge. It
composes a typed LangGraph workflow with a Deep Agents executor:

```text
task -> plan -> approval interrupt -> execute, reject, or revise -> final answer
```

`create_graph(model=...)` is the explicit injected-model boundary. The package
never selects a provider, reads credentials, or creates an HTTP client. The default
`InMemorySaver` supports pause/resume and reopening completed state during the
same local process. Hosted deployment, durable checkpointing, provider
credentials, API sessions, and application persistence remain outside this
package. `runtime_capabilities().external_providers` is explicitly
`"unavailable"` until credentials and provider contracts exist.

Model-generated plans and final answers are marked `untrusted`. Approval is
required by default before the protected `execute_plan` action. The interrupt
payload preserves the ordered `approve`, `reject`, `respond` decision vocabulary.
Every resume is bound to the exact interrupt ID and plan revision. `respond`
requires a bounded comment and may supply a bounded edited plan; a revision
always pauses for a fresh approval before execution.

## Public factory

```python
from deepwork_agent import create_graph, initial_state
from langgraph.types import Command

graph = create_graph(model=injected_chat_model, tools=[optional_tool])
run = {"configurable": {"thread_id": "local-demo"}}

paused = graph.invoke(initial_state("Research the topic and write a short note."), run)
request = paused["__interrupt__"][0].value
assert request["action"] == "execute_plan"

completed = graph.invoke(
    Command(
        resume={
            "interrupt_id": request["interrupt_id"],
            "revision": request["plan_revision"],
            "decision": "approve",
        }
    ),
    run,
)
print(completed["final_answer"])
```

Use a unique `thread_id` for each independent local run. An application can
inspect `plan`, `status`, `approval`, and the final answer in graph state without
depending on private LangChain internals.

## Local checks

Python 3.12 and uv are required. From the repository root:

```bash
make -C packages/agent doctor
make -C packages/agent bootstrap
make -C packages/agent check
make -C packages/agent package-check
```

The test suite uses an official-compatible injected fake model with outbound
sockets denied. It proves plan production, exact LangGraph pause/resume authority,
approve, reject, and respond/revision paths, caller-tool binding alongside Deep
Agents built-ins, the final answer, and same-process state restoration.

`package-check` builds twice, requires matching artifact hashes, installs the
wheel with locked dependencies from the package-local uv cache in offline mode,
and compares the fresh result with the reviewed `artifacts.json` manifest. After
a reviewed source change, refresh that manifest deliberately with
`make -C packages/agent update-evidence`, then rerun `check`.

The package owns its `pyproject.toml`, `uv.lock`, environment, commands, source,
tests, and build artifacts. It never relies on a root Python environment or
`PYTHONPATH`.
