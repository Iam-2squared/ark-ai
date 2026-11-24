# ARK Run1321 — Proactive native-COMMIT privacy fixture rebased

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD after Run1317 Memory ingress integration: `77d3b2f50d258bb3694afc0d03830e0d44644961`.
- Child branch: `research/run1321-proactive-privacy-fixture-rebase-20261125`.
- Rebased the test-only correction from Draft PR #496 / Run1315. Its prior exact-head CI [45453294645](https://github.com/Iam-2squared/ark-ai/actions/runs/45453294645) was GREEN 6/6 on the old parent only; it does not transfer to this rebase.

## Finding and correction

The earlier native-COMMIT hard-exit regression declared a synthetic private observation marker but passed a constant digest to the ledger, making its raw-marker database/WAL/SHM scan vacuous. The revised fixture hashes the marker in the parent process, passes only the digest to the child, verifies that exact digest after cold recovery, and scans the database plus surviving WAL/SHM sidecars after recovery and after the next explicit CAS transition.

## Scope and evidence boundary

Test/documentation-only. No Proactive production source, schema, DDL, policy, CAS semantics, public API or frozen contract changes. The child exits after native SQLite COMMIT returns and before `evaluate()` returns. This does not establish general data-erasure guarantees, trusted time, consent, notification authorization, dispatch, fsync/power-loss durability or exactly-once external effects.

Synthetic values and disposable local SQLite only. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. No paid compute, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, UI work, frozen-contract change or main merge.
