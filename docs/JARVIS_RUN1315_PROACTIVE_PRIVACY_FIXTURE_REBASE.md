# ARK Run1315 — proactive native-COMMIT privacy fixture binding

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `824bb987f0addf4e961c9f4949f6075ca42a1caa`.
- Child branch: `research/run1315-proactive-privacy-fixture-rebase-20261125`.
- Previous child exact-head CI [45441996027](https://github.com/Iam-2squared/ark-ai/actions/runs/45441996027) was GREEN on its old base only; it does not transfer to this rebase.
- Existing source/test basis includes `tests/test_proactive_state_native_commit_hard_exit_run1283.py`; this rebase strengthens that regression without changing production code.

## Finding and correction

The prior crash-boundary test defined a private observation marker but passed a constant digest, making its raw-marker database/WAL/SHM scan vacuous. The revised test computes SHA-256 from the synthetic private marker in the parent process, passes only that digest to the child, verifies the exact digest after cold recovery, and scans the database plus surviving WAL/SHM sidecars after recovery and after the next explicit CAS transition.

## Scope and evidence boundary

Test/documentation-only. No proactive source, schema, DDL, policy, CAS semantics, public API or frozen contract changes. The child exits immediately after native SQLite COMMIT returns and before `evaluate()` returns. This does not establish general data-erasure guarantees, trusted time, consent, notification authorization, dispatch, fsync/power-loss durability or exactly-once external effects.

Synthetic values and disposable local SQLite only. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. No paid compute, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, UI work, frozen-contract change or main merge.
