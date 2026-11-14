# ARK AI — Run650 non-UI privacy, audit and startup carrier custody

**Evidence sampled:** 2026-11-06T12:22:50.411+09:00 Asia/Tokyo/JST (workflow bookkeeping, not trusted time or authentication).
**Work basis:** Draft PR #8 `research/jarvis-foundations`, initial exact HEAD `49cc9d4f87e434920da8cbdf357e77eeec23db60` ([Run649 checkpoint](https://github.com/Iam-2squared/ark-ai/blob/49cc9d4f87e434920da8cbdf357e77eeec23db60/docs/PROJECT_STATUS.md)).
**Current work saved through:** `67b622a12c2e2f426304406263e2b1f7b89a4a11` before this report. No merge or protected/frozen file change. **ARK/JARVIS/V3 NOT_PASSED**.

## Package A — disconnected privacy-veto witness/review/receipt pre-access custody

- Normal Contents source commit [`43d9ae1f`](https://github.com/Iam-2squared/ark-ai/commit/43d9ae1fccfa4d72b58dfe754d1a2d338600503d) changes `src/ark/disconnected_privacy_veto.py`.
- Pins import-original `OfflinePrivacyVetoWitness` fields, constructor, object lookup hooks and false-only custody assertion. Reviews and vetoes refuse an installed malicious witness descriptor *before* inspecting private witness slots or opening the fixture SQLite file. Witness constructors are checked before genesis and after bounded SQLite history scanning.
- Adds symmetric original field, constructor and lookup guards to `OfflinePrivacyVetoReview` and `OfflinePrivacyVetoReceipt`. This prevents a value-equal but executable review/receipt descriptor from being invoked before a local veto action or returned to an untrusted caller. The post-COMMIT ambiguity remains fail-closed; a potentially persisted denial must not be silently retried.
- New `tests/test_privacy_veto_original_carrier_preaccess_run650.py` ([create commit `5e3d6cfe`](https://github.com/Iam-2squared/ark-ai/commit/5e3d6cfe94e6970f2b35f889db1e86a2f6db8f2d)): **23 authored cases** (10 witness, 5 review, 7 receipt, 1 clean denial-only restart). The fixture is local and contains only synthetic identity digests.

## Package B — read-only audit continuity witness original descriptor custody

- Source commit [`caddb105`](https://github.com/Iam-2squared/ark-ai/commit/caddb10545b1ea74736f08fcda469dac553b513b) hardens `src/ark/agency/audit_continuity_review.py`: confirms original `AuditContinuityWitness` `__init__`, `__post_init__`, exact slots and class-level lookup hooks before *any* retained field reads and again through read/return callback boundaries.
- New `tests/test_audit_continuity_witness_original_slots_run650.py` ([create commit `38d03f0b`](https://github.com/Iam-2squared/ark-ai/commit/38d03f0b991e673d25665e6517a7267eeefe2095)): **18 authored cases** (14 preexisting field/lookup substitutions with and without a retained witness, 3 midscan substitutions, 1 normal append-only evidence check). No ToolBackend or external effects.

## Package C — disconnected startup readiness lease carriers

- Source commit [`c6cd650d`](https://github.com/Iam-2squared/ark-ai/commit/c6cd650d4002c935e94f9acd4e4419553adb606c) hardens `src/ark/startup_readiness_lease_review.py`: requires original `SyntheticReadinessRequirement` slots, constructor, `assert_shape` and lookup hooks before reading requirement fields; checks `SyntheticStartupLeaseReview` slots/constructors/hooks before result construction and during subsequent immutable-epoch checks.
- New `tests/test_startup_lease_preaccess_carrier_custody_run650.py` ([commit `89773eef`](https://github.com/Iam-2squared/ark-ai/commit/89773eef874530f9a591a26bbbe9cedb77f3dfc5)): **14 authored cases** (6 poisoned requirement shapes, 7 result-carrier substitutions, 1 valid dependency/freshness denial-only review). No hardware access, real startup, notification or permission grant.

## Validation, failure analysis and exact-head limits

- **55 authored regression cases**, not a claim that all tests passed in CI.
- Existing Run649 checkpoint HEAD `49cc9d4f87e434920da8cbdf357e77eeec23db60`: [CI #42153342003](https://github.com/Iam-2squared/ark-ai/actions/runs/42153342003) observed completed **6/6 GREEN**, Windows/Ubuntu × Python 3.11/3.12/3.13. This success predates this run's source edits.
- First privacy source [CI #42154827040](https://github.com/Iam-2squared/ark-ai/actions/runs/42154827040) and privacy source+tests [#42155008398](https://github.com/Iam-2squared/ark-ai/actions/runs/42155008398): Ubuntu **3/3 GREEN** observed; Windows not yet verified at last inspection.
- Audit source [#42155143795](https://github.com/Iam-2squared/ark-ai/actions/runs/42155143795) and audit source+tests [#42155231680](https://github.com/Iam-2squared/ark-ai/actions/runs/42155231680) produced **four Ubuntu FAIL** from existing `tests/test_audit_continuity_result_epoch_run420.py`; job logs from #42155143795 Ubuntu 3.11 and #42155231680 Ubuntu 3.11 show the new correct *early rejection* `audit continuity witness constructor changed` rather than the old late result/source rejection strings. The source guard was **not weakened**. The one existing test was adjusted to expect early rejection and verify the poisoned callback was never executed, normal Contents commit [`67b622a1`](https://github.com/Iam-2squared/ark-ai/commit/67b622a12c2e2f426304406263e2b1f7b89a4a11).
- During source/test development, independent test-helper contamination was proactively fixed: injected inherited `__getattribute__` is removed by exact original-class-dictionary restoration rather than leaving a newly owned descriptor behind. Fix commits [`858cbf05`](https://github.com/Iam-2squared/ark-ai/commit/858cbf05149ce3aa0ea7a674e3fa0816832b7c2d), [`19a13377`](https://github.com/Iam-2squared/ark-ai/commit/19a133777f9a635104df5e51d87afc5fdd044605).
- Latest corrected source/test HEAD `67b622a12c2e2f426304406263e2b1f7b89a4a11`: [CI #42155847601](https://github.com/Iam-2squared/ark-ai/actions/runs/42155847601) observed **QUEUED**, latest exact-head **6/6 GREEN NOT VERIFIED**. Do not infer success from the older green source basis or earlier incomplete jobs.
- Only normal safeguarded GitHub Contents source/test writes were used. Verified fast-forward `49cc9d4...`→`67b622a1...`: 9 commits, 7 changed files (3 core source, 3 new non-UI tests, 1 updated legacy non-UI test). No local pytest/Ruff/real PC/GGUF run is claimed.

## Frozen and free-only boundaries

- The stored privacy veto can only deny synthetic reuse; absence never proves consent. Local audit digests and snapshot checks cannot prove historical writer authenticity, externally trusted timestamps, external exactly-once effects, or source custody. Runtime class-pinning is not a security sandbox against arbitrary already-executing Python code.
- Main, Draft PR #5 (V3), Draft PR #9 (seven-workspace UI), V1/V2/Local UI/Launcher freezes and protected V2 evaluation untouched. No UI/frontend source/tests/integration modified.
- Passive review of PR #5 `docs/v3/PRE_PAID_COMPUTE_GATE.md` confirmed immutable model/tokenizer/code/tool identities, human-approved 120/30 dataset/contamination review, environment pinning and explicit cost/authorization remain actual blockers; nothing was assumed or opened. No external GPU, paid compute, subscription, Candidate weight generation/promotion, new credentials/account connection, physical-PC action or irreversible operation.

## Next plan / 今後の方針

1. Establish **latest exact-head CI 6/6 GREEN**. If a new failure appears, inspect the actual job logs, apply a minimal test or semantic fix via the ordinary API, and work independently during in-flight CI.
2. Memory: develop COMMIT-UNKNOWN vs retained event/row evidence, CAS and expiry checks without claiming writer identity from hashes or replaying an uncertain write.
3. Planner: interrupted/UNKNOWN step persistence and terminal propagation, never automatic ambiguous WRITE replay.
4. Disconnected ToolRegistry + exact-type PermissionGate + durable occurrence and audit-before-action integration only with independently GREEN lower-layer evidence; no real backend dispatch.
5. Keep privacy-veto, Personal Context and proactive/observation back-end scopes denial-only, and V3 and UI cost/freezes intact.
