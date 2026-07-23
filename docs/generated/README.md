# Generated documentation

Do not edit generated files by hand. Their source is canonical product metadata or
`tools/architecture/graph.json`.

Run:

```bash
python3 tools/docs/generate.py --write
python3 tools/docs/generate.py --check
```

Wave 0 generates feature coverage, issue/dependency map, route inventory, package
graph, architecture graph, and the current database-schema placeholder. OpenAPI is
not generated until an API exists; its absence is explicit rather than simulated.
