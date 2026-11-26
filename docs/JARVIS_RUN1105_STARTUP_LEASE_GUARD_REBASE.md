# Run1105 — startup readiness lease guard-vector regression rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`
- Exact parent/work-basis HEAD: `a37dd52a379ce5606978d9654dd00ca63007e295`
- Child branch: `research/run1105-startup-lease-rebase`
- Rebased from Draft PR #237 child HEAD: `a85f29e643b2660dd32a8c6f4e89891d08b6d2b7`
- Original child exact-head CI run: `44982574024` (GREEN, 6/6); this result does not transfer to the rebased HEAD.
- Test: `tests/test_startup_readiness_lease_guard_vectors_run1102.py`

## Change

Carries the two synthetic test/report files only; the stale `docs/PROJECT_STATUS.md` from PR #237 is intentionally excluded. The 40 regression cases exercise:

- All 11 descriptor/original-carrier guard vectors reject empty and equal-valued replacement before requirement access.
- Replaced requirement descriptors and startup-authority denial properties fail closed before poisoned getters execute.
- Component/schema labels reject NUL, line controls, C1 and Unicode formatting controls, invalid UTF-8 surrogate data, and UTF-8 byte-budget overflow.
- The 512-requirement ceiling and exact bounded age input are exercised.

Production readiness code, startup snapshot semantics, schema, V1/V2 contracts, Planner, ToolRegistry, PermissionGate, audit, authorization and executor code are unchanged.

## Limits

This remains a disconnected synthetic diagnostic. A READY lease is not a real startup attestation, trusted clock, human consent, notification permission, dispatch permission, device check, or backend authorization. No local files, devices, credentials, live personal data, or ToolBackend are opened or executed.

## Validation

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required for this rebase. No local pytest/Ruff PASS is claimed. No roadmap PASS is declared.
