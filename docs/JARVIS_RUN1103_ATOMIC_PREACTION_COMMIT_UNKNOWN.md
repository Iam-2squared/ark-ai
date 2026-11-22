# Run1103 — atomic pre-action intent/audit COMMIT ambiguity

## Exact basis

- Repository: `Iam-2squared/ark-ai`
- Parent: Draft PR #8, `research/jarvis-foundations`
- Exact parent HEAD: `e8761e183094cd27955423844a8db7d6b0063829`
- Child branch: `research/run1103-atomic-preaction-commit-unknown`
- Existing source: `src/ark/agency/disconnected_atomic_preaction_ledger.py` (unchanged)
- Regression suite: `tests/test_atomic_preaction_commit_unknown_run1103.py`

## Added evidence

The new hard-boundary fixture injects a lost COMMIT acknowledgement at two distinct points:

- **Before native COMMIT:** the transaction rolls back; cold recovery sees neither intent nor pre-action audit row.
- **After native COMMIT:** the caller still receives an error, but cold recovery sees the complete intent/audit pair and validates the retained witness.

The test asserts paired cardinality and inert result flags. It deliberately does not retry the failed operation on the original handle; cold readback is the only resolution.

## Limits

This validates the local SQLite transaction boundary of the disconnected fixture only. It does not establish trusted time, authenticated approval, independent custody, power-loss guarantees, cross-database atomicity with Memory/Planner/ActionAudit, or an external effect. The ledger still has no execute method. No production dispatch, frozen contract/schema, UI, V1/V2/Local UI/Launcher evidence, paid service, external compute, Candidate generation/promotion, protected evaluation, credentials, physical hardware or main merge is involved.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. **ARK/JARVIS remains NOT_PASSED.**
