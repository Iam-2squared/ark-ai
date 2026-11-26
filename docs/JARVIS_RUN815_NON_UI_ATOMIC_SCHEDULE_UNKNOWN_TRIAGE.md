# ARK Run815 — Manual-only uncertain occurrence triage (non-UI)

Saved report preparation (JST observed wall clock): 2026-11-12T18:49:05.775+09:00; **not a trusted action clock**.

## Work basis and changes

Branch `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8); beginning basis `c81a1ef7295266a4ff60ba32e4fa923de2ef86bb`, previously confirmed [CI #43187203002](https://github.com/Iam-2squared/ark-ai/actions/runs/43187203002) GREEN Windows/Ubuntu Python 3.11–3.13 (6/6).

1. **Audited SQLite pre-action COMMIT-UNKNOWN local review.**
   - `src/ark/agency/disconnected_atomic_unknown_outcome_review.py`, commit `7bef3b8511f1b3371e2a9c3748c79cc53e4ba7f5` (blob `fe6e87d99cba2a02c56f0cd37a38746fdc66c7ab`).
   - `tests/test_atomic_unknown_outcome_manual_review_run815.py`, commit `ff50702339d6f01569b88bc67075c3d9487754c7` (blob `0643ee27d0bda3cbd6b9f091d3881515b02da16e`).
   - A single read-only SQLite `BEGIN` validates the complete intent + audit chain, retained old prefix hash, exact occurrence/bound action/request tuple, and source identity. Outcomes are `UNCHANGED`, `PREEXISTING`, `LOCALLY_RECORDED`, or `ADVANCED_OTHER`; all require manual review and prohibit auto-replay. Old witness is untrusted caller data. A local positive record **never proves external exactly-once effects, registry binding, a trusted owner, or consent**. Regression matrix includes duplicate identities, nonmatching historical prefix, orphan/corrupt audit, stale/boolean witnesses, uncommitted writer, and substituted review functions.
2. **Expired proactive schedule COMMIT-UNKNOWN local review.**
   - `src/ark/offline_schedule_unknown_quarantine_review.py`, commit `c04fd98468974d5215a21651a44b113e516c90d9` (blob `00c7db63b5e5eb1467cf8cda43a4dcbaf2ad4f43`).
   - `tests/test_schedule_unknown_quarantine_run815.py`, commit `eb04c27695bb4e977d0b60f71e7922ab8a9daae4` (blob `f28b56ed64c3f06cc84b75e717b79a1c9942f199`).
   - A separate read-only SQLite `BEGIN` validates exact synthetic policy/occurrence/due/observed time, retained chain prefix and sequential row chain. Inert outcomes `UNCHANGED`, `PREEXISTING`, `LOCALLY_QUARANTINED`, `ADVANCED_OTHER`. Never advance a schedule cursor, send a notification, verify caller time, or authorize/replay execution. Tests cover restart, stale prefix, future/incorrect observed time, foreign policy, corruption/schema drift and concurrent uncommitted writer.
3. **Unrelated intermittent privacy race diagnosis — no contract weakening.**
   - `tests/test_privacy_revocation_cross_process_run425.py` diagnostic-only commit `33462c4b1902d8c9bb6f2e3067a25b36f14666ea`, blob `193cee8e9e051f7fb30d5587f56505945bb1d943`. Its losing child now prints the **exact rejected exception string** to captured synthetic-fixture CI output BEFORE applying the **same original** `"already revoked"` expectation. No assertion was removed/relaxed.
   - This was motivated by actual [CI #43193827334](https://github.com/Iam-2squared/ark-ai/actions/runs/43193827334): Ubuntu Python 3.11 reported one pre-existing `test_privacy_revocation_cross_process_run425.py::... [0]` failure, with child `AssertionError` but **original rejection text absent**, while Ubuntu 3.12/3.13 passed. The exact root cause remains **UNKNOWN**. The diagnostic is not a fix or proof of a Memory/privacy regression.

## Verification limits and safety

The new reviews exercise only disconnected local SQLite fixture data. No real ToolBackend, real observations, permission grant, user identity, trusted clock, guaranteed cross-store transaction, real side effect, human consent, Candidate weight, evaluation opening, paid API/GPU/compute, automatic deletion or notification. The local old hash/witness cannot authenticate external provenance or distinguish an external action from its absence. No V1/V2/Local UI/Launcher frozen source/evidence, PR #5 gate, or PR #9 UI branch was modified; PR #5, #8, #9 stay Draft/unmerged.

CI [#43193827334](https://github.com/Iam-2squared/ark-ai/actions/runs/43193827334) and [#43194143071](https://github.com/Iam-2squared/ark-ai/actions/runs/43194143071) are **not** exact final checkpoint GREEN 6/6; inspect individual jobs at latest HEAD before claiming PASS. No local complete test suite was performed.

## Next plan / 今後の方針

1. Confirm current exact-head CI all six environments; if FAIL, inspect raw job logs. Do not weaken the privacy loser assertion; recover its error text on a future occurrence, then investigate the specific false rejection with a minimal semantics-preserving correction.
2. Extend retained pre-action and schedule uncertainty into independently authenticated/manual review contracts only after lower-level exact-head GREEN; never automatically replay UNKNOWN.
3. Continue Memory CAS/ABA, Planner crash recovery, immutable registry/exact-type PermissionGate, observation fixture and free-only V3 guards without touching paused UI, frozen contracts or approval boundaries.
4. Keep `docs/PROJECT_STATUS.md` the canonical newest checkpoint; a future checkpoint write creates a separate SHA, and must not fabricate a self-referential commit result. ARK/JARVIS **NOT_PASSED**.
