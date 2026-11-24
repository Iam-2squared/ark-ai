# ARK AI — Canonical Project Status

## LATEST

- **Saved at:** 2026-11-25 05:53:35 JST (Asia/Tokyo)
- **Checkpoint branch / PR:** `research/jarvis-foundations` / Draft PR #8; isolated research branch, not `main`.
- **Exact work-basis HEAD:** `05d65aa006fb4d429abce70869d4271db5bed825` (PR #509 ActionAudit outcome-boundary regression/evidence package integrated into the PR #8 research branch).
- **Checkpoint-result HEAD:** the GitHub commit created by this `PROJECT_STATUS.md` update; the exact returned SHA is recorded in the run summary. This file does not self-reference its own commit SHA.
- **Overall ARK state:** V1, V2, Local UI v1 and Launcher/Gate Runner retain their previously reviewed/frozen PASS evidence. JARVIS core foundations continue in isolated, reversible research branches. **ARK/JARVIS overall remains NOT_PASSED.** No protected V2 evaluation was opened; no later milestone PASS is claimed.
- **Main remains unchanged by this invocation:** no merge to `main`.

## NEW work this invocation

1. **Draft PR #509 — ActionAudit outcome-boundary regressions integrated into PR #8**
   - Child exact HEAD: `d4fbc8dfefcdc6de3af1e7b3649722bf9e8299c9`.
   - Exact-head CI run `45474932797`: GREEN, 6/6 Windows/Linux × Python 3.11–3.13.
   - Integrated by squash merge into `research/jarvis-foundations`; resulting PR #8 work-basis HEAD: `05d65aa006fb4d429abce70869d4271db5bed825`.
   - PR #8 remains Draft/unmerged. Parent-head CI run `45483923713` is IN PROGRESS.

2. **Draft PR #507 — V3 preflight report-path validation integrated into PR #5**
   - Child exact HEAD: `1efb0d25f329035035921241acdd3b95fc9a406d`.
   - Exact-head CI run `45474021116`: GREEN, 6/6 Windows/Linux × Python 3.11–3.13.
   - Integrated by squash merge into `research/v3-learning-evaluation`; resulting PR #5 head: `f7252fbe7d5f65c640fed41bbb5b3cc7ae817296`.
   - PR #5 remains Draft/unmerged and its protected evaluation/training gates remain closed.
   - Parent-head CI run `45484069708` is FAIL. Retrieved job logs report Ruff I001 in three JARVIS test paths, but those paths were absent from the inspected tree for the reported head `f7252fbe7d5f65c640fed41bbb5b3cc7ae817296`. Treat this as an unresolved CI checkout/evidence mismatch; do not attribute it to PR #507 or claim a clean PR #5 head.

3. **Draft PR #510 — Memory query pre-access validation rebased onto current PR #8**
   - Exact child HEAD: `1cdf172797fbb32183ae779d854613fdf9dd89f5`.
   - Replays the narrow pre-SQLite query-epoch check, “during read” diagnostics, and synthetic str-subclass rejection tests.
   - CI run `45484412532`: IN PROGRESS.
   - Supersedes stale PR #505; its description was corrected to disclose the production-source change and stale base.

4. **Draft PR #511 — PermissionGate / ToolRegistry lookup-hook custody**
   - Exact child HEAD: `baaf80d9f4e54e26e2863d97222e51af7fa20049`.
   - Pins class/instance `__getattribute__` and optional `__getattr__` lookup hooks before registered authorization can invoke callbacks, iterate grants or consume a one-shot token.
   - CI run `45484936865`: IN PROGRESS.

5. **Draft PR #512 — Planner COMMIT-UNKNOWN recovery regressions**
   - Exact child HEAD: `28bd01428f6e3d8d9f3fc99d7138f2139d198836`.
   - Covers lost genesis/transition COMMIT acknowledgements, ambiguous RUNNING recovery, no automatic replay/dispatch, stale-transition conflicts and event-prefix truncation.
   - CI run `45485005891`: QUEUED.

6. **Draft PR #513 — Personal Context revocation exact-scope ingress**
   - Exact child HEAD: `cb9a7e7c0e06c9b939eb668628529fed3bb8e45a`.
   - Rejects non-exact owner/namespace text carriers before frozen MemoryScope validation, SQLite access or row writes.
   - CI run `45485106994`: QUEUED.

7. **Draft PR #514 — Proactive privacy fixture digest binding**
   - Exact child HEAD: `baaa0c0ec8d5b862de0be6dda3bb95c44823d859`.
   - Binds the synthetic private observation's actual SHA-256 digest through the hard-exit child process and checks the recovered digest.
   - CI run `45485244434`: QUEUED.

## Tests, CI and evidence

- PR #509 child run `45474932797`: GREEN, 6/6; integrated into PR #8 at work-basis HEAD `05d65aa006fb4d429abce70869d4271db5bed825`.
- PR #8 exact current-head run `45483923713`: IN PROGRESS.
- PR #507 child run `45474021116`: GREEN, 6/6; integrated into PR #5 at head `f7252fbe7d5f65c640fed41bbb5b3cc7ae817296`.
- PR #5 current-head run `45484069708`: FAIL; Ruff I001 is reported in the downloaded logs, with an unresolved mismatch between the reported paths and the inspected commit tree.
- PR #510 run `45484412532`: IN PROGRESS.
- PR #511 run `45484936865`: IN PROGRESS.
- PR #512 run `45485005891`: QUEUED.
- PR #513 run `45485106994`: QUEUED.
- PR #514 run `45485244434`: QUEUED.
- Historical predecessor runs for PR #500–#503 and #505 were GREEN on their old heads only; none of those results transfers to the new rebased child heads.
- PR #508 run `45474394318`: FAIL during pytest collection with missing `ark.personal_context_offline_preview` and `ark.agency` imports on the V3 branch. Those modules belong to the separate JARVIS foundation branch; do not weaken the tests or copy them into V3 merely to silence the failure.
- No local pytest/Ruff result, physical-PC verification, real model runtime, paid compute or external service action is claimed in this invocation.

## Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1 and Launcher/Gate Runner evidence remain frozen as previously reviewed.
- Frozen ToolCall/PermissionGate public contracts, Memory v1 schema/DDL, Observation Envelope v1, Personal Context privacy boundaries and V3 Contract 1 were not changed.
- PR #5 remains Draft/unmerged; no protected V2 evaluation, real Candidate generation or promotion was opened.
- PR #8 remains Draft/unmerged; this checkpoint and child packages do not merge to `main`.
- PR #9 remains Draft/unmerged and untouched. UI/frontend development remains paused.

## Blockers and authorization boundaries

- **Free-only boundary:** no paid/external GPU, paid API/service, subscription, purchase or potentially billable action was started.
- No real Candidate adapter/weight generation, protected V2 final-evaluation opening, Candidate promotion, credentials/secrets, new account connection, unavailable physical-PC action, destructive operation or irreversible data change occurred.
- PR #5 parent CI failure and PR #508's V3/JARVIS dependency mismatch remain explicit blockers; neither is hidden by the green child-head results.
- SQLite process-exit/COMMIT-UNKNOWN tests establish only the specific synthetic native-COMMIT recovery boundaries exercised. They do not prove power-loss/fsync durability, trusted time, independent custody, authenticated consent, cross-store atomicity or exactly-once external effects.
- No automatic promotion, real backend dispatch or human-review decision is inferred from test results.

## Next plan / 今後の方針

1. Inspect exact-head CI for PRs #510–#514 and PR #8 once useful results are available; fix only concrete failures, then switch to an independent non-conflicting lane while reruns execute.
2. After exact-head GREEN and dependency review, integrate validated child packages into the PR #8 research branch only. Keep PR #8 Draft/unmerged and preserve exact-head evidence.
3. For PR #5, reconcile run `45484069708` against the exact checkout/tree and reported Ruff paths before making any correction. Keep PR #5 Draft/unmerged and do not open protected evaluation or training gates.
4. Keep the V3/JARVIS test dependency boundary explicit. Re-home JARVIS-only tests to the foundation branch where their source modules exist; do not weaken tests or make V3 depend on an unproven foundation merge.
5. Continue independent free-only work on Observation fixture byte/lineage guards, startup readiness leases, occurrence/replay protection and disconnected mock execution.
6. Keep UI paused; no frontend features, polish, tests or integration.

## Historical checkpoint archive

### LATEST

- **Saved at:** 2026-11-24 20:40:23 JST (Asia/Tokyo)
- **Checkpoint branch / PR:** `research/jarvis-foundations` / Draft PR #8; this is an isolated research branch, not `main`.
- **Exact work-basis HEAD:** `ddc4a574437361059552615ceb44936a628555dc` (Run1280 Planner terminal hard-exit regression integration).
- **Checkpoint-result HEAD:** the GitHub commit created by this `PROJECT_STATUS.md` update; its exact returned SHA is verified after the write and reported in the run summary. This file does not self-reference its own commit hash.
- **Overall ARK state:** V1, V2 and Local UI v1 retain their reviewed/frozen PASS evidence. JARVIS foundations continue in isolated, reversible research branches. **ARK/JARVIS overall remains NOT_PASSED.** No V3+ protected evaluation was opened and no later milestone PASS is claimed.

### NEW work this invocation

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

### Tests, CI and evidence

- **Foundation basis:** PR #460 merge commit `ddc4a574437361059552615ceb44936a628555dc`; exact-head CI run `45379837623` was GREEN, 6/6 jobs. This is the current research-branch basis, not a main merge.
- **PR #462:** run `45382547475` FAIL (Ruff passed; pytest had 2 expectation failures, 19,472 passed and 151 skipped in the observed Windows/Python 3.11 job). Test-only correction committed at `31ac179ffef6fc536f45b2e8d580d259e36df151`; evidence doc added at `7b71f62204a293cb5c978b6524aec3d64d95ea97`. Fresh run `45385945866` QUEUED.
- **PR #463:** run `45385180828` FAIL (Ruff F401 only; pytest was skipped). Fix commit `78f1d782d2415ba8ded06401a6607ae6e56b5630`. Fresh run `45385683618` QUEUED.
- **PR #464:** run `45385289828` IN PROGRESS.
- **PR #465:** run `45385417961` IN PROGRESS.
- **PR #466:** run `45385598574` IN PROGRESS.
- No local pytest/Ruff run or physical-PC verification was performed in this invocation. No new PASS is claimed for PRs #462–#466.

### Frozen contracts and evidence — unchanged

- V1 Local Core, V2 real-model baseline, Local UI v1 and Launcher evidence remain frozen as previously reviewed.
- Frozen ToolCall/PermissionGate, Memory v1, Observation Envelope v1, Personal Context privacy and existing V1/V2 contracts were not changed.
- UI/frontend development remains paused. PR #9 and existing Local UI/Launcher branches were not modified.
- PR #5 remains under its V3 gate; protected/frozen V2 evaluation was not opened. PR #8 remains Draft/unmerged. No main merge was attempted.

### Blockers and authorization boundaries

- All work remained within existing repository/GitHub workflows; no paid API, subscription, purchase, external GPU, Candidate weight generation, or paid compute was started.
- No credentials, new account connections, live personal data, real capture, hardware action, notification, external dispatch, destructive operation or irreversible change was performed.
- Synthetic SQLite hard-exit tests demonstrate process-exit recovery after a successful native COMMIT only. They do not prove fsync/power-loss durability, trusted time, authenticated consent, independent custody, cross-store atomicity or exactly-once external effects.
- CI is pending on the new child heads. The two initial failures above are recorded honestly and have narrow test-only fixes queued for fresh exact-head validation.
- No user confirmation is currently required; no protected gate or paid boundary was approached.

### Next plan / 今後の方針

1. **Close the current CI loop:** inspect the queued/running exact-head results for PRs #462–#466 once; fix only concrete failures, then immediately return to an independent lane while reruns execute.
2. **Integrate only validated foundations:** after exact-head GREEN and dependency review, consider the isolated test/evidence packages for the Draft #8 research branch. Keep all child PRs Draft until their evidence is complete; do not merge to `main`.
3. **Memory durability:** continue CAS/concurrency, coherent snapshot, event-frontier and expiry/purge recovery tests; preserve schema v1 and avoid claims beyond tested SQLite boundaries.
4. **Planner and authorization:** advance journal genesis/terminal commit-outcome recovery, audit-before-action and occurrence/replay protection; keep disconnected mock execution non-authorizing.
5. **Privacy and proactive/observation:** extend Personal Context revocation/replay lifecycle and proactive CAS/privacy tests; harden observation fixture budgets without connecting real capture.
6. **V3 free-only guards:** continue isolated approval/path/identity/reproducibility review without opening protected evaluation or promoting a Candidate.
7. **UI remains paused:** no frontend work unless explicitly resumed.

