# Run781 — Non-UI alignment CI repair, quarantine protocol pin and Planner epoch custody

**Scope:** local-first, reversible, disconnected, zero-new-paid-service ARK foundations only. Exact work-basis PR #8 `research/jarvis-foundations` HEAD `f1b2128c9c76e12c4aa82f8c8e3a7120ff866923` (Run780 checkpoint). All changes use the ordinary GitHub Contents API, are on Draft PR #8, and are **not** merged. **ARK/JARVIS/V3 NOT_PASSED**.

## A. Real CI blocker — old observation test and new preaccess invariant

[Run780 checkpoint CI #42935086363](https://github.com/Iam-2squared/ark-ai/actions/runs/42935086363) finished **FAIL in all 6 Python/OS jobs**. Actual Ubuntu 3.12 (job `130243044826`) and Windows 3.12 (job `130243044551`) logs isolate **six assertion mismatches** in `tests/test_offline_activity_transcript_region_epoch_run572.py`: tests injected a replacement `alignment.json.dumps` callback and expected a late `"input changed"` error and callback execution, whereas the strengthened source now correctly rejects the replacement **before execution** with `"original alignment authority changed"`. No evidence of a real audio-input acceptance regression.

Commit `ee6d6c0e854a9ac99106ca3a843bdabb6e83f83d` changes only those tests. They now demand preaccess rejection, no replaced callback invocation and no reflective nested region mutation; the unchanged normal path remains covered. Production observation logic and private PCM denial gates are not weakened. [CI #42940578932](https://github.com/Iam-2squared/ark-ai/actions/runs/42940578932): Ubuntu 3/3 GREEN; Windows 3 still IN PROGRESS at last sample. This is **not** exact-final-head six-platform PASS.

## B. Proactive quarantine hash-chain protocol guard

Previous `src/ark/disconnected_schedule_quarantine_ledger.py` validated caller/receipt class slots, but its `_digest` and direct occurrence hash derivation used mutable `json.dumps`, `hashlib.sha256` and protocol constants without an import-original codec check. A locally substituted callback could change a stored synthetic hash-chain or run on a private fixture before durable quarantine evidence was assessed.

Commit `aef72e8f3da00d00f4ebb3c0a40caffa50fc35c3` pins the import-time SHA/JSON modules and callbacks, digest domain, occurrence/witness regex identity, SQLite DDL identity, and exact integer bounds. It rechecks digest dependencies before/after serializing and hashing, and checks both input and receipt admission before attempting the SQLite write path. Commit `82feb2f75685b81a3ce7ee604d5779fbd82778b2` adds `tests/test_quarantine_digest_protocol_preaccess_run781.py`: **11 new parametrized cases** (seven pre-writer rejection cases, three genesis/occurrence rejection cases, one restored normal restart). They use only disposable SQLite and inert callbacks; a failed preflight cannot create a quarantine row. This is integrity hardening, **not** authenticated policy custody, a trusted clock, consent, actual notification or replay authorization.

[Source CI #42940892120](https://github.com/Iam-2squared/ark-ai/actions/runs/42940892120) and [source+test CI #42940973202](https://github.com/Iam-2squared/ark-ai/actions/runs/42940973202) were IN PROGRESS at last sample. No GREEN claim for these exact source+test hashes.

## C. Planner detached recovery input drift across atomic inspection

`src/ark/agency/disconnected_epoch_bound_atomic_triage.py` previously rechecked Planner SQLite twice and Atomic SQLite again, but caller-held `SyntheticPlanRecovery` and `SyntheticPlanTail` are reflectively mutable frozen dataclasses. The final atomic-inspection callback could change their carrier/field identity after both Planner rechecks while the outer review still returned an earlier no-authority diagnostic.

Commit `165b8a003aabd6fa25b3c2f7f4252d358bc7a989` binds original recovery-tail fields, retained-tail fields and recovery-status tuple carrier throughout the independent atomic callback and return path, and binds the atomic child triage fields before the last callback. Any observed drift rejects manual review. Commit `6aa891c39832bb6d02bcd9feab8fb7ea575359ea` adds `tests/test_epoch_bound_planner_input_epoch_run781.py`: **four new cases** for reflected recovered-tail revision, retained-tail hash and equal-value status carrier replacement during the final atomic read, plus normal no-authority result. No real tool/backend invocation exists; this does not provide a two-database transaction or eliminate post-return races.

[Planner source CI #42941338475](https://github.com/Iam-2squared/ark-ai/actions/runs/42941338475) IN PROGRESS; [source+test CI #42941414366](https://github.com/Iam-2squared/ark-ai/actions/runs/42941414366) QUEUED at last sample. Verify all six jobs and actual logs; do not substitute GREEN from earlier SHA.

## Preserve boundaries and next plan

- **Unchanged**: Draft/unmerged PR #5 protected V3, Draft/unmerged PR #9 UI foundation; `main`, frozen V1/V2/Local UI/Launcher, protected evaluation/frozen contracts. UI/frontend remains PAUSED.
- No training, GPU, billable service, Candidate generation/promotion, protected final evaluation, real camera/microphone, live ToolBackend, external WRITE, credentials, destructive action, physical-PC action, or main merge. Fail-closed local hashes are **not** independent custody; reviewer agreement is **not** consent, exactly-once, or external execution proof.
- **Next 1:** read the exact-head 6-job results, inspect failure logs, fix only verified defects with regular GitHub Contents writes. **Next 2:** Memory generation CAS/COMMIT-UNKNOWN/expiry retained-witness review. **Next 3:** Planner crash/terminal persistence and immutable registry/exact PermissionGate with separate trusted-clock audit-before-action and no-dispatch mock integration after lower-level GREEN. **Next 4:** privacy veto, proactive occurrence continuity and safe V3 path/identity/reproducibility reviews, keeping all approval gates intact.

**Report basis:** `6aa891c39832bb6d02bcd9feab8fb7ea575359ea`. This report is source-grounded but does not claim six-platform GREEN for itself or any later checkpoint.

## CI addendum — exact observed lint failure and minimal test correction

[Planner source+test CI #42941414366](https://github.com/Iam-2squared/ark-ai/actions/runs/42941414366) failed **all six jobs during Ruff import sorting**, before pytest. Actual Ubuntu 3.11 job `130263860939` and Windows 3.12 job `130263861209` both report only `I001` in `tests/test_epoch_bound_planner_input_epoch_run781.py:7`. The cause was an extra blank line immediately after the imports, not a failed Planner behavior assertion. Regular Contents-API commit `fc3d5fa1cd5f6b8308bd54476c6bc623b3350541` removes that one redundant blank line. Planner source behavior and test expectations are unchanged. **The corrected exact source/test HEAD is not yet 6/6 GREEN**; wait for its automatically triggered CI. No manual duplicate workflow run was launched.
