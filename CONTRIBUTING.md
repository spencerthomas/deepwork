# Contributing to Deep Work

Deep Work is preparing an OSS-first implementation that should feel familiar to
LangChain and Deep Agents contributors: small scoped changes, public API
discipline, typed boundaries, independently testable packages, conventional
commits, and evidence-backed review.

Before implementation, read `AGENTS.md`, the owning product spec, and an active
ExecPlan. Use one worktree per bounded task. Keep the ExecPlan current and attach
exact validation results. Do not enable an unresolved provider contract, commit a
credential, edit generated output, or use the visual prototype as runtime proof.

The supported repository checks are:

```bash
make doctor
make bootstrap
make check
make check-docs
make test-e2e-demo
```

`make check` includes the repository's format, lint, type, unit, build,
architecture and OSS license/trademark gates. `make check-oss` runs that legal and
branding gate directly and writes a machine-readable local report to
`output/oss-audit/report.json`. The root [README](README.md) states the MIT,
attribution, runtime-license, trademark and non-affiliation boundaries a fork must
preserve.

Security issues should follow [SECURITY.md](SECURITY.md), not a public issue.
