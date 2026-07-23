# Core engineering beliefs

1. Source truth is qualified and explicit; UI plausibility is not evidence.
2. Dependencies point inward through stable domain and port boundaries.
3. Public upstream APIs and conformance tests are preferred to copied internals.
4. Credentials, tenant authority, and provider protocol details stay server-side.
5. Fixture and live behavior share normalized contracts while retaining visible
   evidence class and capability gates.
6. Work is resumable from repository-local specs, ExecPlans, and proof artifacts.
7. Architecture rules become executable and produce actionable repair guidance.
8. Accessibility, security, recovery, and observability are acceptance behavior,
   not later polish.
9. Small independently reviewable changes outrank bulk migrations.
10. Unresolved external contracts fail closed with a named fallback.
