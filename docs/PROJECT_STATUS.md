# ARK AI Project Status

**LATEST — Run 369**

Saved at: **2026-10-24T02:03:07.518+09:00 Asia/Tokyo/JST** (clock captured immediately before the normal GitHub Contents API checkpoint write).

Branch/PR: `research/jarvis-foundations` / **Draft, unmerged PR #8**.
Exact work-basis HEAD: `09d5397cbc6d8b1776c09ae5d9362da6af298d35` (Run 368 checkpoint; CI #411 / run `39982454067`, SUCCESS).
Exact final **source/test/fix** HEAD: `2f7d3b2412ce674922be6fa5c7388edaa1fb8600` (CI #423 / run `39991275039`, **SUCCESS 6/6**).
Work-basis HEAD for this checkpoint write (including reviewed engineering documentation): `8d661e89f8d75b17bb403f3ab54f23a130acb144` (CI #424 / run `39991332239`, **SUCCESS (aggregate; job matrix not separately rechecked)** at timestamp above).
**Checkpoint-result HEAD can only be read from the resulting GitHub Contents API response.** This self-referential document must never assert its own unborn commit SHA or claim prior CI validates that later commit.

## Overall ARK state

Research remains **local-first, synthetic/disconnected, Draft and reversible**. PR #8 is not a production tool authority; no real backend execution, human-approved permission, credential access, external attestation, trusted-clock proof, cross-store atomic transaction or real-world Exactly-Once guarantee. Main at latest observed `7a843f17eb96ed13d66f23b58b06406b3002e405`. V3 PR #5 remains Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`, **NOT_PASSED**. Frozen V1/V2/Local UI/Launcher contracts, final-evaluation boundaries, and prior evidence unchanged.

## NEW work — Run 369 (four packages plus documentation)

Four source/test packages, **33 new parametrized pytest cases** and an additional disconnected review module. Thirteen sequential normal GitHub Contents commits before this checkpoint, including narrow CI-driven fixes; two grounded engineering documentation updates. No raw Git objects, force push or concurrent overwrite. Each write re-read the latest branch HEAD.

1. **Persisted synthetic occurrence integrity (10 cases):** `agency/durable_occurrence_review.py` validates stored token/occurrence/registry/bound-action/request canonical identities and exact SQLite INTEGER reservation/expiry ordering; refuses malformed stored rows before open/read/new reserve, with bounded 10,000-row fixture review. Existing fixture v1 schema remains unchanged. Valid-looking malicious rewrites remain possible without independent evidence.
2. **Synthetic readiness graph recomputation (8 cases):** `startup_readiness_review.py` reconstructs effective dependency states and validates references, cycles and identifiers before serving a cached snapshot; tests demonstrate that even a recomputed matching local digest does not excuse contradictory dependency states. This is internal consistency, not trusted device or backend readiness.
3. **Canonical Planner review digests (7 cases):** `PlanGraph.topology_digest()` binds step IDs, request identities and dependency tuples; `status_digest()` also binds all explicit and derived status/revision values. Deterministic across step registration order, not a durable journal, synchronized snapshot or execution authority.
4. **Independently retained synthetic ledger witnesses (8 cases):** new `agency/synthetic_occurrence_continuity_review.py` reads SQLite read-only and compares canonical row hashes against a prior externally retained local witness. Append/reopen succeeds; row truncation/rewrite and missing DB fail closed. A witness recomputed after storage tampering is **not** independent evidence. No bearer-token plaintext, real dispatch or side effects.
5. **Research docs:** `docs/JARVIS_SYNTHETIC_AUTHORIZATION_AND_READINESS.md` and `docs/PLANNER_RECOVERY.md` document implemented boundaries and the still-open journal/issuer/clock/authorization gates.

## Exact-head CI / evidence

- Intermediate CI #412 / run `39989852639`: FAIL on its partial implementation head. #413 / `39989984038`, #414 / `39990077167`, #415 / `39990150908`: SUCCESS at their respective earlier heads.
- Intermediate CI #416 / `39990404221` and #417 / `39990502590`: FAIL (Planner Ruff I001 helper spacing), fixed normally at `5b43e1deabeee29c939b10ef3c7466be2a54a3ae`; CI #418 / `39990606202`: SUCCESS.
- CI #419 / `39990821422` and #420 / `39990872429`: SUCCESS at earlier review-module heads.
- CI #421 / `39990958955` and #422 / `39991118800`: FAIL on Windows-only fixture filename with a forbidden `?` character; test switched to cross-platform legal `%` at `2f7d3b2412ce674922be6fa5c7388edaa1fb8600`. These failed runs remain historical failures.
- **Final source/test/fix CI #423 / run `39991275039`: SUCCESS GREEN 6/6** on Ubuntu and Windows, Python 3.11/3.12/3.13. All six job conclusions explicitly checked. Ubuntu Python 3.13 job `120543351947`: **Ruff all checks passed; pytest 657 passed in 3.88s**. Node, V2 and model evaluations remain mock/fixture-only.
- Post-source documentation CI #424 / run `39991332239`: **SUCCESS (aggregate; job matrix not separately rechecked)** at snapshot time. Its result does not attest the subsequent checkpoint commit. This checkpoint commit CI is unknown until checked independently.

## Frozen / free-only / permission boundaries

No paid or potentially billable external compute, new paid API, GPU, subscription, Candidate adapter/weight, training, protected V2 final evaluation, promotion, human-review fabrication, secret/account connection, destructive migration, real Tool Backend invocation, user notification, or main merge. PR #5 stays Draft/NOT_PASSED. Synthetic token hashes are **not** credential storage; review digests are **not** signatures; internal reservation at-most-once is **not** external exactly-once execution.

## Next plan / 今後の方針

1. **P0 verify exact checkpoint-result HEAD and subsequent CI** separately. Repair only observed failures through normal writes and preserve failing-run evidence.
2. **P0 durable authorization & execution occurrence:** issuer/subject/purpose/capability/scope/recipient and trusted-clock attestation, registry-bound token identity, audit-before-mock-action, crashed/UNKNOWN WRITE recovery without replay. No real WRITE backend.
3. **P0 durable Planner recovery:** transition journal with deterministic topology/post-state digests, atomic tail anchor and an **independently retained witness**, CAS, interruption classification, multi-process crash tests; keep external effects disconnected.
4. **P1 SQLite/Memory/ActionAudit:** provenance and event-row integrity, cross-process sustained lock faults, coherent CAS snapshots; leave frozen schema/contracts intact.
5. **P1/P2 Personal Context/Scheduler/Observation/Startup:** scoped consent/revocation, occurrence replay budgets, privacy retention, safe startup gates, mock fixture adapters. V3 remains free-only guard reviews; protected and billable paths closed.

---

**HISTORICAL — Run 368 and earlier**

**LATEST — Run 368**

Saved at: **2026-10-24T00:55:34.338+09:00 Asia/Tokyo/JST** (captured immediately before this normal GitHub Contents API write).

Branch/PR: `research/jarvis-foundations` / **Draft, unmerged PR #8**.
Exact work-basis HEAD: `f15764523c9881a6733ad1c471eb1b74b95227a6` (Run 367 checkpoint; CI #401 / run `39974425746`, SUCCESS 6/6).
Exact final **source/test/fix** HEAD: `5203783219bac0f21a9472fa24628a92f4698de4` (CI #409 / run `39981945402`, SUCCESS 6/6).
Work-basis HEAD for this checkpoint write (includes independent engineering safety documentation): `8e0f1226bd144f4051f307abb262873307e74bf4` (CI #410 / run `39982174567`, **IN PROGRESS at last check**).
**Checkpoint-result HEAD is determined only by the GitHub Contents API response**, not by this self-referential file. The source/test GREEN #409 cannot be attributed to the later documentation or checkpoint commits.

## Overall current ARK state

ARK remains an isolated, reversible local-first JARVIS foundations research branch. It is **NOT** authenticated consent, trusted issuer/clock, credential access, trusted real-world Tool dispatch, externally attested audit, real-world Exactly-Once execution or complete JARVIS. Frozen V1/V2/Local UI/Launcher contracts, protected evaluation boundaries and evidence remain unchanged. `main` at observed base `7a843f17eb96ed13d66f23b58b06406b3002e405`; V3 PR #5 is still Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`, **NOT_PASSED**.

## NEW work this invocation — Run 368

**Three source-and-regression packages plus an independent safety/integration specification.** Nine sequential commits before this checkpoint (including one implementation correction and one CI-driven Ruff fix). **33 new parametrized pytest cases**, Ubuntu Python 3.13 count **624/624 PASS** on the exact source/test/fix HEAD. Each write re-read the exact PR HEAD, with no force-push, raw Git objects, protected merge or concurrent overwrite.

1. **Cached readiness witness integrity (11 new cases):** `src/ark/startup_readiness_review.py` now recomputes and validates the local content digest and structural invariants before answering `state()` or `root_blockers()`. Reflected mutation to a previously evaluated `ComponentResult`, dependency list, ordering or snapshot digest is refused rather than returning a stale READY state. Test: `tests/test_startup_snapshot_integrity_run368.py`. This is local consistency of synthetic probes, not attested startup readiness or external authenticity.
2. **Durable synthetic occurrence reservation (17 new cases):** new disconnected `src/ark/agency/durable_occurrence_review.py` stores an artificial token digest and canonical registry-bound occurrence identity through SQLite `BEGIN IMMEDIATE`. Duplicate token and duplicate occurrence are refused across store objects and restarts, with thread contention, schema drift, missing file, invalid time, expiry and READ-effect cases. Receipts explicitly deny dispatch/replay and have unknown action outcome. No backend executed, issuer verified, external side effect attempted or real consent established. Test: `tests/test_durable_occurrence_review_run368.py`.
3. **PermissionGate under-lock epoch revalidation (5 new cases):** `src/ark/agency/policy.py` rechecks the original spec, call, token and every grant immediately before process-local token spend, even when the token lock was contended after grant iteration. Deterministic fake-lock interleavings prove forged grant/spec changes are rejected without spending. Test: `tests/test_policy_spend_lock_epoch_run368.py`. Not restart-safe real-world authorization.
4. **Boundary and crash-model evidence:** `docs/JARVIS_SYNTHETIC_AUTHORIZATION_AND_READINESS.md` fixes explicit negative guarantees, reservation/UNKNOWN crash semantics, local digest limitations and all promotion blockers. This document does not authorize activation.

## Exact-head CI / evidence

- Intermediate **CI #403 / run `39981225966`: FAIL**, and **CI #406 / run `39981596963`: FAIL**, because `tests/test_startup_snapshot_integrity_run368.py` contained an unused `dataclasses.replace` import (Ruff F401). This was removed by normal commit `5203783219bac0f21a9472fa24628a92f4698de4`. Earlier failed runs remain FAILED.
- **Final exact source/test/fix CI #409 / run `39981945402`: SUCCESS 6/6 GREEN** on Ubuntu/Windows, Python 3.11/3.12/3.13. All six job conclusions were checked. Ubuntu Python 3.13 job `120511203205`: Ruff **All checks passed**, pytest **624 passed in 5.45s**. Node/Local UI and V2 evaluations are mock-only; real JARVIS effects remain unmeasured.
- CI #410 / run `39982174567` for documentation HEAD `8e0f1226bd144f4051f307abb262873307e74bf4`: **IN PROGRESS** at last verification; do not declare it GREEN without new evidence.
- This checkpoint commit's CI is unknown while this file is written; resolve its exact resulting SHA/run separately.

## Frozen contracts / authorization boundaries

No paid/potentially billable service, external GPU, paid API, model training, real Candidate/weight/adapter generation, protected V2 final evaluation, automatic promotion, frozen-contract edit, new secrets/accounts, physical PC action, irreversible migration, real Tool backend execution, notification send or main merge. PR #5 stays Draft/NOT_PASSED. Fixture SQLite integrity is not external attestation; SHA-256 token digest is not a secret-management system; local observation cannot certify a real issuer, clock, consent, end-to-end transaction or true exactly-once side effect.

## Next plan / 今後の方針

1. **P0 verify exact checkpoint HEAD and CI** when available; never infer success from earlier commit runs. Diagnose and fix only observed errors.
2. **P0 durable authorization prerequisites:** canonical occurrence/registry/issuer evidence, trusted-clock and purpose/subject/recipient binding, synthetic-only crash injection and independent persisted continuity witness; keep all real WRITE paths disconnected.
3. **P0 SQLite/Memory:** cross-process first-open and sustained lock fault tests, exact schema/row/event identity, coherent snapshot and CAS regression without modifying frozen v1.
4. **P1 Planner/ActionAudit:** durable transition journal and external retained-tail evidence, unknown WRITE reconciliation without blind retry, audit-before-mock-action fault simulation. Do not claim atomicity across databases.
5. **P1/P2 privacy and proactive foundations:** scoped consent/revocation/expiry, scheduler occurrence replay budget, observation provenance/retention, startup readiness with trusted probes only after separate approval. V3 remains free-only approval/path/identity/reproducibility guarding; all paid/protected gates closed.

---

**HISTORICAL — Run 367 and earlier**

**LATEST — Run 367**

Saved at: **2026-10-23T23:59:50.284+09:00 Asia/Tokyo/JST** (sampled immediately before this normal GitHub Contents API update).

Branch/PR: `research/jarvis-foundations` / **Draft, unmerged PR #8**.
Exact work-basis HEAD: `3e32d772e96aad741dd6eeb849b90e877864d842` (CI #390 / run `39966036952`, SUCCESS 6/6).
Exact final **source/test/fix** HEAD before this checkpoint: `ba6626838e65b6ff8ddad46fae03b7b9d425ac3e`.
Checkpoint-result HEAD: this text cannot know the SHA that will commit it; the **GitHub Contents API response is authoritative**. CI #400 validates the source/test/fix HEAD above, **not** this later checkpoint commit.

## Overall current ARK state

ARK remains an isolated/reversible local-first JARVIS foundations **Draft research** branch, NOT trusted real-world Tool dispatch, authenticated consent, durable real-world Exactly-Once, external audit attestation, validated human approval or complete JARVIS. Frozen V1/V2/Local UI/Launcher contracts, evidence and protected evaluation gates remain unchanged. `main` remains `7a843f17eb96ed13d66f23b58b06406b3002e405`; V3 PR #5 stays Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`, **NOT_PASSED**.

## NEW work this invocation — Run 367

**Four coherent free/local-only packages, ten sequential normal GitHub Contents commits (including two Ruff import-style fixes), three modified existing sources, one new isolated review module and four new regression-test files. New cases: 19; Ubuntu 3.13 pytest: 591/591 PASS.** No raw Git objects, force-push or main merge. Each GitHub write re-read the exact branch HEAD; no concurrent changes were overwritten.

1. **Memory cross-process WAL bootstrap (2 new cases):** `src/ark/memory/sqlite_store.py` uses bounded, SQLite-error-code-specific BUSY/LOCKED retries for PRAGMA journal-mode negotiation during initialization, requires actual `wal` result, then preserves the existing `BEGIN IMMEDIATE` atomic v1 schema gate. Multi-process independent first-open regression spawns four local child Python processes in two iterations. No WAL renegotiation on ordinary read/write.
2. **Process-local PermissionGate atomic token consumption (3 new cases):** `src/ark/agency/policy.py` protects one-shot membership-check+spend with a lock, rechecks request/token identity after lock acquisition, and refuses replay. Deterministic forced interleaving verifies exactly one allowed concurrent decision; distinct tokens remain independent. **This is process-local diagnostic safety, NOT durable, issuer-attested authorization or real WRITE permission.**
3. **ActionAudit WAL bootstrap hardening (4 new cases):** `src/ark/agency/audit.py` moves persistent WAL negotiation from routine `_connect()` to serialized startup, uses bounded SQLite lock retries, validates actual WAL mode and retains transactionally validated schema v1. Tests cover routine connection during another writer's transaction, same-process initializers, and cross-process first opens. No real Tool backend was invoked.
4. **Disconnected deterministic startup readiness (10 new cases):** new `src/ark/startup_readiness_review.py` accepts exact synthetic component probes, rejects duplicate/unknown/self/cyclic edges and invalid local states, deterministically propagates dependency-blocked states, and returns an immutable content-minimized startup witness with root-blocker diagnostics. 250 randomized order permutations, isolated lane failures and a 1,500-dependency graph are tested. **No store/credential probing, capability activation, true readiness certification or actual startup wiring.**

## Exact-head CI / evidence

- Initial source-only heads #391–#393 (runs `39972756818`, `39972885474`, `39972973188`): SUCCESS. These do not validate later new test files.
- CI #394–#397: FAIL at intermediate heads due to Ruff I001 import formatting of two new module-level fixture constants; fixed via sequential normal commits `0522a8cd489c4cfccc28b14234341efdc0b0af9f` and `d785eba149f9022e78163c3c8138e687735015c7`. These failures remain explicitly failed, never retroactively green.
- CI #398 / run `39973640168` and #399 / run `39973848558`: SUCCESS 6/6 at their respective intermediate HEADs.
- **Final source/test CI #400 / run `39973947231`: SUCCESS 6/6 GREEN** at exact HEAD `ba6626838e65b6ff8ddad46fae03b7b9d425ac3e` on Ubuntu/Windows Python 3.11/3.12/3.13; all six job conclusions explicitly checked. Ubuntu Python 3.13 job `120483557335`: **Ruff PASS, pytest 591/591 PASS**. Tests remain synthetic/disconnected; this is not real action authority.
- The **checkpoint commit's own CI is not known while this file is being written**. Verify the resulting HEAD/run separately; never attribute #400 to the checkpoint.

## Frozen contracts / authorization boundaries

No paid/potentially billable service, external GPU, paid API, training, real Candidate weights/adapters, protected V2 final evaluation, V3 promotion, frozen contract edit, new credentials/accounts, physical-PC operations, irreversible migration, real Tool Backend execution, notification send, or main merge. PR #5 stays Draft/NOT_PASSED. SQLite WAL retry is bounded and does not guarantee survival of arbitrary sustained contention. Startup readiness is synthetic and cannot authenticate a probe; the Policy lock is process-local and is not restart-safe exactly-once or human consent.

## Next plan / 今後の方針

1. Independently verify **this checkpoint's exact result HEAD and CI**, preserving attribution of #400 exclusively to the pre-checkpoint source/test head.
2. **P0 durable authorization:** registry-bound occurrence+token ledger with verified issuer identity, trusted clock and restart/crash/concurrent replay tests; prototype synthetic-only until explicit user authorization gates. Keep every real WRITE backend disconnected.
3. **P0 SQLite reliability:** verify bounded cross-process WAL bootstrap under injected busy faults and persistent lock contention; examine exact same-version schema/row/event integrity and external witness limitations without changing frozen schema v1.
4. **P1 Planner recovery and ActionAudit:** durable transition journal and independent tail witness, UNKNOWN WRITE reconciliation without blind retry, audit-before-mock-action and fault injection; no cross-database atomicity claims.
5. **P1/P2 startup/Personal Context/Scheduler/Observation:** connect reviewed readiness model only to independently validated probe results, keeping effects disabled; privacy-safe consent/revocation/expiry, proactive occurrence guards, observation provenance/retention. V3 remains free-only approval/path/identity/reproducibility guards; protected/paid gates closed.

---

**HISTORICAL — Run 366 and earlier**

**LATEST — Run 366**

Saved at: **2026-10-23T23:00:55.330 JST (+09:00)** (sampled immediately before this normal GitHub Contents API update).

Branch/PR: `research/jarvis-foundations` / **Draft, unmerged PR #8**.
Exact work-basis HEAD: `aa6e3cda3d1bd839c713e5e6c405a8b58b6821f5` (CI #371 / run `39957436229`, SUCCESS 6/6).
Exact final **source/test/fix** HEAD before this checkpoint: `c21d82a9d49c43b0185f87944cdd2fc333b777a5`.
Checkpoint-result HEAD: this file cannot predict its own committing SHA; the **GitHub Contents API response is authoritative**. CI #389 validates the preceding source/test/fix HEAD, **not** this checkpoint commit.

## Overall current ARK state

ARK's JARVIS foundations remain isolated/reversible, local-first Draft research, **not** authenticated real-user consent, live Tool dispatch, durable real-world Exactly-Once execution, externally attested audit, trusted wall-clock authority or complete JARVIS. Frozen V1/V2/Local UI/Launcher and protected evaluation contracts/evidence remain unchanged. `main` remains `7a843f17eb96ed13d66f23b58b06406b3002e405`; V3 PR #5 remains Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`, **NOT_PASSED**. No Candidate, protected V2 evaluation opening, promotion or paid/external GPU compute.

## NEW work this invocation — Run 366

**Five coherent implementation/test packages, plus CI-driven semantics-preserving fixes: 18 sequential normal GitHub Contents commits before this checkpoint; 55 new parametrized pytest cases; six modified source files and six new regression-test files.** Re-read latest PR HEAD before each write; did not use raw Git objects, force-push, paid services or main merge.

1. **Memory signed-64-bit boundaries (18 tests):** `MemoryWrite.expires_at_ms`, injected clock values, CAS expected revisions, event cursor and revision increment exhaustion are fail-closed at SQLite INTEGER limits. Maximum valid timestamp remains allowed; overflow does not change rows or event journal. Tests: `test_memory_sqlite_integer_boundaries_run366.py`. Existing schema v1 unchanged.
2. **Planner atomic terminal cascade (8 tests):** collect pending descendants and preflight every revision before publishing any explicit or derived BLOCKED state. Exhausted descendants reject the entire transition without partially changing unrelated or earlier steps, preserving linear graph traversal. Tests: `test_planner_atomic_terminal_cascade_run366.py`. No persistent planner journal or backend execution.
3. **PermissionGate time bounds (13 tests):** synthetic `CapabilityGrant`, `OneShotAuthorization` and policy `now_ms` reject invalid/out-of-range times before any process-local write token is consumed; maximum-range normal decisions preserved. Tests: `test_policy_sqlite_time_bounds_run366.py`. **Not** durable authorization or trusted-clock verification.
4. **Content-free Memory coherent snapshot witness v2 (4 tests):** review digest now also binds canonical metadata SHA-256, creation time and expiry as well as existing revision/content/update fields. SQLite Memory v1 schema stays version 1; only the reversible review witness format increments to 2. Synthetic metadata/expiry edits cannot reuse an identical witness. Tests: `test_memory_snapshot_witness_lifecycle_run366.py`. A local digest is not external attestation.
5. **Memory get/search coherent clock epoch (10 tests):** scope/query inputs pinned, SQLite read snapshot anchored before reentrant clock callback, and reflected retargeting rejected. Concurrent synthetic writer does not produce a mixed epoch or partially disclosed search context. Preserves legacy scope-specific exception wording. Tests: `test_memory_get_search_snapshot_epoch_run366.py`.
6. **CI-driven Memory WAL connection remediation (2 tests):** actual CI #373 and #381 intermittently reported `sqlite3.OperationalError: database is locked` during two-initializer fixture. Ordinary `_connect()` no longer renegotiates persistent journal mode on each read/write; WAL setup is serialized for same-process bootstrap and initial schema creation still uses SQLite `BEGIN IMMEDIATE` for writer ownership. Tests: `test_memory_wal_first_open_run366.py`. The extra bootstrap mutex is **process-local**: cross-process first-open robustness is not yet proven.

## Exact-head CI / evidence

- Intermediate **CI #373 / run `39963871840`** and **#381 / run `39964600885`**: FAIL in intermittent Memory two-initializer SQLite lock regression. These failures are not treated as GREEN.
- **CI #383 / run `39964926053`**: FAIL for existing Memory search-scope exception-text compatibility; corrected by `97b9c8717335feec18e989ec28cc2f760ef3217d` and focused test follow-up `492e22475dfb1ffc3b4a8c77dfe85da013500866`.
- **CI #385 / run `39965299967`**: FAIL Ruff I001/B023 in WAL fix and new thread fixture; corrected with source `c4dd69f46a858780992630e4bc882a25db67145a` and test `c21d82a9d49c43b0185f87944cdd2fc333b777a5`.
- **Final source/test CI #389 / run `39965575640`: SUCCESS 6/6 GREEN** at exact HEAD `c21d82a9d49c43b0185f87944cdd2fc333b777a5` for Ubuntu/Windows Python 3.11, 3.12 and 3.13. Ubuntu Python 3.13 logs: **Ruff PASS, pytest 572/572 PASS**; Local UI/Node and evaluation remain mock-only. Six job statuses were checked explicitly. CI #389 is not evidence for the later checkpoint commit.
- **This checkpoint commit's own CI cannot be known until GitHub writes/starts that run**; verify result HEAD/run independently.

## Frozen contracts / authorization boundaries

No potentially billable services, paid APIs, external GPU, secrets/account connections, physical-PC actions, irreversible migrations, frozen-contract edits, real Candidate/weights, protected V2 evaluation, promotion, real Tool Backend execution, notification sends, or main merge. PR #5 stays Draft/NOT_PASSED. Snapshot witnesses are locally derived; the process-local WAL mutex cannot claim multi-process attestation; untrusted application code remains outside a sandbox; real-world Exactly-Once and consent provenance are unproven.

## Next plan / 今後の方針

1. Verify this checkpoint's **own result SHA and CI** independently; #389 validates only the pre-checkpoint source/test HEAD.
2. P0 Memory: follow up cross-process WAL first-open race and same-version schema/read-time integrity; complete trusted-clock ownership and CAS/coherent snapshot interaction tests without changing frozen v1 semantics.
3. P0 Registry/Permission: durable registry-bound occurrence/token ledger with exact issuer provenance and restart/crash/concurrent replay tests, disconnected-only; no real WRITE dispatch.
4. P1 Planner/ActionAudit: SQLite transition journal, independently retained tail witness, UNKNOWN WRITE reconciliation (no blind retry), audit-before-mock-action and crash injection.
5. P1/P2 Personal Context/Scheduler/Observation/Startup: scoped consent/revocation/expiry, deterministic scheduler attention and retention, privacy lifecycle, readiness dependency gates. V3 remains approval/path/identity/reproducibility guards only; all paid/protected gates shut.

---

**HISTORICAL — Run 365**

Saved at: **2026-10-23 21:58:31.668 JST (+09:00)** (sampled immediately before this normal GitHub Contents API checkpoint update).

Branch/PR: `research/jarvis-foundations` / **Draft, unmerged PR #8**.
Exact work-basis HEAD: `2ce198bb206dd9e865a10a8bab357e6eccc77277` (CI #357, run `39950206134`, SUCCESS 6/6).
Exact final **source/test/fix** HEAD before this checkpoint: `ece9421fe35b851c238797fae3b392750b709965`.
Checkpoint-result HEAD: this file cannot predict its own Git commit SHA; the **GitHub Contents update response is authoritative**. CI #370 validates the preceding final source/test HEAD, not this later checkpoint commit.

## Overall current ARK state

The JARVIS foundations remain isolated local-first Draft research, **not** trusted live dispatch, authenticated consent, durable external action identity, external audit attestation, real-world exactly-once, or finished JARVIS. Frozen V1/V2/Local UI/Launcher contracts, evidence, and protected evaluation boundaries remain unchanged. `main` remains `7a843f17eb96ed13d66f23b58b06406b3002e405`. V3 PR #5 remains Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`, **NOT_PASSED**.

## NEW work this invocation — Run 365

**Five coherent free/synthetic-only packages; 13 sequential normal GitHub Contents commits including one lint-only correction; 44 new parametrized pytest cases; seven modified source files and five new regression-test files.** Latest PR HEAD was re-read immediately before every write; no raw Git objects, force-push, or main merge.

1. **Memory atomic bootstrap**: source `da7914426d29f3f8b2a13703d3fd8902c985e75b`, tests `b0e13d122ce1ff0bad9cae3a6ef946b36d68906e` (6 cases), Ruff E501-only test correction `ee7bbf181b406a3bb8878a04ba13e27a73a55e09`. Acquire `BEGIN IMMEDIATE`, reject negative/occupied version-zero schema, create frozen v1 DDL statement-by-statement with transaction rollback on verification failure. Synthetic two-initializer convergence; **no migration or auto-repair**.
2. **Observation exact SQLite-range ingestion timestamp**: source `6d4a77b92d619528b4315701cb13feb1f0753afe`, tests `d9e68f1bd660e497ae9c8ee51f00825be00c17a2` (7 cases). Reject invalid/out-of-range observed inputs without changing the frozen small-time identity vector or accessing media.
3. **ActionAudit read-only event reader**: source `d2345fa4e0efb4da217ea07e0cdf50a3db86c79b`, tests `a1b87ccab9e20a7bf2d598f9c846cbaaabfd4291` (4 cases). `events()` opens local SQLite `mode=ro` and refuses a vanished file rather than creating an empty replacement; correctly handles percent-encoded local paths. No external audit provenance claim.
4. **Planner signed-64-bit revision guards**: contracts source `25e7f6cff6ac7d1abb7622135651d633b08cacbd`, planner source `2e039487b27311c72d35b1141fdd6cbbdf4ff4e0`, tests `d1896a2da87cd34a69f172f42c0df10808a3fad7` (12 cases). Bound status/expected revision and fail closed at terminal increment without changing normal in-memory plan transitions or enabling execution.
5. **Observation scoped-window/rollover integer bounds**: window source `53bc72e8ee9ebe528aeeacb0f710dfcd5fc967c2`, rollover source `4214ce2df2b45847302aacf0ddd270a07e05cccb`, tests `ece9421fe35b851c238797fae3b392750b709965` (15 cases). Reject invalid/unbounded window sample time, retention budget, and rollover timestamp. No camera, microphone, notification, or actual capture.

## Exact-head CI / evidence

- CI **#358** / run `39955999137`: SUCCESS on bootstrap source-only head.
- CI **#359–#363**: FAIL at their respective interim HEADs due to **Ruff E501** in the new Memory concurrency test (line 93). These failures are not retroactively GREEN. Fixed with `ee7bbf181b406a3bb8878a04ba13e27a73a55e09`.
- CI **#364** / run `39956581343` and **#365–#367** / runs `39956698085`, `39956733242`, `39956785271`: SUCCESS 6/6 at their respective exact HEADs after the correction.
- CI **#369** / run `39956972908`: SUCCESS on the subsequent rollover-source HEAD.
- **Final source/test CI #370 / run `39957042895`: SUCCESS, all 6/6 GREEN** on exact HEAD `ece9421fe35b851c238797fae3b392750b709965`. Jobs: Ubuntu 3.12 `120425352588`, Ubuntu 3.11 `120425352683`, Ubuntu 3.13 `120425352788`, Windows 3.12 `120425352871`, Windows 3.11 `120425352947`, Windows 3.13 `120425352999`. Ubuntu Python 3.13 logs: **Ruff PASS, 517/517 pytest PASS**, Node/UI mock and offline evaluation mock PASS. No live tool backend, external compute, or model inference.
- CI #368 was still IN PROGRESS at an intermediate check; this status is not evidence of its completion.
- **This checkpoint commit's own CI is not yet known while this text is being written**; verify its result SHA and CI independently.

## Frozen contracts, blockers, and authorization

No potentially billable API/compute, external GPU, subscription, purchased services, credentials/secrets/new accounts, physical-PC action, irreversible migration, frozen-contract change, real Candidate/weights, protected V2 evaluation, automatic promotion, real backend execution, personal-data access, notification send, or main merge. PR #5 stays Draft/NOT_PASSED. Local witnesses and SQLite read-only opens are not external attestation; in-process frozen dataclasses cannot sandbox hostile code; restart-safe exactly-once **real-world external side effects remain unproven**.

## Next plan / 今後の方針

1. Verify this checkpoint's **own result HEAD/CI** and keep #370 attributable only to the final source/test HEAD.
2. P0 Memory: bound all SQLite-backed revision/expiry/time inputs and reject overflow; integrate a clock-coherent, atomic `get/search` snapshot with exact input epoch and fail-closed stored-row validation; preserve independent-clock V1 semantics.
3. P0 Registry/Permission: authoritative registry-bound approval with an explicit trusted issuer and durable occurrence/token ledger, synthetic concurrent consumption/replay tests, no real dispatch.
4. P1 Planner/ActionAudit: persist exact step transitions, retained tail evidence and restart recovery; classify UNKNOWN WRITE without blind retry; mock-only audit-before-action and crash-injection, no cross-file atomicity claim.
5. P1/P2 Personal Context/Scheduler/Observation/Startup: synthetic scoped consent and revocation, cooldown/retention/anti-replay and dependency readiness. V3 remains free-only path, authorization and identity guards; never open paid/protected gates without explicit approval.

---

**HISTORICAL — Run 364 and earlier (preserved below)**

**HISTORICAL — Run 364**

Saved at: **2026-10-23 21:01:00.372 JST (+09:00)** (sampled immediately before the normal GitHub Contents update).

Branch/PR: `research/jarvis-foundations` / **Draft, unmerged PR #8**.
Exact work-basis HEAD: `90677077a13d52397fffe1c133ef3b0228afbd94` (CI #342 / run `39942509779`, SUCCESS 6/6).
Exact final **source/test/fix** HEAD before this checkpoint: `6d39597ab73ec56784f693b7bbfc5d5d746af5d5`.
Checkpoint-result HEAD: this file cannot contain its own future commit SHA; the **normal GitHub Contents API update response is authoritative**. CI #356 below validates the preceding source/test HEAD, **not this later status-only checkpoint commit**.

## Overall current ARK state

ARK remains a local-first, isolated/reversible JARVIS foundations **Draft research** branch, not production dispatch or complete JARVIS. No authenticated real-user consent, production-capable durable authorization, external trusted audit anchor, cross-database atomic execution, or real-world exactly-once assurance. Frozen V1/V2/Local UI/Launcher contracts and evidence unchanged. `main` remains `7a843f17eb96ed13d66f23b58b06406b3002e405`. V3 PR #5 remains Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`, **NOT_PASSED**. No Candidate weights, protected V2 evaluation, promotion, or external/paid training.

## NEW work this invocation — Run 364

**Five coherent free/local-only work packages; 14 sequential normal GitHub Contents commits (including three focused corrective commits); 45 new pytest cases.** The current PR HEAD was verified immediately before each write. Comparison from the exact work-basis HEAD reports 14 commits, 5 modified source files and 5 new test files, with no frozen or main branch file changes.

1. **Memory delete/expiry scope epoch**: source `6b3d8084ee63812156d8961b9036c9c0c2d25bd2`, focused tests `37c724b3392fee282bf89edea9f5ecb3c0aec97c` (9 cases). Pin exact scope identity before injected clock, reject reflected owner/namespace mutation inside DELETE/scoped purge, bind SQL and event to original scope, rollback on drift; keep unscoped purge behavior and CAS/expiry predicates.
2. **ActionAudit atomic v1 bootstrap**: source `1b0320920c1a99fc9ae8c6902262c562c2d733c7`, tests `6c179a3daa3f0a16643661e4d577109b1d4903c4` (5 cases), compatible newer-version error-message correction `4746cbcfb2f990e79fb3b9c6b0cad7bb32bcdeeb`. Use explicit BEGIN IMMEDIATE and statement-by-statement bootstrap; reject nonempty version-zero or negative-version databases; rollback fully if validation fails. No migration or auto-repair.
3. **ActionAudit continuity stale-schema review**: source `1a5e36829f0f764c383da8f1b6902464dcf72d12`, tests `dc2c514c2a5e5fc3a057e8362f5e72c76e3856a4` (6 cases). Reverify version and semantic v1 schema inside the read transaction, detecting post-startup table/index/trigger/version drift; witness remains locally derived, not authenticated external provenance.
4. **Observation cached-window retention recheck**: source `d7b1f423e0c21222590230970cae12bb1772f0d4`, tests `51db20504dca4327505e24c14a99efe711a3e151` (9 cases), timestamp-fixture correction `275bdfe6ee10b6286da469b511a872ac52687fd4`. New opt-in exact integer `assert_fresh_at(now_ms)`: reject stale/clock-rollback/reflected windows without changing witness or accessing media. Its supplied clock is not trusted-time or consent authority.
5. **Memory exact scope ingress**: contract source `65dbb91435cebfe76384769fa1bc30cd2bf1b973`, store source `04eda2fb41e93bc2c26db85089eca49185608c72`, tests `49fce08ecc4e0ce6062c77cf70471ac25a417f1c` (16 cases), lint-only correction `6d39597ab73ec56784f693b7bbfc5d5d746af5d5`. Public Memory value constructors and store ingress reject duck-typed or subclass scopes; search pins scope against reentrant clock retargeting.

## Exact-head tests / CI / evidence

- **CI #343 / run `39948389011`, #344 / run `39948451196`: SUCCESS, 6/6 each** for initial Memory scope-epoch source/tests.
- **CI #345–#351: FAIL on intermediate exact HEADs.** Root causes were one pre-existing newer-schema error-message compatibility assertion and one new observation mutation fixture using an inadmissible future timestamp; both corrected without changing the intended boundary. Failed runs are not retroactively GREEN.
- **CI #352 / run `39949282818`, #353 / run `39949433397`, #354 / run `39949512830`: SUCCESS, 6/6 each** on their respective intermediate HEADs.
- **CI #355 / run `39949587090`: FAIL** (Ruff E501: two overly long lines in new exact-scope regression tests); corrected in `6d39597ab73ec56784f693b7bbfc5d5d746af5d5`.
- **CI #356 / run `39949779488`: SUCCESS, all 6/6 GREEN** on exact source/test HEAD `6d39597ab73ec56784f693b7bbfc5d5d746af5d5`. Job IDs: Windows 3.11 `120401137466`, Windows 3.12 `120401137837`, Windows 3.13 `120401137935`, Ubuntu 3.11 `120401137845`, Ubuntu 3.12 `120401137872`, Ubuntu 3.13 `120401137710`. Ubuntu 3.13 logs show **Ruff PASS and 473/473 pytest PASS**. No live tool backend, camera, microphone, notification, personal-data connector, or training was invoked by foundation source.
- **Checkpoint commit CI not yet known at the time this text is written.** Verify the result HEAD and its CI separately; never attribute #356 to it.

## Frozen contracts / blockers / authorization boundaries

No spending or potentially billable API/compute, subscriptions, external GPU, new credentials/secrets/accounts, physical-PC action, irreversible migration, frozen-contract change, Candidate/weights, protected final V2 evaluation, promotion, real backend execution, notification sending, or main merge. PR #5 stays Draft/NOT_PASSED. A local hash witness cannot prove trustworthy authorship or historical completeness without an independently retained trustworthy anchor; in-process frozen inputs cannot sandbox malicious code; local process-only one-shot tokens cannot guarantee exactly-once real-world execution.

## Next plan / 今後の方針

1. Check this checkpoint's **own returned HEAD** and CI separately; report #356 only for the preceding source/test HEAD.
2. P0 Memory: bound all SQLite-backed integers and expiry/revision overflow, improve atomic bootstrap/CAS and clock-coherent `get/search` read snapshots while preserving legal V1 independent-clock nonmonotonicity.
3. P0 Permission/Registry: bind exact registry authority to a restart-safe, durable occurrence/token ledger with synthetic concurrent consumers and no real dispatch. Require explicit trusted approval provenance before live integration.
4. P1 Planner/Audit: append explicit transitions with retained tail proof, fail-closed recovery for UNKNOWN WRITE, and locally mocked audit-before-action crash-injection; no cross-file atomicity claims.
5. P1/P2 Personal Context / Scheduler / Observation / Startup: minimum-necessary consent and revocation, retention and anti-replay, dependency-scoped readiness. V3 remains free-only approval/path/identity/reproducibility guard work, with all protected and paid gates shut.

---

**HISTORICAL — Run 363 and earlier (preserved below)**

**LATEST — Run 363**

Saved at: **2026-10-23 19:55:32.354 JST (+09:00)**.

Branch/PR: `research/jarvis-foundations` / **Draft, unmerged PR #8**.
Exact work-basis HEAD before this invocation: `b54cd44fa121baa8f5ee6446e64f1cebf78853d8` (CI #328 / run `39934759120`, SUCCESS 6/6).
Exact final **source/test** HEAD before this checkpoint: `752692c03fad933ca39e7b3a9bdf696b045bfd30`.
Checkpoint-result HEAD: **this file cannot contain its own future commit SHA**; the normal GitHub Contents API update response is authoritative. **CI #341 applies to the exact source/test HEAD above, not to this later status-only commit.**

## Overall current ARK state

ARK remains a reversible, local-first JARVIS foundations **Draft research** branch. There is **no production dispatch, authenticated personal consent, durable exactly-once external action, trusted external audit anchor, or JARVIS completion**. Frozen V1/V2/Local UI/Launcher contracts and evaluation evidence remain unchanged. Main remains `7a843f17eb96ed13d66f23b58b06406b3002e405`; separate V3 PR #5 remains Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`, **NOT_PASSED**, with no Candidate weights, protected V2 evaluation, promotion or paid/external compute.

## NEW work this invocation — Run 363

**Five independent coherent packages; 13 sequential normal GitHub Contents commits including two semantics-preserving fixes; 37 new parametrized pytest cases.** PR head was re-read immediately before every write; no raw Git objects, force-push, main merge or real backend dispatch.

1. **Memory v1 reentrant put-input epoch:** source `f1c1cf951c11c8e24b987e958adc029b98df4d66`, tests `7b16c6fd51cda4840f70f44de33e5e94cd437c92` (11 cases). Pin scope/source/content/expiry/metadata before clock callback, reject reflected mutation under writer lock, persist and return pinned values; preserve existing v1 schema, CAS and event behavior. This is not malicious in-process sandboxing.
2. **Planner terminal propagation:** source `d188a26c157dfb83e0c983c51f2b176f0ebfb288`, tests `b7df2b82547f444582e236d76aefb4e3141cd6a8` (3 cases). Replace repeat full-graph scans with dependent-index traversal O(vertices + edges), preserving PENDING-only blocking and revisions. Exercise a 1,500-step chain, shared descendant, and independent unaffected lane. No persistent journal or real executor.
3. **ActionAudit SQLite integer bounds:** source `30b31e41dc27e9475e0a73def824be463c5d9cf7`, tests `5163617603c395c5456bbc045a8f7b85176296f1` (13 cases), compatible clock-error message fix `34021fa130e2499f32582aa3f0c920c2226c6c23`. Reject out-of-range/invalid clock and event cursors before SQLite binding; preserve prior error contract and allow the maximum signed 64-bit time. No trusted clock or audit-before-real-action proof.
4. **PermissionGate grant-iteration epoch:** source `2f069940ce29ad0d85673efce7f56bed9df65fc8`, tests `fb0309f547958da7852fb5e822dee2a2228e604f` (6 cases), corrected missing-token test setup `752692c03fad933ca39e7b3a9bdf696b045bfd30`. Detect reflected ToolSpec/ToolCall/grant/one-shot changes during external grant iteration before token consumption. Still process-local one-shot only, not durable approval or production execution.
5. **Read-only history-review opening:** Memory source `081098d995785206af7b9abfab017b62f434c819`, ActionAudit source `80c4b0e558a09dd14275ed90d7516becf64f5a30`, tests `2052ad91999112ead5a1a534adac4ec1324b3ad9` (4 cases). SQLite `mode=ro` URIs prevent read-only continuity/snapshot reviews from creating a replacement DB after a file vanished; test percent-encoded local paths. No schema mutation/migration/connector.

## Exact-head CI / evidence

- CI #329 `39941363242`, #330 `39941419967`, #331 `39941494457`, #332 `39941533483`: **SUCCESS** at their respective source/test HEADs.
- Intermediate #333–#340: **FAIL** at their exact intermediate heads, first due to pre-existing clock error-message assertion and later an incomplete synthetic test invocation. Both addressed with minimal semantics-preserving updates noted above; these failures are not retroactively GREEN.
- **CI #341 / run `39942139581`: SUCCESS, all 6/6 GREEN** at exact final source/test HEAD `752692c03fad933ca39e7b3a9bdf696b045bfd30`: Ubuntu Python 3.11/3.12/3.13 and Windows Python 3.11/3.12/3.13. Job IDs: `120375906221` (test (windows-latest, 3.12)); `120375906555` (test (windows-latest, 3.11)); `120375906569` (test (ubuntu-latest, 3.12)); `120375906587` (test (ubuntu-latest, 3.11)); `120375906706` (test (windows-latest, 3.13)); `120375906810` (test (ubuntu-latest, 3.13)).
- The **checkpoint commit's own CI remains unverified at the moment this text is written**; never attribute #341 to this later documentation commit.

## Frozen boundaries / blockers / authorization

No paid/potentially billable external service or GPU, credentials/secrets/new accounts, real-user personal data, real ToolBackend, notification send, real training, Candidate weights, protected V2 evaluation, promotion, frozen-contract change, destructive migration, or main merge. V3 PR #5 stays Draft/NOT_PASSED under explicit approval gate. A local SHA-256 witness does not authenticate its issuer; a frozen dataclass/registry cannot stop malicious in-process code; process-local one-shot does not survive restart; unknown WRITE completion remains non-replayable without explicit reconciliation.

## Next plan / 今後の方針

1. Check **this checkpoint's own exact-result HEAD and CI** separately; #341 validates only the preceding source/test commit.
2. P0 Memory: extend reflected-input epoch to `delete` and scoped `purge_expired`, bound persisted SQLite integer fields and clock, preserve v1 nonmonotone independent clocks; then integrate coherent read snapshot into a reviewed public contract without altering frozen evidence.
3. P0 Permission/Registry: keep registry as sole tool-effect authority, design restart-safe durable one-shot occurrence/expiry and audit-first transaction boundaries; test disconnected mocks only, never claim external exactly-once.
4. P1 Planner: integrate an append-only explicit-transition journal, independent retained tail evidence, crash/recovery tests and fail-closed UNKNOWN WRITE; retain terminal propagation and plan identity invariants.
5. P1/P2 privacy/proactive/observations and V3: implement synthetic scoped consent and revocation, startup dependency readiness, scheduler dedup/cooldown, observation retention/provenance; V3 remains free-only identity/path/reproducibility guards with NO paid compute or protected evaluation.

---

**HISTORICAL — Run 362 and earlier (preserved below)**

**HISTORICAL — Run 362**

Saved at: **2026-10-23 18:50:13.230 JST (+09:00)**.

Branch/PR: `research/jarvis-foundations` / **Draft, unmerged PR #8**.
Exact work-basis HEAD before this invocation: `38a1aa4c64acfe540bf75871227a19d6b44372f0` (CI #317 / run `39932364336`, SUCCESS).
Exact final **source/test** HEAD before this checkpoint: `aede3216524ea3af5a4d3b2175c07735e931d4b9`.
Checkpoint-result HEAD: **this file cannot contain its own future commit SHA**. The GitHub Contents API update result is authoritative. **CI #327 validates the source/test HEAD above, not this subsequent documentation checkpoint**.

## Overall current ARK state

ARK remains a reversible, local-first JARVIS foundations Draft research branch. It is not production dispatch, authenticated personal consent, trusted exactly-once external actions or JARVIS completion. Frozen V1/V2/Local UI/Launcher contracts and evidence remain unchanged. Main remains `7a843f17eb96ed13d66f23b58b06406b3002e405`. V3 PR #5 remains Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`, **NOT_PASSED**, without Candidate weights, protected V2 evaluation, promotion or paid/external compute.

The work-basis HEAD already contained intervening **Run361** Memory/Registry-authoritative diagnostics, Audit continuity, Observation window and synthetic snapshot groundwork; those commits were **not** made during Run362 and are not included in its new-test count. Prior Run360 checkpoint history is preserved verbatim below.

## NEW work this invocation — Run 362

**Five coherent work packages, ten sequential normal GitHub Contents commits, 35 new parametrized pytest cases**; latest PR HEAD checked immediately before each write. No raw Git Object / force / alternate write path, no real backend dispatch.

1. **ActionAudit same-version SQLite schema integrity**: source `7d138121bdbd9bac3c263ccc0ca8598c42c3d9a0`, regression file `55f8fbc68e52c855fd066e1fefc7d09f4122611a` (7 cases). Startup compares original v1 DDL, indexes and extra objects while preserving quoted SQL literals; runs `PRAGMA quick_check`, rejects schema drift without migrations/auto-repair. This does not authenticate audit writers.
2. **Planner deep-DAG validation**: source `6daca3ba54c7b9bf72000a501477a260e3aa5b10`, tests `1ceb13fc4846fa4fb76d0f09fb8ba3d81f0da60a` (3 cases). Iterative DFS validates 1,500-deep plans/cycles without Python recursion exhaustion; immutable-input epoch and all existing transition rules remain in place. No persistent Planner journal or backend.
3. **ToolRegistry static backend execution-interface pinning**: source `33b1a3f36703067947d9b733a506d8b0da76a3a8`, tests `1032a7a0a8a8c33f5dd9612340615a1b86037e72` (8 cases). Reject non-callable/property descriptors without invoking them and detect reflected replacement after registration. This is not attestation or an isolation sandbox.
4. **ActionAudit clock-reentrant identity fence**: source `5038d4a160f2e42661d912115307e6f9da350a27`, tests `5890efbda556fd430bbcda1885231d52a69b71f3` (7 cases). Freeze ToolCall identity before clock callback, reject mutations with transaction rollback, return the pinned persisted identity. Still not a trusted clock or audit-before-real-action proof.
5. **Observation continuity**: isolated source `177e3c30a28deeff59653413a3b169ac53e97da1`, tests `aede3216524ea3af5a4d3b2175c07735e931d4b9` (10 cases). Privacy-scoped, monotonic synthetic window rollover, equal-time idempotency, local hash chain and reflected-input checks. No camera, microphone, screen capture, live notification or consent authority.

## Exact-head CI / evidence

- **#318** `39933573083`, **#319** `39933657908`, **#320** `39933769196`, **#321** `39933834484`, **#322** `39934039534`, **#323** `39934102298`, **#324** `39934241170`, **#325** `39934315270`, **#326** `39934396839`: all **SUCCESS** on their respective exact source/test HEADs.
- **#327 / run `39934441974`: SUCCESS, all 6/6 GREEN** on exact Run362 final source/test HEAD `aede3216524ea3af5a4d3b2175c07735e931d4b9`: Ubuntu Python 3.11 job `120350412085`; Ubuntu 3.12 `120350411732`; Ubuntu 3.13 `120350412036`; Windows 3.11 `120350412000`; Windows 3.12 `120350412148`; Windows 3.13 `120350411951`.
- No separate detached local Run362 pytest count is claimed. Run362's formal evidence is GitHub PR-head CI. Local evidence summary is `RUN362_EVIDENCE_SUMMARY.md` and is not a repository contract or external attestation.
- This **checkpoint commit's own CI is not yet known at the time this text is written**. Never attribute #327 to the future checkpoint-result HEAD.

## Frozen boundaries / blockers / authorization

No paid/potentially billable service, subscriptions, external GPU, credential/account changes, actual user data, real ToolBackend, notification, real training, Candidate weights, protected V2 final evaluation, promotion, frozen contract change, destructive migration or main merge. PR #5 stays Draft/NOT_PASSED under separate explicit authorization. Startup DDL and local witness checks are not externally trusted history; in-process reflection defenses do not prove sandbox integrity. Registry-bound production permission, durable one-shot occurrence, trusted audit-before-action, cross-database atomicity and UNKNOWN WRITE reconciliation are unproven.

## Next plan / 今後の方針

1. Confirm **this checkpoint's resulting SHA and its own exact-head CI** separately; do not confuse the checkpoint with #327.
2. P0 **Memory**: strengthen coherent snapshot/CAS/expiry with strict persisted row/event evidence, bounded error and restart tests while preserving legitimate V1 nonmonotone clocks.
3. P0 **Permission and ToolRegistry**: safely integrate exact registry-derived READ/WRITE effect into durable one-shot diagnostic permission, with immutable bound IDs and non-dispatch mock evidence; require GREEN lower-layer dependencies.
4. P1 **Planner / Audit / One-Shot**: combine externally retained history witness, crash-safe checkpoint, audit-before-action with an explicitly trusted clock model, and fail-closed UNKNOWN WRITE no-replay status. Do not claim exactly-once real-world actions.
5. P1/P2 **privacy and V3 free-only**: scoped synthetic Personal Context consent/withdrawal, proactive scheduler claim/notification budgets, Observation provenance/retention; V3 identity/path/reproducibility reviews only, no paid GPU, protected evaluation, Candidate or promotion.

---

**HISTORICAL — Run 360 and earlier (retained unchanged below)**

**HISTORICAL — Run 360**

Saved at: **2026-10-23 17:59:30.521 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / **Draft, unmerged PR #8**.
Exact work-basis HEAD before Run360: `e65ca8e32f9f3c9f64985bb9417f630ae1502f83`.
Exact new source/test HEAD before this checkpoint: `7335126999787c8f1369b2c2173c4231028836d6`.
Checkpoint-result HEAD: **this file cannot contain its own future commit SHA**; the normal GitHub Contents API result is authoritative. CI #302 refers to the source/test HEAD above, **not automatically to this later status-only commit**.

## Overall current ARK state

ARK is a reversible local-first JARVIS foundations research branch, not production dispatch, certified user consent, trusted exactly-once external actions, or JARVIS completion. Frozen V1/V2/Local UI/Launcher contracts and evidence are unchanged. `main` remains `7a843f17eb96ed13d66f23b58b06406b3002e405`. V3 PR #5 remains Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`, **NOT_PASSED**, with no Candidate, protected V2 evaluation, promotion or paid compute.

## NEW work this invocation — Run 360

Five coherent packages committed on PR #8 through the **normal GitHub Contents API**; **12 sequential source/test/fix commits before this checkpoint**, latest HEAD re-read before every write. Three existing source modules changed, four focused test files created, **33 new test cases** added. All tests use local synthetic SQLite and mock-only inputs; no ToolBackend executes.

1. **Memory v1 event read integrity**: source `d95da824a70777f016093f8d5d728ca37c912f92`, Ruff B023-only correction `a378d58edbe7e623b5a4bebf2a557864bdefd07a`, tests `42f7345dc01249db558c5081e536d58a4dcd37db` (8 cases). Fail closed on malformed SQLite storage, event ordering, scope, canonical event ID and operation; preserve legitimate nonmonotone clocks across unrelated memories. Canonical-looking forged histories cannot be authenticated without external evidence.
2. **ActionAudit persisted event integrity**: source `a98191efc100d28de32c454051b00a43fcf39f70`, tests `2d1d799a9479fd50577cfc7ccd4ad24401083ee3`, SQLite-TEXT-affinity fixture correction `f5481310c501150d69a62d392323395854538401` (9 cases). Read nonempty exact TEXT fields, canonical digest shapes, positive event IDs and nonnegative clock. Argument bodies remain excluded; this is not pre-action audit authenticity.
3. **Planner immutable-input epoch**: source `c3852c4cdb2f0d91f610abac37415290c9339d65`, tests `40709618b47afc6f60b941231ad99a71cc46d453` (7 cases). Detect reflected PlanStep/ToolCall/Mapping replacement before ready-step observation or transition; no durable Planner journal or backend dispatch.
4. **Memory same-version schema startup gate**: source `7c28004e1458d610781c29768afa215135b63e79`, tests `fcd8d2eddf60ef43d3f2ebdef3cbc7af1de6c86f` (6 cases). At startup compare version-1 SQLite DDL/index/trigger objects with original frozen DDL after quote-preserving normalization and run `PRAGMA quick_check`; fail closed without migration/auto-repair. Startup-only checks are not continuously attested.
5. **Planner status output isolation**: source `15b39dceabc589e6bdeec4564bbb19f904a7a3dc`, tests at `7335126999787c8f1369b2c2173c4231028836d6` (3 appended cases). Return detached status values to prevent caller reflection from silently changing internal dependency authority. This is not restart-safe, thread-safe or malicious-process isolation.

## Exact-head CI / evidence

- CI #291 / `39926445872`: **FAIL** on `d95da824...`, Ruff B023 inner event helper capture. CI #292 / `39926497537`: **FAIL**, inherited same issue on audit source HEAD.
- CI #293 / `39926717179`: **SUCCESS**, explicit row helper binding corrected.
- CI #294 / `39926824014`: **SUCCESS**, Planner input epoch source.
- CI #295 / `39927008358`: **SUCCESS**, Memory event tests.
- CI #296 / `39927055711`: **FAIL**, audit test fixture put INTEGER into SQLite TEXT affinity (coerced to valid string). CI #297 / `39927154291`: **FAIL**, inherited same fixture case on Planner test HEAD.
- CI #298 / `39927234123`: **SUCCESS**, fixture corrected to BLOB, semantics unchanged.
- CI #299 / `39927698054`: **SUCCESS**, Memory startup schema source.
- CI #300 / `39927807166`: **SUCCESS**, detached Planner status source.
- CI #301 / `39927971672`: **SUCCESS**, Memory schema tests.
- **CI #302 / run `39928130150`: SUCCESS 6/6 GREEN** on exact final source/test HEAD `7335126999787c8f1369b2c2173c4231028836d6`, Ubuntu/Windows × Python 3.11/3.12/3.13; job IDs `120329452334` (Ubuntu 3.12), `120329452584` (Windows 3.13), `120329452596` (Windows 3.11), `120329452599` (Windows 3.12), `120329452651` (Ubuntu 3.13), `120329452673` (Ubuntu 3.11).
- Local read-only next-dependency audit (not in PR #8): `RUN360_NEXT_DEPENDENCIES.md`, SHA-256 `37368de00546e78c222772e510717781b4fc51896a1fcf8e10ac6ea3a63c5e1a`. This is design review, **not** independent attestation of the formal HEAD.
- This checkpoint commit has **no CI result at the time of writing**. Do not misattribute #302 to it.

## Frozen boundaries / blockers / authorization

No paid/potentially billable service, external GPU, training, real Candidate generation, protected V2 final evaluation, Candidate promotion, frozen-contract edit, credential/account connection, real user data, PC action, real ToolBackend, notification, destructive migration, force-push, alternate write path or main merge. PR #5 remains under its separate human/gate authorization. The Memory and Audit event reader checks do not prove provenance/authenticity; Planner is in-memory only; permission is not registry-authoritative or durable; no trusted clock, cross-database atomicity or exactly-once external WRITE guarantee is proven.

## Next plan / 今後の方針

1. Confirm the **checkpoint-result SHA and its own CI** separately. Never conflate documentation-only GREEN with the earlier exact source/test HEAD.
2. **P0 Memory**: use exact-type v1 row reads in mutators rather than permissive SQLite `int(...)` coercion; strengthen CAS, expiry and coherent snapshot semantics under concurrent writes; preserve schema v1 and valid nonmonotone event times. Test reopening legacy fixture databases and startup schema false positives.
3. **P0 Registry/PermissionGate**: design opt-in registry-authoritative diagnostic authorization before durable one-shot claims. Require immutable bound identity, exact-grant validation and non-dispatch mock evidence; no production authority yet.
4. **P1 Planner and One-Shot**: integrate independent externally retained history-witness, SQLite checkpoint/recovery, audit-first trusted time and UNKNOWN WRITE no-replay classification. Never auto-replay ambiguous writes.
5. **P1/P2 free lanes**: privacy-scoped synthetic Personal Context consent/expiry, Scheduler budgets and recurrence, Observation provenance/retention, Startup Readiness, V3 identity/path/reproducibility guards; no live personal capture, real backend, paid GPU, Candidate, protected evaluation, promotion or main merge.

---

**HISTORICAL — Run 359 and earlier (superseded by Run 360)**

**HISTORICAL Run359 checkpoint**

Saved at: **2026-10-23 16:56:11.871 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / **Draft, unmerged PR #8**.
Exact work-basis HEAD before Run359: `9e466a7bd45af757b3d610fea10b936eeb6f772f`.
Exact new source/test HEAD before this checkpoint: `1bbecea19b4dde49fef120d7964f47ffd3178bf8`.
Checkpoint-result HEAD: **this document cannot embed its own future commit SHA**. The GitHub Contents API update result commit SHA is authoritative. CI #289 verifies the code-and-test HEAD `1bbecea19b4dde49fef120d7964f47ffd3178bf8` only, not automatically the documentation checkpoint commit.

## Overall current ARK state

ARK's local-first JARVIS foundations remain reversible Draft research, not production dispatch, certified consent, trustworthy exactly-once external actions, or JARVIS completion. Frozen V1/V2/Local UI/Launcher contracts and evidence remain unchanged. `main` remains `7a843f17eb96ed13d66f23b58b06406b3002e405`.
V3 PR #5 remains Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`, **NOT_PASSED**, with no Candidate, protected V2 evaluation opening, or promotion.

## NEW work this invocation — Run 359

Five coherent source-and-test packages were committed by the **normal GitHub Contents API**, in 10 sequential commits with latest HEAD reviewed before every write. No force-push or raw Git Object route.

1. **Memory put/delete lock-before-clock and CAS**: source `4bb13acd7f95d1cedbf77b51175ed937484056e6`, tests `bf64c189bc786354aa75e977d49e20f1fd5136c2` (4 test cases: create/update/delete writer-lock clock and stale cross-store revision conflicts). Existing frozen schema/event contracts were not changed.
2. **PermissionGate exact carriers**: source `48522982873c65d6cc4c8af0c93397d7b1e1475b`, tests `7b4cd6c885e5e419339e03676193ee8a18445f02` (6 parametrized test cases: exact ToolSpec/ToolCall/one-shot/grant, invalid late grant does not spend one-shot). This is **not** registry-authoritative or restart-safe authorization.
3. **Registry bind ToolCall identity drift**: source `c68d18546a4c53dea26d22b573e3203a3f66c530`, tests `6934d20a9a9adef0a2401f88cdbc17395d33b753` (5 parametrized cases). Bound IDs reject reflected request mutation while computing registry revision; no ToolBackend executed.
4. **Memory persisted-row read integrity**: source `ee8dd7c9a2c73f45d9223ff40e909968b088ad97`, tests `2130f8d85a8de943bae3fff6328071eeab82f728` (10 cases: digest, deterministic row identity, exact storage classes, canonical metadata and valid legacy v1 rows). Same-version schema DDL audit and event-history authenticity remain separate future gates.
5. **SQLiteActionAudit lock-before-clock**: source `bc8439423cf35adb5fd2eb34830a5412f8a6eb3f`, tests `1bbecea19b4dde49fef120d7964f47ffd3178bf8` (5 test cases: writer lock before clock, rollback, exact action/outcome carriers). This is an append-only synthetic fixture, **not** real pre-action authorization or a trusted-clock attestation.

## Exact-head CI / tests / evidence

- CI #280 run `39919242863`: **SUCCESS**, source HEAD `4bb13acd7f95d1cedbf77b51175ed937484056e6`.
- CI #281 run `39919403677`: **SUCCESS**, source HEAD `48522982873c65d6cc4c8af0c93397d7b1e1475b`.
- CI #282 run `39919616598`: **SUCCESS**, tests HEAD `7b4cd6c885e5e419339e03676193ee8a18445f02`.
- CI #283 run `39919818595`: **SUCCESS**, tests HEAD `bf64c189bc786354aa75e977d49e20f1fd5136c2`.
- CI #284 run `39919954724`: **SUCCESS**, source HEAD `c68d18546a4c53dea26d22b573e3203a3f66c530`.
- CI #285 run `39920198471`: **SUCCESS**, source HEAD `ee8dd7c9a2c73f45d9223ff40e909968b088ad97`.
- CI #286 run `39920279016`: **SUCCESS**, tests HEAD `6934d20a9a9adef0a2401f88cdbc17395d33b753`.
- CI #287 run `39920428517`: **SUCCESS**, tests HEAD `2130f8d85a8de943bae3fff6328071eeab82f728`.
- CI #288 run `39920504970`: **SUCCESS**, source HEAD `bc8439423cf35adb5fd2eb34830a5412f8a6eb3f`.
- **CI #289 run `39920693019`: SUCCESS 6/6 GREEN**, exact final code-and-test HEAD `1bbecea19b4dde49fef120d7964f47ffd3178bf8`, Ubuntu/Windows × Python 3.11/3.12/3.13; job IDs `120304916694`, `120304916793`, `120304916886`, `120304916981`, `120304917013`, `120304917052`.
- Local disconnected synthetic tests: Policy **6/6**, Registry **5/5**, Audit **5/5** = **16/16 PASS** under Linux Python 3.13; some local supporting modules were from a detached candidate, **not byte-identical with official PR #8**. Two Memory regression files were locally syntax-compiled, with their full GitHub CI covered above.
- A local read-only integration audit records the remaining same-version SQLite schema, event-storage, authorization and privacy gates. It is not part of PR #8 and is not an attestation.

## Frozen boundaries / blockers / authorization

No new paid or potentially billable services, paid/external GPU, credentials, actual user data, local PC device action, model training, Candidate adapter/weight generation, protected V2 final evaluation, Candidate promotion, frozen-contract edits, real backend dispatch, notifications, destructive migration or main merge. No safety safeguard bypass. Registry-backed immutable authorization, trusted pre-action audit, durable exactly-once occurrence/replay guards, multi-database atomicity and UNKNOWN WRITE reconciliation are **not proved**. Local SQLite history anchors are not external authenticity roots.

## Next plan / 今後の方針

1. Confirm checkpoint-result commit and its own CI; do not conflate source GREEN with the later documentation commit.
2. **Memory v1**: fail-closed same-version schema/index/DDL integrity and `quick_check` without auto-migration; strict `memory_events` typed integrity while respecting legitimate nonmonotone V1 event timestamps; define coherent search/get snapshot and clock semantics before changing behavior.
3. After exact-head GREEN dependency checks, integrate **Registry-authoritative PermissionGate**, durable One-Shot occurrence claims, trusted clock, audit-before-action and disconnected/mock executor with crash/UNKNOWN WRITE recovery; no live backend.
4. Strengthen Planner durable checkpoint witness/restart semantics and startup readiness; keep externally held evidence requirements explicit.
5. Continue Personal Context privacy-scoped consent and cache invalidation, Scheduler state/budget, Observation provenance/retention, and V3 free-only path/identity/reproducibility guards. Keep PR #5 Draft/NOT_PASSED with no training, protected evaluation or main merge.

---

**HISTORICAL — prior Run357 checkpoint (superseded by Run359)**

**HISTORICAL Run357 checkpoint**

Saved at: **2026-10-23 14:59:25.379 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / **Draft, unmerged PR #8**.
Exact work-basis HEAD (before Run357): `ed13c53c815eeacaec22b9e7d8e97e410c63d932`.
Exact new source/test HEAD (before this checkpoint): `112c6f4951210a1b1159fb0c7df560e65e5739f5`.
Checkpoint-result HEAD: cannot be embedded into its own committed file; **the GitHub Contents update result commit SHA is authoritative**. CI #278 applies to `112c6f4951210a1b1159fb0c7df560e65e5739f5` only, and not automatically to the documentation-only checkpoint commit.

## Overall current ARK state

ARK JARVIS foundations remain reversible Draft research, **not** production dispatch, authenticated consent, real exactly-once actions, or JARVIS completion. Frozen V1/V2/Local UI/Launcher evidence/contracts unchanged. `main` remains `7a843f17eb96ed13d66f23b58b06406b3002e405`.
V3 PR #5 stays Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`, **NOT_PASSED**, no protected evaluation opening.

## NEW work this invocation — Run 357

- **Registry mapping epoch:** normal GitHub Contents source update `adb173e14a36a71285ddbaec594960af44c65265` pins the exact read-only ToolRegistry mapping object and rejects reflected equal-valued replacement; separate repository regression file at `fa6a6bc270ef6dd9e05cad2da853d97aa275e009` (11 parametrized tests). No backend is invoked.
- **Memory expiry CAS:** source update `b24cecf2bde72ffd6b8a62dc62564a82d7ec1a56` acquires SQLite writer lock **before** sampling time or selecting expired rows, and conditionally deletes by exact memory ID, scope, revision and expiry. Only successful deletions emit expiry audit events. Repository tests committed at `5446d3a69a6eaed8aaab59f77120a23a8377247d` (3 tests: writer-lock clock probe, scoped expiry, rollback on failed audit).
- **CI recovery:** commit `5446d3a69a6eaed8aaab59f77120a23a8377247d` produced CI **#277 FAIL** across 6 jobs due solely to Ruff I001 import ordering in the new Memory test. A minimal import-order correction at `112c6f4951210a1b1159fb0c7df560e65e5739f5` restored **CI #278 SUCCESS 6/6**.
- **Independent Planner durability (offline only):** disconnected synthetic SQLite Planner journal now transactionally updates and verifies a second local tail-anchor table. Missing/replaced anchor, inconsistent count/hash or truncated journal are refused. 9 new synthetic tests; Linux/Python 3.13.5 local warnings-as-errors: Memory **390**, Agency/Observation **659**, Personal Context **193** = **1,242/1,242 PASS**. Clean Run356 patch replay matches **162/162 file SHA-256**; syntax parsed as Python 3.11/3.12/3.13 grammars (not actual alternate runtime tests).
  Detached source ZIP SHA-256 `039a1fb9e34147f9220045ac098e25454531878d2380ffd37bf426b376c97652`; detached evidence ZIP SHA-256 `c8f30521db7d6fbd4ed0ddccd84bb51774fa26499ff983b1b0d873f54726a2f0`. **Not committed or covered by GitHub CI.**
- Produced read-only exact-source follow-up audit prioritizing Memory put/delete lock-before-clock, persisted-row integrity and same-version schema checks. No frozen-contract changes or operational data reads.

## Tests / CI / evidence

- PR #8 CI #274 / run `39907742262`: **SUCCESS**, registry source HEAD `adb173e14a36a71285ddbaec594960af44c65265`.
- CI #275 / run `39907979841`: **SUCCESS**, registry regression HEAD `fa6a6bc270ef6dd9e05cad2da853d97aa275e009`.
- CI #276 / run `39908163598`: **SUCCESS**, Memory source HEAD `b24cecf2bde72ffd6b8a62dc62564a82d7ec1a56`.
- CI #277 / run `39908372539`: **FAIL 6/6**, Ruff I001 new test import only, test body not reached.
- CI #278 / run `39908587091`: **SUCCESS 6/6 GREEN**, exact source-and-test HEAD `112c6f4951210a1b1159fb0c7df560e65e5739f5`; Ubuntu/Windows × CPython 3.11/3.12/3.13; job IDs `120266096541`, `120266096437`, `120266096428`, `120266096146`, `120266096559`, `120266096293` respectively.
- The detached Planner fixture is not part of PR #8. Its synthetic local hashes are **not** independent security attestation.
- No run of new CI on this documentation checkpoint commit is asserted here.

## Frozen boundaries, blockers and authorizations

No paid/external compute, paid services, training, real Candidate adapter/weight generation, protected V2 final evaluation, promotion, frozen-contract edits, credentials, physical-PC action, real backend execution, personal-data ingestion, notification delivery, destructive migration, or main merge. No bypass or raw Git Object writes. PR #5 remains separately gated. SQLite local tail anchor is mutable with its database; it is not a trusted external history root. Memory v1 still needs schema/content-row integrity and more lock-before-clock work; trusted clock, issuer authenticity and real restart-safe exactly-once remain open.

## Next plan / 今後の方針

1. Verify the documentation-only checkpoint result HEAD/CI separately; maintain exact-head GREEN evidence without duplicate reruns.
2. Continue **Memory v1**: move put/delete clock behind writer locks, validate persisted IDs, content digests, types/canonical metadata and same-version schema integrity. Add conflict, corruption, cross-process SQLite tests.
3. After official lower-level GREEN, integrate registry-authoritative PermissionGate, durable one-shot, trusted-clock pre-action audit and mock no-replay recovery. **No live tool dispatch**.
4. Advance Planner state persistence and UNKNOWN WRITE reconciliation; keep offline anchor fixture isolated pending API/schema compatibility and independent history-witness design.
5. Progress privacy-safe Personal Context, Scheduler/Observation and V3 free-only provenance/path/reproducibility guards without training, live inputs, Candidate, protected evaluation or main merge.

---

**HISTORICAL — earlier status preserved below; superseded by Run357**


Saved at: **2026-10-16 17:59:25 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / **Draft, unmerged PR #8**.

Work-basis HEAD: `2baeb7824df9460235e876336fac942ae64dbbee` (source).
Checkpoint-result HEAD: this file cannot embed the SHA of its own future commit; use the GitHub Contents update result SHA. CI #271 applies to work-basis HEAD **only**, not automatically to the subsequent documentation checkpoint commit.

## Overall current ARK state

V1/V2/Local UI/Launcher contracts and evidence remain frozen and unchanged.
`main` remains `7a843f17eb96ed13d66f23b58b06406b3002e405`.
V3 PR #5 remains Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`, NOT PASSED.
JARVIS PR #8 remains reversible Draft/unmerged, not a production dispatch gate or JARVIS completion.

## NEW work this invocation — Run 204

- Saved a narrowly scoped **source** hardening in `src/ark/agency/registry.py`: reject equal-valued reflected `str` subclasses for registry revision and registered name/capability/backend identity. Normal GitHub Contents write succeeded at source HEAD `2baeb7824df9460235e876336fac942ae64dbbee`, based on `3804b77de13570bf8cc6b59aa67a3f0f6c4bec84`.
- Exact source HEAD CI **#271**, run `38876767855`: **SUCCESS 6/6 GREEN** on Ubuntu/Windows × Python 3.11/3.12/3.13; jobs `116893574699`, `116893574968`, `116893575063`, `116893575068`, `116893575095`, `116893575174`. These jobs validate committed source and existing tests, **not** the blocked new test file.
- Attempted the normal Contents `create_file` path for `tests/test_registry_epoch_exact_types_run204.py`, but the safety path **BLOCKED** it. No focused GitHub test commit/CI is claimed and no bypass was attempted.
- Continued independent, reversible **offline-only** code: an exact-carrier ToolRegistry regression suite; duplicate synthetic pre-action audit receipt detection across distinct WRITE occurrences; and purpose-bound synthetic observation/privacy review. **29 new tests**, detached Linux/Python 3.13.5 **1,601/1,601 PASS with warnings-as-errors**. Clean Run203 patch replay has 166/166 Python SHA-256 matches and **29/29 focused PASS**; a full clean replay was interrupted, so it is not claimed GREEN. Offline ZIP SHA-256: `634064ace63338365a2f7804b18de8a94bdb370f70aa756ef2de3f83f02eb7c5`.
- Detached source and PR #8 source are **not byte-identical**; never replace PR source wholesale with the offline ZIP.

## Frozen boundaries and blockers

No paid/external compute, new credentials, training, Candidate generation, protected V2 evaluation opening, promotion, real tool/backend execution, destructive migrations, frozen contract changes, or main merge. PR #5 stays under its separate authorization gate. No live observation/consent proof is asserted.
The new ToolRegistry regression file remains GitHub-write blocked; only the source change has exact-head CI. Synthetic hash/digest results are not external attestation. Multi-database atomicity, trusted time, issuer provenance, restart-safe authorizing one-shot and unknown WRITE recovery remain unproven.

## Next plan / 今後の方針

1. Save the focused Registry exact-epoch test file via the **normal** GitHub path when permitted; establish fresh exact-head CI GREEN before downstream PermissionGate authority wiring.
2. In separate safe lanes, advance Registry-bound exact-type PermissionGate, durable one-shot/occurrence integrity, trusted-clock pre-action audit and disconnected no-replay recovery; preserve no real dispatch.
3. Independently advance Memory CAS/event/expiry and coherent snapshots; address existing GitHub Memory v1 schema/row integrity and lock-before-clock gaps before integration.
4. Continue Planner ambiguous WRITE recovery, privacy-scoped synthetic Observation/Personal Context and Scheduler fixtures; require actual provenance/consent design before live capture.
5. Keep V3 free-only JSON/identity/provenance guards reversible, with no paid/training/validation/final opening or promotion.

---

**HISTORICAL — superseded by Run 204**

Saved at: **2026-10-13, 00:37:52 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / Draft, unmerged PR #8

Work-basis HEAD: `1ebeafe6d7ba8ffd58a32cd0d83d0567a66d256c`.

Checkpoint-result HEAD: this self-updating file cannot contain the SHA of the commit that
writes it. The GitHub Contents update result for this checkpoint commit is authoritative;
CI #267 below applies to the **work-basis source HEAD**, not automatically to this
subsequent documentation-only checkpoint commit.

## Overall current ARK state

V1/V2/Local UI/Launcher contracts and evidence remain frozen and unchanged.
`main` is `7a843f17eb96ed13d66f23b58b06406b3002e405`.
PR #5 V3 remains Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`;
no protected evaluation was opened or later PASS declared. PR #8 remains Draft,
reversible, and unmerged, not a JARVIS completion or official roadmap PASS.

## NEW work this invocation

- Restored PR #8 source CI after public registry exports commit
  `3ea77091a9725341f3e3e79d77ff0257f577b26b` caused Ruff I001.
  The **only source change** was a reorder of the `.policy` and `.registry`
  imports in `src/ark/agency/__init__.py`. Normally permitted GitHub Contents
  update succeeded at `1ebeafe6d7ba8ffd58a32cd0d83d0567a66d256c`.
- The exact source HEAD above passed CI #267 / run `38270375604`:
  **SUCCESS 6/6 GREEN**, Windows and Ubuntu, Python 3.11/3.12/3.13.
  Previous #266 / run `38244247324` was FAIL 6/6 for I001 on an older HEAD.
- Prepared reference-vector/non-dispatch ToolRegistry repository tests for the
  already-committed fixture files. A normal GitHub Contents `create_file` write
  for `tests/test_tool_registry_committed_vectors.py` was blocked by safety
  checks, so no such test was saved and **its CI evidence does not exist**.
- Advanced two **detached, reversible, offline-only** modules in Run 121:
  paged Memory event-chain continuity (21 new tests) and per-source Observation
  liveness (23 new tests). Neither source/test module is in PR #8.
  Run121 detached Linux/Python 3.13.5 Agency **2555/2555 PASS**,
  independent V3 guards **186/186 PASS**, total **2741/2741 PASS**;
  source ZIP SHA-256 `f49aff22ec9fc0c5204719b305b658a81b3316f9108f6c941c2be432275f601d`.
  All 311 prior Run120 source bytes are unchanged; 4 new files; 315 source
  hashes match the ZIP manifest. Clean patch replay new tests **44/44 PASS**.
  No Windows/actual Python 3.11/3.12/Ruff run was performed for the detached candidate.

## Tests / CI / evidence

CI #267 / `38270375604`, source HEAD `1ebeafe6d7ba8ffd58a32cd0d83d0567a66d256c`:

- Ubuntu 3.11 job `114882867967`: SUCCESS
- Ubuntu 3.12 job `114882868485`: SUCCESS
- Ubuntu 3.13 job `114882868378`: SUCCESS
- Windows 3.11 job `114882868301`: SUCCESS
- Windows 3.12 job `114882868373`: SUCCESS
- Windows 3.13 job `114882868279`: SUCCESS

Run121 offline test evidence is **not** exact-head GitHub CI evidence.
The Run121 ZIP is not safe to overwrite onto PR #8: its lower-level module
dependencies and implementation differ from the GitHub branch.

## Frozen boundaries unchanged

No paid/external GPU compute, paid APIs/services, model training, real Candidate
adapter/weight generation, protected V2 final-evaluation opening, promotion,
frozen-contract change, credentials/account connection, physical-PC device
capture, actual tool dispatch, destructive action, or main merge.

## Blockers / authorization boundaries

Normal GitHub source/test write safety layer rejected the focused ToolRegistry
repository-test addition. No bypass, raw Git object, alternate ref-write, force
push, or duplicate CI workflow was used. Keep all detached Memory/Observation/
Planner/Scheduler/Personal Context work isolated until prerequisites are
reviewed and integrated with exact-head GREEN evidence.

PR #5 remains subject to frozen Contract and explicit approval for any real
training, provider/billing, Candidate generation, protected evaluation or promotion.
Preserve populated historical audit/Memory migration boundaries until reviewed.

## Next plan / 今後の方針

1. Add focused ToolRegistry committed-fixture identity/immutability/non-dispatch
   tests through the normal path when permitted; require exact-head CI GREEN.
2. Then integrate Registry-bound PermissionGate, durable one-shot authorization,
   execution occurrence/replay protection and trusted-clock audit-before-action
   only after their prerequisite invariants are GREEN.
3. Advance independently tested Memory CAS/event/expiry and coherent snapshots;
   integrate detached chain review only once its underlying interfaces match.
4. Continue Planner ambiguous-RUNNING recovery without automatic WRITE replay.
5. Stage fixture-only Observation session/liveness adapters and privacy-safe
   Personal Context/Scheduler without live capture, action authority or user
   consent assumptions. Keep free-only V3 guards isolated.

---

## Historical checkpoint — 2026-10-07 (preserved)

**HISTORICAL — superseded by LATEST above**

Saved at: **2026-10-07 18:50:20 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / Draft PR #8

Work-basis HEAD: `eb49558c0e6a80df53e246aa1fb0a71b93ec3932`

Checkpoint-result HEAD: this file cannot contain the SHA of the commit that writes itself; use the
resulting commit SHA from this checkpoint update as the authoritative checkpoint-result HEAD.

## Current state

V1/V2/Local UI/Launcher evidence is frozen and unchanged. PR #5 remains Draft/unmerged at
`d6d4c1954a85fc716b1c593ac55c85417912418f` under its controlling V3 Contract. JARVIS
foundation work remains isolated/reversible and is not a roadmap PASS.

PR #8 is open, Draft, mergeable, **114 commits ahead / 0 behind** `main` at this work basis.

## New work this session

- Landed immutable ToolRegistry source at
  `eb49558c0e6a80df53e246aa1fb0a71b93ec3932` through the normal GitHub Contents path.
- The registry snapshots exact `ToolRegistration` values, rejects duplicate names, sorts by
  tool name, exposes a read-only mapping, computes a registration-order-independent revision,
  resolves exact capabilities, and derives registry-bound action IDs from request + registry
  revision + capability/effect/backend identity.
- CI #260 / run `37603020130` for that exact source HEAD completed **SUCCESS, 6/6 GREEN**,
  including Ruff and pytest on Windows/Linux Python 3.11-3.13.
- Offline focused validation reproduced the frozen registry revision and all three bound-action
  reference vectors, exercised 256 randomized registration orders, and verified lookup/bind
  caused zero backend executions: **260 focused checks PASS**. This focused result is local
  evidence only until matching repository tests are saved.
- Read-only Memory review reconfirmed the highest-risk v1 gaps remain exact request/scope ingress,
  persisted row/event storage-class and digest validation, lock-before-clock mutation ordering,
  revision-bound expiry purge, and coherent read snapshots.
- PR #5 free-only audit reconfirmed **8 production modules / 9 `json.loads` parse sites**.
  A shared strict decoder package was prepared for duplicate decoded keys, NaN/Infinity,
  float-overflow-to-infinity, invalid UTF-8, and exact str/bytes ingress, but the normal source
  write was safety-blocked and therefore did not land.
- Production Observation fixture adapters and focused ToolRegistry repository tests/public exports
  were also prepared, but their normal source/test writes were safety-blocked and did not land.

## Tests / CI / evidence

CI #260 GREEN jobs:
- Ubuntu 3.11 `112731721391`
- Ubuntu 3.12 `112731721723`
- Windows 3.11 `112731721736`
- Windows 3.12 `112731721767`
- Ubuntu 3.13 `112731721779`
- Windows 3.13 `112731721793`

The prior PR #8 checkpoint HEAD
`ae967e5cb8a5df40162c3a9223cc25582bae7fb2` remains CI #259 /
run `37578146322` **SUCCESS, 6/6 GREEN**.

PR #5 remains at `d6d4c1954a85fc716b1c593ac55c85417912418f` with
CI #151 / run `36223644908` **SUCCESS**.

Focused local/source-ready evidence is not repository test evidence until matching tests are
saved and their exact-head CI is GREEN.

## Frozen boundaries unchanged

No paid/external compute, real training, Candidate adapter/weight generation, protected V2
opening, Candidate promotion, frozen-contract change, new credentials/account connection,
live capture, destructive action, unavailable physical-PC action, or main merge occurred.

## Blockers / authorization boundaries

After the ToolRegistry source write succeeded, later normal GitHub Contents writes for production
Observation adapters, focused ToolRegistry tests, agency public exports, the PR #5 strict JSON
guard, and a Gap Matrix reconciliation were rejected by the safety layer. No raw Git objects,
ref manipulation, force push, hidden route, or other safeguard bypass was used.

The ToolRegistry source is landed and exact-head CI GREEN, but its frozen-vector/randomized-order
focused repository regressions and public package exports remain pending; do not integrate durable
authorization on top of it until those tests/exports are saved and exact-head GREEN.

PR #5 still requires explicit authorization before any external compute, real Candidate
generation, protected V2 opening, or promotion.

Populated Action Audit v1 -> occurrence-bound v2 migration and populated Memory v1 ->
independently anchored event-log v2 migration remain blocked until reviewed historical mapping
policies exist.

## Next plan / 今後の方針

1. Retry only the normal permitted path later for focused ToolRegistry fixture/reference-vector
   tests and public exports; require exact-head GREEN before dependent integration.
2. Then harden exact PermissionGate ingress + non-consuming grant validation and, only after GREEN,
   land durable registry-bound one-shot authorization -> execution occurrence/replay protection ->
   trusted-clock audit-before-action disconnected executor.
3. Continue independent Memory v1 hardening: exact ingress, schema/row/event integrity,
   lock-before-clock CAS/expiry, then coherent multi-namespace snapshot -> Personal Context.
4. Continue Planner Recovery against the already-landed exact planner state machine; preserve
   rollback safety and RUNNING ambiguity without automatic write replay.
5. Land fixture-only Observation adapters when the normal source path permits; keep live capture
   disconnected.
6. Continue PR #5 free-only guard closure only; do not start preflight/training, external GPU,
   Candidate generation, protected evaluation, or promotion.
