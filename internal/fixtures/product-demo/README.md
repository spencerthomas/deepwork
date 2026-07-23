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
It reads only this directory and never reads the environment, wall clock, Git,
or network. `update_evidence.py` is the only helper allowed to write; it updates
only `hashes.sha256` and the two files under `evidence/`.
`verify_scope.py` is deliberately separate: it may run fixed, shell-free Git
queries for repository scope proof and never validates or mutates the corpus.

The 13 positive cases and 55 single-code negatives are indexed by `corpus.json`
and `negative/matrix.json`. The negatives include tool correlation, bounded
untrusted content and raw-body exclusion; exact positional HITL decision arrays
and actual submission/resume absence; ordinary, partial-failure and collision
source qualification; structural and semantic-shape rejection; credential/
short-or-unpadded-Basic-auth/endpoint/actor-and-identity-key/path scrub;
value-qualified machine references, generic bare-host and descendant bypasses;
and logical-delay cases.
`hashes.sha256` closes exactly over the
machine index, applied structural schemas, manifests, positive cases, negative
matrix, and negative fixtures.
