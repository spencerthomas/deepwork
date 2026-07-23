# Execution plans

ExecPlans are self-contained, living implementation records. Product behavior
belongs in stable-ID product specs; an ExecPlan describes one bounded change and
keeps progress, discoveries, decisions, validation, and outcome current.

## Active

- [Canonical program coordination](active/DW-EXEC-PROGRAM-CANONICAL.md)
- [Wave 1 repository scaffold](active/DW-EXEC-M1-REPOSITORY-SCAFFOLD.md)
- [Wave 1 TypeScript package scaffold rework](active/DW-EXEC-M1-TS-PACKAGES-SCAFFOLD.md)
- [Wave 1 deterministic product-demo fixture contract](active/DW-EXEC-M1-FIXTURE-CONTRACT.md)
- [Outcome 3 shared task domain and client contract](active/DW-EXEC-OUTCOME3-SHARED-TASK-CONTRACT.md)
- [LangChain-shaped OSS integration and repository gates](active/DW-EXEC-M1-OSS-ALIGNMENT.md)

## Other records

- [Completed plans](completed/README.md)
- [Feature ExecPlan template](templates/feature.md)
- [Technical debt tracker](tech-debt-tracker.md)

## External dispatch packets

- [Worktree isolation and architecture harness](external/DW-EXT-W1-WORKTREE-ARCH-HARNESS.md)
- [LangChain contract-spike research](external/DW-EXT-W1-LANGCHAIN-CONTRACT-RESEARCH.md)
- [Documentation-harness acceptance](external/DW-EXT-W1-DOCS-HARNESS-ACCEPTANCE.md)
- [API-key and workspace-header contract research](external/DW-EXT-W1-AUTH-HEADER-CONTRACT-RESEARCH.md)
- [Add a file to the first task safely](external/DW-EXT-W1-FIRST-TASK-SAFE-ATTACHMENTS.md)
- [Require a real plan before the first task executes](external/DW-EXT-W1-FIRST-TASK-PLAN-APPROVAL.md)
- [Finish research and writing with verifiable results](external/DW-EXT-W1-RESEARCH-WRITING-OUTCOME-CONTRACT.md)

Symphony is not active. A maintainer manually creates one worktree per reviewed
ExecPlan and keeps external credentials and provider integration out unless the
plan explicitly authorizes them.

Until `SPIKE-WORKTREE-001` passes, at most one full-stack application or product-
demo worktree may run. Package-only and documentation-only worktrees with disjoint
governed paths may run in parallel.
