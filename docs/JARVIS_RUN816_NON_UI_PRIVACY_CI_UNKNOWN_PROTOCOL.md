# ARK AI Run816 — privacy CI protocol repair and fail-closed UNKNOWN triage

**Scope:** strictly FREE-ONLY / backend / disconnected; Draft PR #8 `research/jarvis-foundations`, no frontend. **ARK/JARVIS NOT_PASSED.** Existing V1/V2/Local UI/Launcher freezes and protected evaluation gates remain unchanged.

## Verified starting evidence

Work basis was Run815 checkpoint HEAD `8f2b1ce8a3f4b97a0997b0c440e099e1d9747943`. GitHub Actions [#43195197178](https://github.com/Iam-2squared/ark-ai/actions/runs/43195197178) concluded **FAIL**. Raw Ubuntu 3.11 job `131104238206` and Windows 3.13 job `131104238622` show `tests/test_privacy_revocation_cross_process_run425.py` failed in *both* parameterizations. This was not an observed double-revocation: one child emitted `REVOKED:<digest>`; the other correctly rejected `scope already revoked`. A recently introduced diagnostic was printed on **stdout**, making the second reply `LOSER_REJECTION_DETAIL:'scope already revoked'\nALREADY` instead of exact `ALREADY`. Therefore `outputs.count("ALREADY") == 1` failed. This is an exact stdout protocol regression, not evidence that the underlying privacy veto was broken. Test assertion/fixture and veto implementation must remain strict.

## NEW package A — process-race diagnostic channel repair

- Normal GitHub Contents API commit `8b2a3ef0037c9a0c098802e3fd975e6ffd5f83e1`, file `tests/test_privacy_revocation_cross_process_run425.py`.
- Moved only `LOSER_REJECTION_DETAIL` from stdout to **stderr** using the already imported `sys`. Kept exact stdout machine protocol `ALREADY` / `REVOKED:<digest>`, still asserts `"already revoked" in str(error)`, still checks one revocation row and rejects later reads. Diagnostic retains visibility in `replies` on pytest failure.
- No status/consent reversal, retry grant, or production privacy code changed. No arbitrary skipped/xfail cases.

## NEW package B — atomic preaction UNKNOWN outcome protocol pins

- Source commit `213eaed100d70a42453ec260df8799bdcfcb0f96`, `src/ark/agency/disconnected_atomic_unknown_outcome_review.py`. Pinned imported SQLite module, the ledger module's SQLite binding, and allowed triage states against runtime rebinding *before* opening a private SQLite handle.
- New `tests/test_atomic_unknown_outcome_protocol_run816.py` commit `ded146bc6a90834916639d17eb2de0fb1777efe6`, corrected fixture setup ordering at `0a8ecf44be284af779409fa87fe4bb5b43c69042`. **Four new cases:** three rejected protocol substitutions and one intact, non-authorizing unchanged-ledger result. Fixture creates its SQLite source before the intentionally hostile module rebinding; no accidental bootstrap failure can mask the review guard.
- Reviewer remains diagnostic only: local presence is not an external effect; audit-before-action and exactly-once claims require independent corroboration and separate authorization.

## NEW package C — proactive quarantine UNKNOWN outcome protocol pins

- Source commit `acb4a0c332165e019b3d9449a7c9e59ba58e9cf7`, `src/ark/offline_schedule_unknown_quarantine_review.py`. Same explicit fail-closed pinning for local SQLite module, underlying ledger SQLite binding, and allowed quarantine states.
- New `tests/test_schedule_unknown_protocol_run816.py` commit `107bfb37d2645fc8614accaab46aadfe606506e1`. **Four new cases:** three substituted input-protocol carriers rejected before reading the fixture, plus intact unchanged-ledger classification with all notification/execution/replay/consent/clock flags false.
- Neither source executes a scheduled action, delivers notifications, or automatically replays an UNKNOWN operation.

## CI observations (at report preparation; not final-head certification)

- [#43202443884](https://github.com/Iam-2squared/ark-ai/actions/runs/43202443884) on privacy repair commit: Ubuntu Python 3.11 and 3.12 GREEN; other matrix jobs IN PROGRESS at last review.
- [#43202724802](https://github.com/Iam-2squared/ark-ai/actions/runs/43202724802) on intermediate atomic test commit: IN PROGRESS.
- [#43202852281](https://github.com/Iam-2squared/ark-ai/actions/runs/43202852281) on completed source+test work HEAD `107bfb37d2645fc8614accaab46aadfe606506e1`: QUEUED, six matrix jobs not certified.
- Eight new regression cases are **submitted, not yet claimed GREEN**. No local full pytest/Ruff run was available. Do not treat any intermediate run as final checkpoint HEAD evidence; later documentation commits have distinct HEADs.

## Remaining hard gates and next plan

1. Inspect exact final-checkpoint HEAD's six CI jobs (Ubuntu/Windows × Python 3.11/3.12/3.13). If FAIL, extract real logs and fix only the affected invariant/test without weakening gates.
2. If privacy process-race errors recur, distinguish actual second writer from output-protocol instrumentation and preserve revocation veto. No regrant.
3. Only after exact-head GREEN, consider further Planner/registry/atomic integration. A pair of independently reviewed SQLite stores is **not** an atomic cross-store transaction; UNKNOWN must never become automatic WRITE replay.
4. Continue Memory CAS/ABA, COMMIT-UNKNOWN and privacy-lifecycle work; seek complete bounded retained witness before authorizing any irreversible operation.
5. PR #5 V3 gate and paused UI PR #9 remain Draft/unmerged/untouched, as do frozen V1/V2 and Local UI/Launcher evidence. No paid API, external GPU, Candidate training/promotion, credentials, physical-PC action, real tool backend, protected evaluation, or main merge.
