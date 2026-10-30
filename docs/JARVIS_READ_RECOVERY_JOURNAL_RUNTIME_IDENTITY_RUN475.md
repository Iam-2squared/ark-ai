# ARK AI Run475 — Detached READ recovery/journal custody and V3 runtime identity epochs

**Observed at:** 2026-10-30 17:45 JST (local runtime clock; NOT a trusted clock, GitHub commit time, consent record, or provider billing proof).
**Repository:** `Iam-2squared/ark-ai`; **PR #8:** `research/jarvis-foundations` Draft/open/unmerged; **PR #5:** `research/v3-learning-evaluation` Draft/open/unmerged.
**Work-basis HEADs:** PR #8 `f2012fc40ce4f5b94665c7e382138d9ddf7c7c3a`; PR #5 `93352996075ccdcf001b133d6bca6d7f886a2ba5`.
**Final source/test HEADs before this evidence document:** PR #8 `667272ed5644ed623a280ed617d722ee07ae9b73`; PR #5 `23fe76a18a2197cf19ff7daa9ac403e64d23cb4b`.

## NEW work — three independent implementation/test packages, 28 authored pytest cases

1. **Detached READ recovery decisions** (7 cases): `src/ark/agency/disconnected_read_recovery_schedule.py`, blob `a9cf2dbea2d77fd75e6aeed7795ff1ab16a5c74f`; `tests/test_read_recovery_decision_custody_run475.py`, blob `fae58340b9b4810906b800aeba79dbe22b41f713`. Preserve exact original, non-authorizing decision and schedule result types. Recheck earlier decisions after each constructor and SHA-256 callback. Reject reflected mutations, equal-value replacement, forged decision factories and forged result factories. Never grant execution or automatic replay.
2. **SQLite READ journal retained witness/COMMIT boundary** (8 cases): `src/ark/agency/disconnected_read_journal.py`, blob `94139be7d5e38e44f58be2b5d2b887184b938d8a`; `tests/test_read_journal_receipt_epoch_run475.py`, blob `35f72593179495b2d961eebcdabcb5acf41df57f`. Pin retained witness and receipt fields across `BEGIN`, scan/hash, insert, and COMMIT. Reject stale/rewritten values, including same-content replaced objects, forged read-witness factories and invalid returned authority flags. **Post-COMMIT rejection is diagnostic: persisted row remains reserved; no implicit rollback or automatic retry.**
3. **V3 pre-paid runtime identity snapshot custody** (13 cases): `src/ark/learning/runtime_guard.py`, blob `4df67de1aa688a546ce7c654ae98ce793d14de24`; `tests/v3/test_runtime_identity_epoch_run475.py`, blob `fa8ee6a62302b75994690b3eb7f2647dbd4aa851`. Require all frozen environment/hardware identity fields before runtime validation, preserving original exact snapshot mapping/value and measured identity carriers across callbacks. Missing required fields produce a denied `RuntimeIdentityMismatch` rather than an unclassified `KeyError`. Validation is synthetic and does not use a GPU, create Candidate bytes, access billing, or authorize a runtime.

All six source/test blobs above were independently re-fetched through the ordinary GitHub repository API and SHA-matched on their respective branches. Six source/test commits used the ordinary Contents API; no raw Git objects, force updates, protected evaluation or main merge.

## CI: distinguish exact source/test HEADs from later docs/checkpoint HEADs

- **Last inherited checkpoint, PR #8** `f2012fc40ce4f5b94665c7e382138d9ddf7c7c3a`: #1547 / run `41023430668` **COMPLETED SUCCESS**, all six Ubuntu/Windows Python 3.11–3.13 jobs GREEN. Historical baseline only.
- **PR #8 exact new source/test HEAD** `667272ed5644ed623a280ed617d722ee07ae9b73`: #1551 / run `41028241533` **IN PROGRESS at 17:45 JST**; Ubuntu 3/3 GREEN, Windows 3/3 IN PROGRESS. Do not claim 6/6 or full-repo local pytest/Ruff.
- **PR #5 exact new source/test HEAD** `23fe76a18a2197cf19ff7daa9ac403e64d23cb4b`: #1553 / run `41028538883` **IN PROGRESS at 17:45 JST**; Ubuntu 3/3 and Windows 3.12/3.13 GREEN, Windows 3.11 IN PROGRESS. Do not claim 6/6 before completion.
- **Local whole-repository pytest/Ruff:** NOT VERIFIED. Isolated execution container cannot resolve GitHub DNS to clone. CI checks are GitHub-hosted standard public-repository workflows automatically triggered by normal commits, not separately launched paid compute.

## Boundaries and integration prerequisites

- Both PRs remain Draft and unmerged. No new paid/external GPU compute, APIs, subscriptions, credentials, account connections, real user data, production READ/WRITE Tool dispatch, or unapproved main merge.
- Frozen V1/V2/Local UI/Launcher evidence, Memory v1 DDL, V3 Contract 1 (120 approved training / 30 validation, one Candidate and no sweep), protected V2 final evaluation, provenance/contamination/regression/reproducibility, and all human approval gates remain unchanged.
- The READ journal is local SQLite + hash-chain evidence, NOT independent immutable custody or exactly-once external effect. A crash after COMMIT but before externally retaining the witness still needs manual reconciliation. A local runtime identity comparison is NOT authorization for billable compute or trusted provider identity.
- **Next:** confirm CI for both exact source/test HEADs, repair only real failures through standard writes, add SQLite file/WAL/handle custody where safe, advance Memory coherent CAS/retention, Planner UNKNOWN WRITE quarantine and trusted-clock audit-before-action, and V3 independent approval/provenance gates. Full JARVIS remains **NOT_PASSED**.
