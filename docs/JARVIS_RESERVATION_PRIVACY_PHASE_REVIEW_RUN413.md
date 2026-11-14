# JARVIS foundations — bounded recovery / returned witness / audit-link / privacy epochs (Run413)

**Evidence class:** disconnected, local-fixture engineering note. This is not an execution PASS, an authenticated audit record, a paid-training clearance, verified human approval, or externally attested time. Free-only ordinary GitHub Contents writes on the **Draft PR #8** `research/jarvis-foundations` branch; no merge.

## Precise basis and packages

Invocation began from prior Run412 checkpoint HEAD `fb33ab136e4610decfa9ddda6654b97df3ba4fe0`. Four independent packages add **19 parametrized pytest cases** and source hardening:

| Lane | Source commit | Test commit | Exact scope |
| --- | --- | --- | --- |
| Bounded cross-store reservation triage | `df2cff17cad437be32023552e1f376441e05ca44` (Ruff-only import correction `976abf78f7894c7f674a70a2de85ebefc31a62f8`) | `bb36ecb1178d4f76c7aaa597e15651ded9a1151f` | Bound the previously unbounded direct `_COLUMNS` scan at 10,001 fetched rows, reject >10,000, and recheck the input epoch after every row hash. **4 tests.** |
| Plan-wide returned witness custody | `a48eefb7671b9839eba9640be33d3974aaf03ea1` | `dae1bf3c522e7a526602651fc9d96f36ac993661` | Retain every per-WRITE recovery result and nested witness field carrier through later per-step SQLite callbacks and final replay; refuse locally forged later status/digest values. **5 tests.** |
| Sidecar read-only audit link continuity | `a29d8ebc4a9ec4cd5e1c0b044bff9505417d1d76` | `cb0c21837e5972f67c5bc724de2a509538cdcff0` | Pin the exact source Path and retained event/hash/time carriers across connection, BEGIN, replay, commit and return. Equal-valued carrier swaps are rejected. **5 tests.** |
| Personal Context privacy veto phases | `9d957119c1aafba6b38821a632da98337d1bb5e9` | `7a6cb7e1a7811e6238a146bebf6172f4c3edc9d5` | Revalidate owner/namespace and source through revocation transaction boundaries and read-only veto checks. Post-COMMIT veto failures do not roll back committed privacy markers. **5 tests.** |

Source and fixture paths:
- `src/ark/agency/synthetic_recovery_triage.py` / `tests/test_recovery_ledger_bounded_scan_run413.py`
- `src/ark/agency/synthetic_write_plan_recovery_review.py` / `tests/test_recovery_plan_returned_epoch_run413.py`
- `src/ark/agency/synthetic_occurrence_audit_link_review.py` / `tests/test_audit_link_read_epoch_run413.py`
- `src/ark/personal_context_revocation_review.py` / `tests/test_privacy_veto_transaction_epoch_run413.py`

## Fault and behavior matrix

| Fault / boundary | Expected assertion | Consequence |
| --- | --- | --- |
| Recovery ledger has > row budget | `SyntheticRecoveryRejected` before unbounded materialization | No replay, no ToolBackend use |
| Reservation row hash mutates ToolCall on first of two rows | Reject before next digest can restore modified caller | No result promoted |
| Third plan-wide WRITE-review callback modifies earlier per-step result | Reject even when first step's final replay is unchanged | No false terminal status |
| Equal-valued replacement of earlier nested ledger digest | Reject original field-carrier mismatch | Local hashes do not become authority |
| Sidecar `_connect` or BEGIN retargets source | Reject, close read handle | No later sidecar SELECT as trusted evidence |
| Sidecar validator or replay clones retained digest carrier | Reject despite string equality | No silent witness substitution |
| Privacy-veto BEGIN changes owner/namespace while subsequent validator might restore it | Reject before validator; transaction rolled back | Cannot silently review/mark wrong scope |
| Privacy-veto COMMIT callback retargets source | Reject; if write committed, marker remains durable | No implicit reenrollment / deletion |
| Healthy two-WRITE snapshot, retained empty link, nonrevoked privacy scope | Inert fixture reviews remain usable | All authority properties remain **false** |

## Verification discipline

The first six source/test HEAD workflow runs **#1004–#1009** were observed failing in **all six environments** from a Ruff `I001` import-group ordering regression introduced by the first package, not from verified test outcomes. Job log evidence: #1004 Ubuntu 3.13 job `121099779330`; #1007 Ubuntu 3.13 job `121100192036`; #1008 Ubuntu 3.13 job `121100456553`. The narrow normal Contents correction commit `976abf78f7894c7f674a70a2de85ebefc31a62f8` matches Ruff's printed desired import order. **Do not mark any new HEAD GREEN from a lint-only correction or an in-progress CI.** Inspect exact final source+test and documentation/checkpoint HEAD runs and retain failures in history.

Prior Run412 canonical checkpoint `fb33ab136e4610decfa9ddda6654b97df3ba4fe0`: CI **#1003 / 40167055942 SUCCESS all six**, independently re-read at start of this invocation. Its source #1001 and engineering doc #1002 also completed SUCCESS, both six-job suites. Any newer validation is separately determined.

## Safety limitations and gates

- No shared transaction spans Planner, reservations, audit and audit-link SQLite. A sequence of individually verified snapshots cannot establish atomically consistent external effects. Retained witness hashes are caller-custodied local *diagnostics*, not immutable trusted anchors.
- No authenticated issuer, authenticated clock, proof of true user consent, real ToolBackend receipt, exactly-once external effects, live notification, microphone/camera, personal-data deletion/export, Candidate training, GPU, evaluation opening or main merge.
- **UNKNOWN/RUNNING and reserved-PENDING WRITE are never automatically replayed.** Synthetic SUCCEEDED never authorizes external dispatch; all these reviews are inert.
- Frozen V1/V2/Local UI/Launcher evidence, frozen V3 contract, Memory v1 and ActionAudit v1 SQL schemas, and Draft V3 PR #5 must remain untouched.

## Next plan / 今後の方針

1. Inspect the exact post-lint source/test CI across Ubuntu/Windows 3.11–3.13 and resolve failures with smallest ordinary-Contents patch; do not duplicate workflow executions.
2. Add retained sidecar *write-path* custody and multi-WRITE relational crash fixtures only on independent source/test paths, keeping external effects disabled.
3. Tighten remaining SQLite transaction-phase checks in Memory and privacy retention without touching frozen schemas.
4. Advance issuer/clock and observation/proactive interfaces solely as disconnected fixtures; preserve spend/training/review gates and PR draft states.
