# Contributing to Deep Work

Deep Work is preparing an OSS-first implementation that should feel familiar to
LangChain and Deep Agents contributors: small scoped changes, public API
discipline, typed boundaries, independently testable packages, conventional
commits, and evidence-backed review.

Before implementation, read `AGENTS.md`, the owning product spec, and an active
ExecPlan. Use one worktree per bounded task. Keep the ExecPlan current and attach
exact validation results. Do not enable an unresolved provider contract, commit a
credential, edit generated output, or use the visual prototype as runtime proof.

Wave 0 validation is:

```bash
python3 tools/docs/generate.py --check
python3 tools/docs/check.py
```

The Wave 1 scaffold will establish language-specific setup, format, lint, type,
test, build, and changeset commands. Until those commands exist, report the gap
instead of inventing an equivalent pass.

Security issues should follow [SECURITY.md](SECURITY.md), not a public issue.
