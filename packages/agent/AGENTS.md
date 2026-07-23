# Agent package instructions

These instructions apply to `packages/agent` in addition to the repository root
guidance.

## Boundary

This is an independently installable Python package. It may use supported public
Deep Agents, LangChain, and LangGraph APIs only after their exact contract is
reviewed. It must not import `apps/api`, application sessions or tenant models,
FastAPI, SQLAlchemy, browser or TypeScript code, or another Deep Work package.

`SPIKE-CONFIG-001` remains open. Until it passes, keep graph/runtime behavior
explicitly unavailable. Do not add `langgraph.json`, infer configuration fields,
or simulate provider success.

## Commands

Run from the repository root:

```bash
make -C packages/agent doctor
make -C packages/agent bootstrap
make -C packages/agent lock-check
make -C packages/agent format-check
make -C packages/agent lint
make -C packages/agent typecheck
make -C packages/agent test
make -C packages/agent build
make -C packages/agent package-check
```

Default tests deny network access. Integration/evaluation work that needs an
external runtime requires a separate reviewed ExecPlan and must never be folded
into these commands.
