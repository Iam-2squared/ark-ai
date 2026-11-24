# ARK AI — Canonical Project Status

## LATEST

- **Saved at:** 2026-11-24 20:40:23 JST (Asia/Tokyo)
- **Checkpoint branch / PR:** `research/jarvis-foundations` / Draft PR #8; this is an isolated research branch, not `main`.
- **Exact work-basis HEAD:** `ddc4a574437361059552615ceb44936a628555dc` (Run1280 Planner terminal hard-exit regression integration).
- **Checkpoint-result HEAD:** the GitHub commit created by this `PROJECT_STATUS.md` update; its exact returned SHA is verified after the write and reported in the run summary. This file does not self-reference its own commit hash.
- **Overall ARK state:** V1, V2 and Local UI v1 retain their reviewed/frozen PASS evidence. JARVIS foundations continue in isolated, reversible research branches. **ARK/JARVIS overall remains NOT_PASSED.** No V3+ protected evaluation was opened and no later milestone PASS is claimed.

## NEW work this invocation

All new packages are test/documentation-only rebases onto the exact Run1280 foundation HEAD above. No production source, schema, DDL, public API or frozen contract was changed.

1. **Draft PR #462 — startup readiness lease regression correction**
   - Current child HEAD: `7b71f62204a293cb5c978b6524aec3d64d95ea97`.
   - Corrected one invalid negative-case fixture: age 1 ms with a 100 ms maximum is valid, and added a positive assertion for that case.
   - Corrected the descriptor-substitution assertion to expect the stronger, earlier `readiness result authority epoch changed before review` denial.
   - Added `docs/JARVIS_RUN1282_STARTUP_READINESS_LEASE.md`.
   - Initial run `45382547475` failed in pytest with those two test-expectation errors; Ruff passed. No production defect was reported. Fresh run `45385945866` is QUEUED.

2. **Draft PR #463 — durable-ledger native-COMMIT hard-exit regression bundle**
   - Current child HEAD: `78f1d782d2415ba8ded06401a6607ae6e56b5630`.
   - Rebased synthetic hard-exit tests for Memory scoped expiry purge, Personal Context replay reservation, and proactive eligibility state.
   - Added `docs/JARVIS_RUN1283_LEDGER_NATIVE_COMMIT_RECOVERY.md`.
   - Initial run `45385180828` failed Ruff F401 for one now-unused `hashlib` import after a test assertion simplification. The import was removed without changing test semantics. Fresh run `45385683618` is QUEUED.

3. **Draft PR #464 — ToolRegistry deletion-seal regression**
   - Child HEAD: `605842017b112f09619928c80209b0564cdafd68`.
   - Rebased ordinary slot-deletion, reflective registration-map deletion and replaced-guard checks; inert backend remains uncalled.
   - Added `docs/JARVIS_RUN1284_TOOL_REGISTRY_DELETE_SEAL.md`.
   - Exact-head CI run `45385289828` is IN PROGRESS.

4. **Draft PR #465 — Personal Context final revocation veto**
   - Child HEAD: `ee9fa010ef9deceb904cf8c3e37d90ac6e21fee5`.
   - Rebased the synthetic race regression in which a revocation appended during final retained-history review must veto projection return.
   - Added `docs/JARVIS_RUN1285_CONTEXT_FINAL_VETO.md`.
   - Exact-head CI run `45385417961` is IN PROGRESS.

5. **Draft PR #466 — Observation fixture UTF-8 allocation**
   - Child HEAD: `8ec985d4b7290fdc59b8f309678b25e90a699837`.
   - Rebased ASCII/multibyte byte-boundary, early oversize rejection, surrogate rejection and pre-hash denial tests for the disconnected fixture adapter.
   - Added `docs/JARVIS_RUN1286_OBSERVATION_UTF8.md`.
   - Exact-head CI run `45385598574` is IN PROGRESS.

## Tests, CI and evidence

- **Foundation basis:** PR #460 merge commit `ddc4a574437361059552615ceb44936a628555dc`; exact-head CI run `45379837623` was GREEN, 6/6 jobs. This is the current research-branch basis, not a main merge.
- **PR #462:** run `45382547475` FAIL (Ruff passed; pytest had 2 expectation failures, 19,472 passed and 151 skipped in the observed Windows/Python 3.11 job). Test-only correction committed at `31ac179ffef6fc536f45b2e8d580d259e36df151`; evidence doc added at `7b71f62204a293cb5c978b6524aec3d64d95ea97`. Fresh run `45385945866` QUEUED.
- **PR #463:** run `45385180828` FAIL (Ruff F401 only; pytest was skipped). Fix commit `78f1d782d2415ba8ded06401a6607ae6e56b5630`. Fresh run `45385683618` QUEUED.
- **PR #464:** run `45385289828` IN PROGRESS.
- **PR #465:** run `45385417961` IN PROGRESS.
- **PR #466:** run `45385598574` IN PROGRESS.
- No local pytest/Ruff run or physical-PC verification was performed in this invocation. No new PASS is claimed for PRs #462–#466.

## Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1 and Launcher evidence remain frozen as previously reviewed.
- Frozen ToolCall/PermissionGate, Memory v1, Observation Envelope v1, Personal Context privacy and existing V1/V2 contracts were not changed.
- UI/frontend development remains paused. PR #9 and existing Local UI/Launcher branches were not modified.
- PR #5 remains under its V3 gate; protected/frozen V2 evaluation was not opened. PR #8 remains Draft/unmerged. No main merge was attempted.

## Blockers and authorization boundaries

- All work remained within existing repository/GitHub workflows; no paid API, subscription, purchase, external GPU, Candidate weight generation, or paid compute was started.
- No credentials, new account connections, live personal data, real capture, hardware action, notification, external dispatch, destructive operation or irreversible change was performed.
- Synthetic SQLite hard-exit tests demonstrate process-exit recovery after a successful native COMMIT only. They do not prove fsync/power-loss durability, trusted time, authenticated consent, independent custody, cross-store atomicity or exactly-once external effects.
- CI is pending on the new child heads. The two initial failures above are recorded honestly and have narrow test-only fixes queued for fresh exact-head validation.
- No user confirmation is currently required; no protected gate or paid boundary was approached.

## Next plan / 今後の方針

1. **Close the current CI loop:** inspect the queued/running exact-head results for PRs #462–#466 once; fix only concrete failures, then immediately return to an independent lane while reruns execute.
2. **Integrate only validated foundations:** after exact-head GREEN and dependency review, consider the isolated test/evidence packages for the Draft #8 research branch. Keep all child PRs Draft until their evidence is complete; do not merge to `main`.
3. **Memory durability:** continue CAS/concurrency, coherent snapshot, event-frontier and expiry/purge recovery tests; preserve schema v1 and avoid claims beyond tested SQLite boundaries.
4. **Planner and authorization:** advance journal genesis/terminal commit-outcome recovery, audit-before-action and occurrence/replay protection; keep disconnected mock execution non-authorizing.
5. **Privacy and proactive/observation:** extend Personal Context revocation/replay lifecycle and proactive CAS/privacy tests; harden observation fixture budgets without connecting real capture.
6. **V3 free-only guards:** continue isolated approval/path/identity/reproducibility review without opening protected evaluation or promoting a Candidate.
7. **UI remains paused:** no frontend work unless explicitly resumed.
