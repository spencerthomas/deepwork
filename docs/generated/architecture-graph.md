<!-- GENERATED: do not edit by hand. -->
<!-- Source: tools/architecture/graph.json; command: python3 tools/docs/generate.py --write -->

# Architecture graph

```mermaid
flowchart LR
  "packages/sdk" --> "packages/domain"
  "packages/ui" --> "packages/domain"
  "apps/web" --> "packages/domain"
  "apps/web" --> "packages/sdk"
  "apps/web" --> "packages/ui"
  "apps/desktop" --> "apps/web"
```
