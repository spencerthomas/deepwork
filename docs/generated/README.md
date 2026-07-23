# Generated documentation

Do not edit generated files by hand. Their source is canonical product metadata or
`tools/architecture/graph.json`.

Run:

```bash
python3 tools/docs/generate.py --write
python3 tools/docs/generate.py --check
```

Wave 0 generates feature coverage, issue/dependency map, route inventory, package
graph, architecture graph, and the current database-schema placeholder.

The API's OpenAPI contract now exists and is generated deterministically from
`create_app().openapi()` into `apps/api/openapi.json` (`make -C apps/api openapi`),
drift-checked by `apps/api/tests/contract_tests/test_openapi.py`. It lives beside
the API rather than under `docs/generated/`; a `docs/generated/` mirror is not yet
wired into `tools/docs/generate.py`.
