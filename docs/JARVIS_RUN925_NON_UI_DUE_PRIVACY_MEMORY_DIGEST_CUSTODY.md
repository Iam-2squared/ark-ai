# ARK AI Run925 — detached due digest, privacy veto ingress, Memory event sequence bound

**Observed reporting wall clock:** 2026-11-17T04:58:15.354+09:00 (Asia/Tokyo/JST; **not** a trusted execution or audit clock). **ARK/JARVIS NOT_PASSED**; UI/frontend work paused. Free-only non-UI foundations on Draft PR #8, no main merge.

**Work-basis HEAD:** `48a0a9d3a6c4eccbc80b3bc1d1cb64332d747a0f` (Run924 checkpoint). **Complete source/test HEAD before this report:** `343322d7e07735ecab714571fddea4e82930f2c4`. Report-creation and eventual status checkpoint commits must be separately observed and must not be mistaken for this tested source basis. Draft PR #5 protected and Draft PR #9 UI paused/unmerged.

## New work — three isolated non-UI source + regression packages (19 new synthetic tests authored)

1. **Disconnected due-restart digest custody (6 tests):** source commit `57d3a44a19c89cb3dabb465c9acfbda67716978a`; test commit `84ae7fd21694f634f908caee04186888709980a2`; source `src/ark/agency/disconnected_due_recovery_review.py`, regression `tests/test_due_recovery_digest_authority_run925.py`. Pin this review's own SHA-256, JSON encoder and domain **before** reading the synthetic due-ledger witness, and recheck before/after the digest and before returning the inert review. The lower-level reservation and prefix reviewers' existing pins alone did not protect this wrapper-specific domain against an equal-bytes replacement or a post-prefix callback change. Cases cover equal/different domain replacement, swapped SHA/JSON, a reentrant prefix callback and unchanged deterministic/restart-safe denial. This is not authenticated historical custody or notification authority.
2. **Personal Context privacy-revocation hash admission (7 tests):** source commit `4ed8093eb67bb06f96b5e74032d8e64dd1078131`; test commit `41911d6c43effddf0959883e06d5ecb4c6b84493`. Source `src/ark/personal_context_revocation_review.py`; regression `tests/test_revocation_scope_digest_contract_run925.py`. Pin exact `MemoryScope` v1 identity, its validator and slot/look-up descriptors and revocation SHA/JSON functions before **private scope field access**, including post-validation and post-hash rechecks. Six unsafe definition mutations should leave the append-only synthetic veto table unchanged; one healthy restart test retains the revoked-scope denial. No Memory v1 contract, revocation schema, export permission, authentication or consent change.
3. **Memory event high-water bounded read (6 tests):** source commit `6e8ee97675a84ff75a4ce876a42ac4b7321ed093`; test commit `343322d7e07735ecab714571fddea4e82930f2c4`. Source `src/ark/memory/sqlite_event_alignment.py`; regression `tests/test_memory_event_marker_bounded_hydration_run925.py`. The passive, same-transaction `sqlite_sequence` high-water query now fetches **at most two markers** (`LIMIT 2`) while preserving zero/one/multiple-marker classification and duplicate fail-closed behavior. Synthetic probes check bounded SQL, duplicate corruption not rewritten, and stable healthy cold restart. No persisted DDL, Memory CAS, lifecycle or frozen API change.

**Status of tests:** 19 synthetic regression cases **authored and committed**, not a claim of PASS. No full local pytest suite was run and no GitHub Actions run for the newest source/test HEAD was fully GREEN at this report's initial observation. Existing Run924 checkpoint HEAD `48a0a9d`: [CI #43935432737](https://github.com/Iam-2squared/ark-ai/actions/runs/43935432737) **GREEN six of six**; unrelated to this invocation's new source/test.

## Exact CI boundaries at this report observation

- Due source `57d3a44`: [#43943730161](https://github.com/Iam-2squared/ark-ai/actions/runs/43943730161), IN PROGRESS; due source+tests `84ae7fd`: [#43943832319](https://github.com/Iam-2squared/ark-ai/actions/runs/43943832319), IN PROGRESS.
- Privacy source `4ed8093`: [#43944025465](https://github.com/Iam-2squared/ark-ai/actions/runs/43944025465), IN PROGRESS; privacy source+tests `41911d6`: [#43944122980](https://github.com/Iam-2squared/ark-ai/actions/runs/43944122980), QUEUED.
- Memory source `6e8ee97`: [#43944299278](https://github.com/Iam-2squared/ark-ai/actions/runs/43944299278), QUEUED; complete source+tests `343322d`: [#43944429073](https://github.com/Iam-2squared/ark-ai/actions/runs/43944429073), QUEUED.
- These statuses are **snapshots**. New report and checkpoint writes trigger their own default CI; no duplicate equivalent workflow was launched manually. If any job FAILS, inspect precise logs and apply the smallest semantics-preserving correction. Prior Run924 frozen-Observation v1 direct NUL compatibility correction remains intact.

## Boundaries, unresolved blockers, and Next plan / 今後の方針

Protected V1/V2/Local UI/Launcher evaluation and evidence unchanged; Observation direct v1 frozen; PR #5/#8/#9 Draft/unmerged and UI work stopped; no real GGUF/GPU, paid API, external compute/services, secrets/credentials, physical-PC test, protected final-eval, Candidate training/weight production/promotion, real tool dispatch, notification, consent impersonation, automatic ambiguous WRITE replay, destructive action or main merge.

**Blocking gaps:** newest exact-HEAD Windows/Ubuntu × Python 3.11–3.13 CI completion, SQLite WAL/SHM cross-process alias/last-close race, verified independent audit clock and restart-safe real one-shot approval, Memory CAS/event/expiry consistency under failures, Planner COMMIT-UNKNOWN source-independent recovery, personal-data consent, and user physical-PC gates. Hashes and local SQLite evidence cannot prove external effects or authenticated custody. Overall **NOT_PASSED**.

1. Verify newest source/test **exact SHA** all-six CI; fix any failing job without changing frozen semantics. Prefer independent lanes during CI.
2. Continue disposable-only WAL/SHM held-FD/alias diagnosis; avoid retrying unknown outcomes.
3. Review Memory event/row/CAS/expiry coherent cold snapshots and Planner retained COMMIT-UNKNOWN diagnosis, without auto-dispatch.
4. Only connect registry → exact PermissionGate → durable occurrence → trusted-clock audit-before-action → disconnected mock after lower-level exact-head GREEN; independently advance privacy-safe Personal Context, proactive/Observation backend and free V3 guards.
5. Continue zero-cost, no UI, no main/protected merge, no Candidate/evaluation, no billable external action.
