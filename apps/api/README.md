# Deep Work API scaffold

This independently locked Python 3.12 project is the application-service package
boundary for Deep Work. The Wave 1 scaffold provides:

- a side-effect-free `deepwork_api.create_app()` factory;
- process-only `GET /health`;
- deterministic `GET /api/v1/demo/status` that is permanently labelled fixture;
- separate `deepwork-api` and `deepwork-worker` entry points from one artifact; and
- package-local format, lint, type, no-network test, build, and clean-wheel checks.

It does **not** provide authentication, source connections, provider calls,
streaming, persistence, durable jobs, credentials, or production readiness. The
worker supports `--check` only and reports durability unavailable.

## Commands

```bash
make doctor
make bootstrap
make format-check
make lint
make typecheck
make test
make contract
make build
make package-check
make check
```

`make bootstrap` is the only command permitted to resolve dependencies from
reviewed public package indexes. Normal tests deny sockets and require no `.env`,
provider account, or external service.
