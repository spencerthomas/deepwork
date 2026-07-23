# Deterministic product-demo fixture corpus

This directory contains synthetic, credential-free, language-neutral JSON
fixtures. It is private conformance input, not a public API schema, provider
transcript, live-contract result, or proof that an application consumer is
network-isolated.

The corpus clock is fixed at `2026-07-23T00:00:00Z` with 250 milliseconds per
logical tick. IDs are fixed, `fx_`-prefixed, and source-qualified. Provider and
runtime operations whose spikes remain open are represented as gated, unknown,
or unavailable even when a fixture demonstrates their presentation fallback.

Run from the repository root:

```text
PYTHONDONTWRITEBYTECODE=1 python3 internal/fixtures/product-demo/update_evidence.py --write
PYTHONDONTWRITEBYTECODE=1 python3 internal/fixtures/product-demo/update_evidence.py --check
PYTHONDONTWRITEBYTECODE=1 python3 internal/fixtures/product-demo/validate.py --check
```

`validate.py` is read-only and uses only deterministic standard-library logic.
Its exact bytes are hash-closed, and a fail-closed AST pass derives the reported
import, filesystem-write, process, dynamic-access, network, environment, and
wall-clock/wait counts from those bytes. This is static source evidence for this
validator, not a runtime sandbox or isolation claim for a future consumer.
`update_evidence.py` is the only helper allowed to write; it updates only
`hashes.sha256` and the two files under `evidence/`.
`verify_scope.py` is deliberately separate: it may run fixed, shell-free Git
queries for repository scope proof and never validates or mutates the corpus.

The 13 positive cases, 55 file-indexed negatives, and 141 deterministic semantic
probes are indexed by `corpus.json`, `negative/matrix.json`, and
`negative/semantic-matrix.json`. All 196 negative checks require exactly one
declared stable diagnostic. The negatives include tool correlation, bounded
untrusted content and raw-body exclusion; exact positional HITL decision arrays
and actual submission/resume absence; ordinary, partial-failure and collision
source qualification; structural and semantic-shape rejection; credential/
short-or-unpadded-Basic-auth/token/endpoint/actor-and-identity-key/path scrub;
value-qualified machine references, generic bare-host and descendant bypasses;
generic schemes/local/abbreviated/octal/numeric/Unicode-dot hosts, confusable
keys, maximum nesting, fixed case/tenant/workspace identities, corpus-wide
record-ID uniqueness, exact available-capability name inventories, coordinated
interrupt signatures, type-exact JSON scalar
semantics, every required positive-case semantic contract, the closed exact
logical-delay object, and an adversarial validator-purity source probe.
`hashes.sha256` closes exactly over `validate.py`, the machine index, applied
structural schemas, manifests, positive cases, negative matrix, and negative
fixtures. The generated hash manifest and evidence reports remain outside that
asset set to avoid a self-referential hash cycle.
