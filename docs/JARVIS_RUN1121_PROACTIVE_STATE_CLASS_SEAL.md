# Run1121 — proactive state ledger class identity seal

## Exact basis

- Parent: Draft PR #304, `research/run1120-proactive-state-process-crash`.
- Parent HEAD at child creation: `c082c2dfd0004a7d3525dbfbda9556a7a9bc53e8`.
- Child branch: `research/run1121-proactive-state-class-seal`.
- Source commit: `3bade794c8332783f644dc2e00a99770295176e2`.
- Test commit: `e42b549dd5ff416d0329e175168c9f1264ff6504`.

## Finding

The proactive state ledger already rejects subclasses, mutable instance dictionaries and instance path reassignment. However, its instance guard did not pin the exact class-level entry-point descriptors or the `__slots__` layout. A class-level replacement of `_connect`, `evaluate`, `count`, the `path` property or the assignment guards could therefore change the implementation reached by otherwise exact instances.

## Change

- Capture the exact ledger class, slot tuple, descriptor-name vector and import-original descriptors for constructor, hooks, path property, connection, policy binding and public read/write/count methods.
- Validate the class descriptor epoch before exact-instance validation and before any path/database access.
- Pin the vector references themselves so empty/equal-valued vector replacement cannot skip checks.
- Add synthetic regressions for class-level descriptor substitution before database creation and for descriptor-vector rebinding before read.

The existing instance slots, path identity, SQLite schema, CAS behavior, state digest, policy semantics and denial-only authority flags are unchanged. Existing process-restart coverage remains in the parent branch.

## Evidence boundary

The guard detects class-level descriptor substitution when an original ledger entry point is invoked; it is not a secure Python sandbox against arbitrary same-process reflection or hostile interpreter mutation. Tests use disposable local SQLite only. No notification, dispatch, trusted clock, consent, external service, timer, paid compute, credentials, hardware, UI, protected V2 evaluation, Candidate or main merge is enabled.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No PASS is claimed. PR #8 and PR #304 remain Draft/unmerged; ARK/JARVIS remains NOT_PASSED.
