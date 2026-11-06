# ARK AI — Canonical Project Status

**LATEST — Run650 / 2026-11-06 JST:** **Three non-UI, disconnected core custody packages saved**: privacy-veto witness/review/receipt pre-access checks, append-only local audit continuity witness checks, and startup-readiness requirement/receipt original descriptor checks. **55 authored regression cases** plus one old-test compatibility repair after actual CI FAIL. **Latest six-job CI still IN PROGRESS / NOT VERIFIED GREEN.** ARK/JARVIS/V3 = **NOT_PASSED**. **ALL NEW UI DEVELOPMENT PAUSED.**

**Saved at:** **2026-11-06T12:24:10.427+09:00 Asia/Tokyo/JST**, sampled from the current runtime immediately before the ordinary safeguarded GitHub Contents update. This is administrative checkpoint time, **not** a trusted action clock, authorization, training approval, model/runtime identity, or independent evidence.

## LATEST — work basis, branch and checkpoint

- Branch `research/jarvis-foundations`; [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8) OPEN/Draft/unmerged.
- **Invocation initial exact work-basis HEAD:** `49cc9d4f87e434920da8cbdf357e77eeec23db60` (Run649 checkpoint; verified its own CI #42153342003 six GREEN). No changes were stacked on concurrently modified paths without rereading GitHub HEAD and the source blob.
- Source/test/compatibility-result HEAD before report: `67b622a12c2e2f426304406263e2b1f7b89a4a11`. Normal-API fast-forward compare from initial basis: **9 commits, 7 changed files** (3 non-UI sources, 3 new non-UI regression tests, 1 adjusted legacy non-UI test); no frozen/UI file.
- **Technical report HEAD:** `9357f6f4d7639e67b163adafbeffdd785ce2a4d0`; [Run650 technical evidence](https://github.com/Iam-2squared/ark-ai/blob/9357f6f4d7639e67b163adafbeffdd785ce2a4d0/docs/JARVIS_RUN650_NON_UI_PRIVACY_AUDIT_STARTUP_CUSTODY.md).
- **Checkpoint write-basis HEAD:** `9357f6f4d7639e67b163adafbeffdd785ce2a4d0`, re-read immediately before this status write. **Checkpoint-result HEAD is assigned by GitHub only AFTER this checkpoint commit**, so it cannot be accurately written into its own file in advance. Re-fetch the PR branch and status blob after saving. Pre-write status blob SHA `ed4a07e614e8e979243a9db2f76572311876ad25`.
- Run649 checkpoint remains below, with full earlier history retained in Git, technical reports and `docs/status_archive/PROJECT_STATUS_THROUGH_RUN639_PART1.md` / `PART2.md`.

## NEW work this invocation

1. **Privacy veto original carrier custody:** `src/ark/disconnected_privacy_veto.py` source commit [43d9ae1f](https://github.com/Iam-2squared/ark-ai/commit/43d9ae1fccfa4d72b58dfe754d1a2d338600503d); checks retained witness, review, receipt fields/constructors/lookup hooks before private fixture SQLite read or veto mutation. `tests/test_privacy_veto_original_carrier_preaccess_run650.py` adds **23** synthetic cases. A stored veto only denies reuse, never proves consent/deletion or a trusted writer.
2. **Audit continuity original witness custody:** `src/ark/agency/audit_continuity_review.py` source commit [caddb105](https://github.com/Iam-2squared/ark-ai/commit/caddb10545b1ea74736f08fcda469dac553b513b); pins original audit witness fields, `__init__`, `__post_init__` and lookup hooks *before* retained history reads. `tests/test_audit_continuity_witness_original_slots_run650.py` adds **18** synthetic cases.
3. **Startup readiness lease original carrier custody:** `src/ark/startup_readiness_lease_review.py` source commit [c6cd650d](https://github.com/Iam-2squared/ark-ai/commit/c6cd650d4002c935e94f9acd4e4419553adb606c); protects exact requirements/shape validator and result constructor/slots/hooks around reentrant diagnostic callbacks. `tests/test_startup_lease_preaccess_carrier_custody_run650.py` adds **14** synthetic cases. No startup, dispatch or notification authorized.
4. **Actual CI FAIL semantics-preserving repair:** Ubuntu 3.11 in CI [#42155143795](https://github.com/Iam-2squared/ark-ai/actions/runs/42155143795) and [#42155231680](https://github.com/Iam-2squared/ark-ai/actions/runs/42155231680) showed **four FAIL** in the old audit result-epoch test: new correct early rejection `audit continuity witness constructor changed` conflicted with old expected *late* errors. Ordinary Contents commit [67b622a1](https://github.com/Iam-2squared/ark-ai/commit/67b622a12c2e2f426304406263e2b1f7b89a4a11) updates old expectations and checks the injected callback was never invoked; source guards are **not weakened**. Two new test helpers were also corrected to restore inherited Python lookup hooks without contaminating later test cases ([858cbf05](https://github.com/Iam-2squared/ark-ai/commit/858cbf05149ce3aa0ea7a674e3fa0816832b7c2d), [19a13377](https://github.com/Iam-2squared/ark-ai/commit/19a133777f9a635104df5e51d87afc5fdd044605)).

## CI / tests / evidence at this checkpoint

- Initial Run649 exact HEAD `49cc9d4...`: [CI #42153342003](https://github.com/Iam-2squared/ark-ai/actions/runs/42153342003), observed **6/6 GREEN** (Ubuntu/Windows × Python 3.11/3.12/3.13). It predates this invocation.
- Privacy source+tests `5e3d6cfe...`: [CI #42155008398](https://github.com/Iam-2squared/ark-ai/actions/runs/42155008398), observed **SUCCESS (all six jobs)** in the last workflow-list snapshot. Later audit and readiness modifications are not covered.
- Audit source/tests pre-repair [CI #42155143795](https://github.com/Iam-2squared/ark-ai/actions/runs/42155143795) and [#42155231680](https://github.com/Iam-2squared/ark-ai/actions/runs/42155231680): actual logged **4 FAIL** on Ubuntu, from old expected errors after earlier rejection. Corrected via `67b622a1...`.
- Latest corrected source+tests `67b622a1...`: [CI #42155847601](https://github.com/Iam-2squared/ark-ai/actions/runs/42155847601) **QUEUED** at last read. Technical report HEAD `9357f6f4...`: [CI #42156201800](https://github.com/Iam-2squared/ark-ai/actions/runs/42156201800) **QUEUED** at last read. This checkpoint creates its own normal CI. **Latest exact-head all-six GREEN remains NOT VERIFIED**. Never launch a duplicate workflow.
- **55 authored cases**, NOT a pytest PASS count. No local pytest/Ruff, actual physical-PC GGUF inference or external validation claimed.

## Frozen contracts, blockers and free-only authorization boundary

- `main` last observed `7a843f17eb96ed13d66f23b58b06406b3002e405`; no main writes/merges. [PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) Draft/unmerged `805b377697472268db02650a89c7a94b1c5337c8`. Protected historical V2 final evaluation unopened; V3 Candidate training and promotion not authorized. Review of V3 `PRE_PAID_COMPUTE_GATE.md` confirms real identity, provenance/rights, human review, budget and provider cost evidence blockers, not assumed resolved.
- [PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) Draft/unmerged `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`; **no new UI/frontend source, features, tests or integration**. Frozen V1/V2/Local UI/Launcher contracts/evidence unchanged.
- No billable action, external GPU/compute, paid API/subscription, adapter/Candidate weights, credentials/secrets/new account connection, real ToolBackend action, personal-data export, physical PC, human approval, destructive operation, main merge or protected evaluation. New code remains local-only and reversible; local class guards are not a sandbox or independent witness authentication.

## Next plan / 今後の方針

1. Check the corrected/latest exact-head **6/6 CI**, inspect real failure logs and repair minimally if required. While CI runs, use independent non-UI lanes and never duplicate CI or make same-path evidence obsolete.
2. Memory: COMMIT-UNKNOWN vs read-only retained event/row coherency, CAS revision and expiry; retain independent witness limitations and never claim a writer from matching digests or replay an ambiguous write.
3. Planner: durable interruption/UNKNOWN recovery, terminal dependency propagation and persistence; no automatic replay of uncertain WRITE work.
4. Integrate disconnected/mock ToolRegistry, exact-type PermissionGate, durable occurrence and audit-before-action only after lower-level exact-head GREEN; never authorize live tools from a fixture.
5. Continue privacy-safe Personal Context, proactive and observation back-end contracts, and free V3 approval/path/identity guards; keep UI paused, frozen evaluations closed, PR #5/#9 Draft and spend blocked.

---

## Prior checkpoint — Run649 (retained unmodified content)

**LATEST — Run649 / 2026-11-06 JST:** **Three non-UI core packages saved**: local Context lexical-search result/hit custody, Personal Context request-binding slot custody, and disconnected Observation envelope-validator/field custody. **40 newly authored regression test cases**, NOT a claim of latest-head pytest PASS. The first two packages had their earlier CI evidence inspected; the latest exact-head **six-job CI remains IN PROGRESS / NOT VERIFIED GREEN**. ARK/JARVIS/V3 = **NOT_PASSED**. **ALL NEW UI DEVELOPMENT PAUSED.**

**Saved at:** **2026-11-06T11:54:02.788+09:00 Asia/Tokyo/JST**, sampled from the current runtime shortly before the ordinary safeguarded GitHub Contents update. This is checkpoint bookkeeping, **not** a trusted action clock, model/runtime attestation, approved human review, or execution authorization.

## LATEST — branch, exact work basis and checkpoint authority

- Branch `research/jarvis-foundations`; [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8) OPEN/Draft/unmerged.
- **Invocation initial work-basis HEAD:** `d5cdfd923d749242e274b03e6593b1429464004b` (Run648 technical-report tip; prior canonical Run646 checkpoint still present when work began).
- Package A source/test result HEADs: `fd71255c5aa2c8c6f0a0d5ff683deee2ad1db350`, `6f7c30841dcf13a7a36ed510d2f58523f16cbb54`.
- Package B source/test result HEADs: `63028ad98527c4e0502fd14eb9dee3d3d487db2e`, `39e2b336139d736526e2988044b2c2ccdc7f44a6`.
- Package C source/test result HEADs: `315446da42805f54d22566c14b5f22d22193e39c`, `ff66b52ec1141566a646a917d52a46e29bac1350`. CI-detected compatibility repair HEADs: `1bf7d46efdd157cbd5d6fa8c9ae512d9ed5544af`, `c16941fe399aab50e71a018e92cb627abd6c6807`, `925ff0c98b68a5b6fc4a1a64d7a5e1c7d809dcad`.
- Verified initial-to-repair compare: 9 fast-forward commits, exactly 8 changed paths (3 non-UI source, 3 new non-UI tests, 2 adjusted existing non-UI tests); no frozen/UI change.
- Technical-report HEAD: `cf1e0a1701e7cec0028373be0bacb77590f518a8`, report [Run649](https://github.com/Iam-2squared/ark-ai/blob/cf1e0a1701e7cec0028373be0bacb77590f518a8/docs/JARVIS_RUN649_NON_UI_CONTEXT_SEARCH_BINDING_OBSERVATION_CUSTODY.md).
- **Checkpoint write-basis HEAD:** `cf1e0a1701e7cec0028373be0bacb77590f518a8`, re-read immediately before this status update. **Checkpoint-result HEAD is assigned by GitHub only AFTER the status write**, so it is distinct from the above work-basis and cannot truthfully be embedded here beforehand. Re-fetch PR head and status blob after saving for the exact result. Pre-write canonical status blob SHA `d761613ce37ce97e1b3a90b8ab535b62e6920d95`.
- Historical reports [Run647](https://github.com/Iam-2squared/ark-ai/blob/research/jarvis-foundations/docs/JARVIS_RUN647_NON_UI_RESTART_MEMORY_SCHEDULE_CARRIER_CUSTODY.md), [Run648](https://github.com/Iam-2squared/ark-ai/blob/d5cdfd923d749242e274b03e6593b1429464004b/docs/JARVIS_RUN648_NON_UI_MEMORY_TRIAGE_RECOVERY_BUNDLE_CUSTODY.md); earlier long history retained by Git and `docs/status_archive/PROJECT_STATUS_THROUGH_RUN639_PART1.md` / `PART2.md`. No historical/frozen evidence was rewritten.

## NEW work this invocation

1. **Lexical search private result custody:** `src/ark/offline_context_search.py` pins original preview and nested hit dataclass fields and lookup hooks before returning fixture excerpts; `tests/test_offline_context_search_result_slot_custody_run649.py` adds **14** cases. No authorized disclosure, retention or external dispatch is inferred from a matching private result.
2. **Personal Context binding input/result custody:** `src/ark/personal_context_request_binding.py` statically validates original preview and output slot descriptors, constructors and lookup hooks before inspecting synthetic private JSON or producing a content-free binding; `tests/test_personal_context_binding_slot_preaccess_run649.py` adds **16** cases. Request ID/hash do not authenticate identity, consent, revocation freshness or data reuse.
3. **Disconnected observation fixture validator custody:** `src/ark/observation_fixture_adapters.py` pins the original ObservationEnvelope field descriptors, validator and lookup machinery before constructing local in-memory fixture envelopes; `tests/test_observation_envelope_validator_slot_custody_run649.py` adds **10** cases. No microphone, camera, capture source attestation, network or real observation integration.
4. **Actual CI failure repaired without weakening early guards:** Ubuntu Python 3.11 on observation-source CI [#42151893412](https://github.com/Iam-2squared/ark-ai/actions/runs/42151893412) logged **53 FAIL / 9,313 PASS / 1 SKIP** because previous tests expected later rejection messages; the modified source now correctly distinguishes forged constructor, poisoned validator and data slot, and keeps a stable original validator separate from the test-injectable postconstruction callback. Two existing observation test files accept earlier fail-closed rejection. All repairs used the normal Contents write path; never bypassed any safety protection. Latest repair validation remains pending.
5. Run649 technical evidence in `docs/JARVIS_RUN649_NON_UI_CONTEXT_SEARCH_BINDING_OBSERVATION_CUSTODY.md`, saved before this checkpoint.

## CI / tests / evidence at checkpoint

- Previous Run648 report HEAD `d5cdfd923d749242e274b03e6593b1429464004b`: [Actions #42150177666](https://github.com/Iam-2squared/ark-ai/actions/runs/42150177666), observed **all six GREEN** (Ubuntu/Windows × Python 3.11/3.12/3.13).
- Package A source+tests `6f7c30841dcf...`: [#42151453696](https://github.com/Iam-2squared/ark-ai/actions/runs/42151453696), observed **6/6 GREEN**.
- Package B source+tests `39e2b336139d...`: [#42151745990](https://github.com/Iam-2squared/ark-ai/actions/runs/42151745990), **IN PROGRESS** at last CI read (Ubuntu 3.11 GREEN, others not yet verified).
- Package C pre-repair source `315446da...`: [#42151893412](https://github.com/Iam-2squared/ark-ai/actions/runs/42151893412) **FAIL** as logged above, corrected in later commits.
- Corrected source + tests `925ff0c98...`: [#42152879253](https://github.com/Iam-2squared/ark-ai/actions/runs/42152879253), **QUEUED** at latest run read.
- Technical-report HEAD `cf1e0a1701e7...`: [#42153114777](https://github.com/Iam-2squared/ark-ai/actions/runs/42153114777), **QUEUED** at latest read. This checkpoint will start its normal CI run; never dispatch a duplicate.
- **40 authored regression cases**, NOT an all-head pytest PASS count. Latest corrected HEAD all-six GREEN = **NOT VERIFIED**. No local pytest, Ruff, physical-PC GGUF/model run or independent external assertion is claimed.

## Frozen boundaries / cost / authorization

- `main` remained at `7a843f17eb96ed13d66f23b58b06406b3002e405` in the last inspected PR metadata; this invocation made no main write.
- [PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) remains OPEN/Draft/unmerged at `805b377697472268db02650a89c7a94b1c5337c8`; protected V2 final evaluation remains closed, V3 Candidate training/promotion not authorized.
- [PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) remains OPEN/Draft/unmerged at `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`; **no new UI/frontend work or branch modification**.
- Frozen V1/V2/Local UI/Launcher contracts/evidence unchanged. No new paid/billable service, external GPU, credentials/secrets/account connection, protected evaluation, real ToolBackend action, real user data export, physical hardware use, irreversible operation or main merge. All new code remains local fixture-only and reversible.

## Next plan / 今後の方針

1. Confirm the latest corrected exact-head **all six** CI jobs; if FAIL use actual job logs and the smallest semantics-preserving fix via the normal Contents API, while pursuing only independent safe lanes during CI.
2. Memory: follow up COMMIT-UNKNOWN with read-only two-handle event/row coherency, CAS generation/expiry and preserved independent witness boundaries; do not infer who wrote from matching hashes or silently retry uncertain commits.
3. Planner: hardened persistent UNKNOWN, terminal dependency propagation and interruption recovery; never automatically replay ambiguous WRITE actions.
4. Integrate disconnected/mock ToolRegistry + exact-type PermissionGate + durable occurrence + audit-before-action only after lower-level exact-head GREEN evidence, without authorizing actual external effects.
5. Continue privacy-safe Personal Context and proactive/observation back-end contract groundwork; keep PR #5/#9 Draft and all frozen evaluation, paid compute, user consent/approval and UI pause boundaries intact.
