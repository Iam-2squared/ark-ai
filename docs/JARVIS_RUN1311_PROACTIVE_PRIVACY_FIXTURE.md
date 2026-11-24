# ARK Run1311 — proactive native-COMMIT privacy fixture binding

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `169950b5728fe874148abe2fe40be0bf3173d0b7`.
- Child branch: `research/run1311-proactive-privacy-fixture-hardening-20261125`.
- Existing source/test basis includes `tests/test_proactive_state_native_commit_hard_exit_run1283.py`; this change strengthens that regression without changing production code.

## Finding and correction

The prior crash-boundary test defined a private observation marker but passed the constant digest `"a" * 64` to the ledger. Its database/WAL/SHM scan therefore did not prove that the marker corresponding to the persisted digest was absent.

The revised test computes SHA-256 from the synthetic private marker in the parent test process, passes only that digest to the child, verifies the exact digest after cold recovery, and scans the database plus any surviving WAL/SHM sidecars both after recovery and after the next explicit CAS transition.

## Scope and evidence boundary

Test-only. No proactive source, schema, DDL, policy, CAS semantics, public API, or frozen contract changes. The child exits immediately after native SQLite COMMIT returns and before `evaluate()` returns. This demonstrates only the tested local digest-only persistence path; it does not establish general data-erasure guarantees, trusted time, consent, notification authorization, dispatch, fsync/power-loss durability, or exactly-once external effects.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No PASS is claimed before that run completes. Synthetic values and disposable local SQLite only; no paid compute, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, UI/frontend work, or main merge.
