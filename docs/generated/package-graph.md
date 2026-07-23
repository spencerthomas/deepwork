<!-- GENERATED: do not edit by hand. -->
<!-- Source: tools/architecture/graph.json; command: python3 tools/docs/generate.py --write -->

# Package graph

| Zone | Runtime | May depend on |
|---|---|---|
| `packages/domain` | browser-safe | none |
| `packages/sdk` | browser-safe | packages/domain |
| `packages/ui` | browser-safe | packages/domain |
| `apps/web` | browser | packages/domain, packages/sdk, packages/ui |
| `apps/desktop` | native-host | apps/web |
| `apps/api` | server | none |
| `packages/agent` | server-independent | none |
