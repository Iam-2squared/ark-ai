# ARK AI — Run776 / NON-UI free-only foundation evidence

## Scope and basis

- Work-basis PR #8 branch `research/jarvis-foundations` at `9b85e1031832a0aa1ae83db1fc4c65e43391f678` (Run775 canonical checkpoint; exact PR HEAD read before any write).
- All changes are isolated, reversible, **non-UI** and rely solely on synthetic local SQLite data. Frozen V1/V2/Local UI/Launcher, observation contracts, V3 Candidate/evaluation gates and protected evidence remain unchanged.
- No real ToolBackend, authorization, permission grant, external effect, model weights, service purchase, physical-PC gate, PR #5/#9 edit, main merge or paid/external GPU activity.

## Package A — recheck atomic tail after Planner review

- Core source commit `71c7237d8ae32477d7661c8e36d2e4dbbb24f7b5`: `src/ark/agency/disconnected_epoch_bound_atomic_triage.py`.
- Regression commit `1a4dea3e6fcf46bd7fc9b292b78c7fbe3dc949ee`: `tests/test_epoch_bound_atomic_tail_recheck_run776.py`, 3 cases.
- Previously, a Planner -> atomic -> Planner read sequence had no atomic tail read following the second Planner read. The optional deny-only helper now invokes the original `DisconnectedAtomicPreactionLedger.inspect` after the second Planner recovery, validates its exact snapshot witness/count and rejects a new atomic reservation or tampered reader. It is not a lock, multi-database transaction or proof of freshness beyond its final read.
- A deterministic synthetic callback on the ledger instance opens its second read only after committing a new independent reservation, verifying that the old tip is rejected. Additional tests reject a substituted inspect method *before invoking it* and verify a positive local match still denies dispatch, WRITE, automatic replay, external effect and cross-store atomicity.
- The frozen journal/ledger schema and existing execution permissions were not altered. The result is still **manual review only**, and a recovered RUNNING WRITE is still UNKNOWN.

## Package B — independently retained privacy veto continuity

- Regression commit `98e857d703a985c93291b105a6c414c46d7ef417`: `tests/test_context_revocation_retained_rollback_run776.py`, 4 cases.
- Three synthetic tampering variants (deleted row, rewritten timestamp, rewritten scope digest) preserve a valid SQLite schema but disagree with an *already retained* privacy witness, so the continuity check must reject. A distinct new veto remains compatible with an earlier retained witness. No raw private source content or credentials.
- The retained witness must actually live outside the mutable ledger to detect rollback. Neither this test nor the local hash establishes authenticated consent, complete deletion or independent trusted custody.

## Package C — Memory COMMIT-UNKNOWN must not invite retry

- Regression commit `5f245f54bd169de48cae3053d9db7cf32fb7dd6a`: `tests/test_memory_generation_postcommit_unknown_run776.py`, 2 parameterized cases.
- Inject only a synthetic readback error *after* generation-fenced CAS has committed: one SQLite-level error, one schema-level error. The caller gets an UNKNOWN/manual-review rejection while the durable row has advanced exactly one revision, event history appended exactly once, and reuse of the retained old lifetime token cannot create a second update.
- No production Memory schema/CAS/expiry constraints changed, no real-world exactly-once effects asserted.

## CI status, boundaries and verification policy

- Prior Run775 checkpoint `9b85e1031832a0aa1ae83db1fc4c65e43391f678`: [CI #42900905430](https://github.com/Iam-2squared/ark-ai/actions/runs/42900905430) **6/6 GREEN** verified at beginning of this invocation, Windows and Ubuntu × Python 3.11–3.13.
- New source commit `71c7237...`: [CI #42907531137](https://github.com/Iam-2squared/ark-ai/actions/runs/42907531137) **IN PROGRESS** at observed job query.
- Privacy commit `98e857...`: [CI #42907724868](https://github.com/Iam-2squared/ark-ai/actions/runs/42907724868) **IN PROGRESS** at observed job query.
- Memory commit `5f245f...`: [CI #42907850185](https://github.com/Iam-2squared/ark-ai/actions/runs/42907850185) **IN PROGRESS** at observed job query.
- Last source/test commit `1a4dea3...`: [CI #42907989699](https://github.com/Iam-2squared/ark-ai/actions/runs/42907989699) **IN PROGRESS / QUEUED** at observed job query.
- This report and a future single canonical checkpoint each create a **newer HEAD**. Six-job GREEN for final exact HEAD is **not yet established**. No local full-suite test result or Windows hardware gate is claimed. CI failures, if any, must be investigated via actual job logs and corrected through the normal Contents path without weakening safety.
- A local snapshot, old hash witness or recovered planner status **never** authenticates an issuer, gives consent, provides a trusted clock, grants execution permission, proves external effects, establishes independent custody, or guarantees cross-store atomicity.

## Next plan / 今後の方針

1. Verify exact-head six-job CI after report/checkpoint and diagnose any actual failed job, including potential injected interleaving fixture/runtime failures.
2. Advance isolated Memory COMMIT-UNKNOWN recovery/readback, expiry/ABA and legitimate concurrency; keep uncertain results manual-only.
3. Strengthen Planner terminal propagation, immutable registered tool inputs, exact PermissionGate/authorization and audit-before-action only after lower-layer checks pass.
4. Continue privacy-safe Personal Context, proactive/observation fixture interfaces, free V3 reproducibility/path/identity/rights guards. Never open protected evaluation or paid compute without explicit authorization.
