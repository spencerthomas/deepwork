# Execution plans

ExecPlans are self-contained, living implementation records. Product behavior
belongs in stable-ID product specs; an ExecPlan describes one bounded change and
keeps progress, discoveries, decisions, validation, and outcome current.

## Active

- [Canonical program coordination](active/DW-EXEC-PROGRAM-CANONICAL.md)
- [Wave 1 repository scaffold](active/DW-EXEC-M1-REPOSITORY-SCAFFOLD.md)
- [Root TypeScript workspace baseline](active/DW-EXEC-M1-ROOT-TS-HARNESS.md)

## Other records

- [Completed plans](completed/README.md)
- [Feature ExecPlan template](templates/feature.md)
- [Technical debt tracker](tech-debt-tracker.md)

Symphony is not active. A maintainer manually creates one worktree per reviewed
ExecPlan and keeps external credentials and provider integration out unless the
plan explicitly authorizes them.

Until `SPIKE-WORKTREE-001` passes, at most one full-stack application or product-
demo worktree may run. Package-only and documentation-only worktrees with disjoint
governed paths may run in parallel.
