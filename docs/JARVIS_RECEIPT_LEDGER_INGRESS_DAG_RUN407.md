# ARK JARVIS foundations — Run407 disconnected receipt, continuity, observation, DAG and proactive review

**Scope:** Five independently scoped FREE-only work packages on Draft PR #8. No live backend, user permission, trusted clock, sensor collection, external compute, Candidate, protected evaluation, frozen schema/contract edit or main merge. This document describes locally checkable fixture behavior **only** and is not a release PASS.

## A. Mock reservation receipt subject binding (+8 tests)

- `src/ark/agency/synthetic_mock_action_cycle_review.py`: after the durable RUNNING journal transition and synthetic occurrence reservation, verify the **exact** receipt class, occurrence identity, registry revision, bound action ID, request ID and exact integer reservation time against the original bound WRITE.
- Refuse a mismatched or reflected/forged local reservation receipt *before* a pre-action ActionAudit append and before synthetic terminal SUCCEEDED. This does **not** roll back an independently committed RUNNING or reservation; the WRITE remains UNKNOWN/non-replayable.
- `tests/test_mock_reservation_receipt_binding_run407.py`: seven adversarial receipt substitutions (including bool timestamp / wrong type) plus a stable inert-success control. Both original API and all synthetic receipts retain `dispatch_authorized=False`, `automatic_replay_authorized=False`, `external_outcome_known=False`.

## B. Retained occurrence history in the same SQLite snapshot (+8 tests)

- `src/ark/agency/synthetic_occurrence_continuity_review.py`: optional independently retained `SyntheticLedgerWitness` is checked **within the same read-only transaction** used to hash current reservation rows. Pin exact original retained row tuple carrier/digest before callbacks; recheck after integrity, path/handle setup, per-row hashes, witness hash and retained-prefix comparison.
- Direct `assert_synthetic_history_continues` now pins both original witness epochs across its two potentially reentrant integrity validations and subset check. Exact 10,000-hash witness/scan bounds align with existing synthetic occurrence fixture validation.
- `tests/test_synthetic_ledger_retained_snapshot_run407.py`: exact extension, erased history veto, equal-value witness carrier mutation during hash, direct cross-witness mutation during validation, oversized/wrong-type retained witnesses before disk access, and missing database non-creation.
- **Recorded repair:** initial source head `0c71e027fe8e471a2d2e8dca9161d269b63787d3` incorrectly escaped the existing regex/hash domain separators (CI #930 / run `40151753321` **FAIL**). Ordinary Contents-API fix `3cc08f734d13d1c6606819abfab69d796b60bdeb` restored the original byte-exact `\\Z` and `\\0` Python spellings. Source+test head `b60fd7feef57eb55065603104dafccd3d682fccb` CI #932 / `40151817426` **SUCCESS**. Never reinterpret #930 as GREEN.
- Still no OS inode custody, external authenticated retained storage, or atomic multi-DB recovery.

## C. Observation window original ingress header (+7 tests)

- `src/ark/observation_window_review.py`: pin privacy scope, observed time, age budget and original tuple **before** initial validation. Recheck exact original header object carriers and each previously hydrated ObservationEnvelope field after reentrant per-item ID calculation. A callback cannot redefine the reviewed age/privacy window and have the altered header accepted as the original baseline.
- Also retain identity-carrier checks when `assert_consistent` is used later, including equal-value string substitutions.
- `tests/test_observation_header_ingress_run407.py`: altered time/age during first envelope, input mutation on initial validation, value-equal tuple/header replacements, unchanged deterministic content-minimized witness. No real microphone, screen, camera or notification.

## D. Mixed DAG/write restarts and independent mock statuses (+3 tests)

- `tests/test_synthetic_write_plan_mixed_restart_run407.py`: a RUNNING/UNKNOWN root WRITE, READ bridge and dependent WRITE coexist with an independent synthetic SUCCEEDED WRITE; the independent success does not resolve the root's external outcome. Four separately committed journal/occurrence/audit/link SQLite stores are reopened and compared against separately retained witnesses, with no replay after restart.
- A blocked dependent WRITE cannot enter RUNNING while prerequisites are unsatisfied. A terminal FAILED root can mark descendants BLOCKED but cannot erase already committed occurrence and audit evidence or manufacture external success. No backend method runs.

## E. Proactive retained-witness SQLite-open custody (+7 tests)

- `src/ark/proactive_synthetic_continuity_review.py`: independently recheck the original SQLite source and caller-held retained witness **after** Path.resolve, URI generation, handle creation and BEGIN, before the first schema/row validation. Each step is an injectable boundary; a later callback cannot restore a transient source/history retarget and hide it.
- `tests/test_proactive_witness_open_epoch_run407.py`: six resolve/URI/connect variations against same-value Path substitution or retained row-hash carrier replacement; confirm opened handles close and no trigger rows change. Stable restart/retained-prefix control remains read-only and inert.
- Synthetic trigger preparation is NOT a real notification, device observation, user permission, trusted time, or external Tool execution.

## CI and source integrity requirements

- Exact initial work-basis HEAD: `89de461e7030b9f747b2d7cfc2df435b9a568d02` (Run406 checkpoint; CI #927 / `40148292385` **SUCCESS**).
- Mock source+test head: `4d42364d171112540f1de2ac6bf7b7c3ebf2430b`; CI #929 / `40151630127` **SUCCESS**.
- Occurrence source+tests head: `b60fd7feef57eb55065603104dafccd3d682fccb`; CI #932 / `40151817426` **SUCCESS** (includes earlier corrections).
- Observation source+tests head: `674cd29dd006a95adc66ae522cd26dfc35cbba09`; CI #934 / `40152005809` **IN PROGRESS at this document's initial evidence read**.
- Four initial work packages' source/test head: `678967a236d200dfcea9eb4274b9bffbc83b2e31`; CI #935 / `40152100238` **SUCCESS**, including Ubuntu Python 3.13 Ruff PASS / **2088 pytest passed**. Fifth package added separately afterward.
- Fifth proactive package source/test head: `5000a6315cf98615d87430d85b75ce03bbd32c0f`; CI #938 / `40152265950` **IN PROGRESS at this document update**. Its exact SHA must pass Ubuntu/Windows Python 3.11–3.13; do not borrow GREEN from earlier heads.
- +33 new test cases this invocation: **8 + 8 + 7 + 3 + 7**. Previous exact-head baseline: 2062; **2088 passed** on #935 before proactive fixtures. **2095** is the final expected count, NOT a verified PASS until #938 is GREEN.
- No frozen V1/V2/Local UI/Launcher contracts, Memory v1 / ActionAudit v1 SQL, V3 Contract 1, evaluation opening or main merge are changed. PR #5 stays Draft/NOT_PASSED; PR #8 stays Draft/unmerged.

## Non-proofs / blockers

Local hash witnesses can be forged by coordinated storage rewriting unless independently retained and authenticated; SQLite read transactions are per-file, **not** global snapshots. Neither a synthetic SUCCEEDED marker, an unauthenticated token/clock, a digest nor a matching audit link attests permission, actual external action, idempotent effect or exactly-once delivery. UNKNOWN WRITE automatic retry is forbidden. Protected V2 final evaluation, Candidate training/preflight/promotion, paid/external compute, real devices and live ToolBackend remain disabled.

## Next plan / 今後の方針

1. Confirm #934/#935 on the **exact** SHA including Windows; narrow fixes only for observed regressions and never relabel FAIL as GREEN.
2. Extend read-only multi-DB crash matrix to cross-store race/erasure with independently retained witnesses and UNKNOWN non-replay, keeping DAG holds separate from actual authorization.
3. Advance Memory CAS, coherent snapshots/expiry, privacy revocation and content-minimized Personal Context projection without changing frozen schemas.
4. Keep scheduler retained-witness open fencing and Observation ingress independent of real notification/capture; define deny-by-default authenticated issuer / trusted clock / audit-before-action contracts, then connect only after lower-level exact-head validation. Maintain V3 provenance/identity/path/approval and no-spend boundaries.
