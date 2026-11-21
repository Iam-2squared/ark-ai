# ARK AI Run907 — bounded detached Planner/SQLite/Context ingress (non-UI)

This source-grounded report describes three reversible, disconnected core safety packages. **ARK/JARVIS NOT_PASSED**. No real user/private data, real tools, training, export, approvals, UI integration, physical-PC access, GPU, paid API or other billable actions were used. This document does not amend frozen evaluation contracts.

## Basis and verified previous CI

Initial PR #8 branch `research/jarvis-foundations` HEAD: `9b43274d0107fd6dee7046189d7d0f6acf0a909d`. [CI #43772661471](https://github.com/Iam-2squared/ark-ai/actions/runs/43772661471) was verified **GREEN 6/6** (Windows/Ubuntu × Python 3.11–3.13). It certifies only that earlier HEAD, not this run's changes.

## Package 1 — Planner replay tail hash admission

- [Source `b45825628`](https://github.com/Iam-2squared/ark-ai/commit/b45825628d5c79e050653180f91d7ca5ffb2361d): `SyntheticPlanTail.assert_shape` now rejects reflected arbitrary-length topology/event/status strings *before* the respective digest regex. The exact valid lengths remain `plan_`+64 = 69, `pevt_`+64 = 69, `pstate_`+64 = 71.
- [Tests `2d0f37744`](https://github.com/Iam-2squared/ark-ai/commit/2d0f37744a3ac0bae278851928ec84a21dc5a785): **seven authored cases** (three overlong cases with a poison-regex witness; three fixed-width invalid-hex negatives; valid synthetic genesis and denial-only RUNNING recovery). No Planner schema, execution/retry behavior, frozen contracts or real tool interfaces changed.
- [CI #43776463428](https://github.com/Iam-2squared/ark-ai/actions/runs/43776463428) and [#43776413786](https://github.com/Iam-2squared/ark-ai/actions/runs/43776413786) were **IN PROGRESS** at first examination, not claimed GREEN.

## Package 2 — disconnected SQLite schema seal hash admission

- [Source `109ac85e`](https://github.com/Iam-2squared/ark-ai/commit/109ac85e191c47b19ae5607b794d3ff165edf5c4): reject a caller-retained malformed/overlong `schema_sha256` unless exact-length 64, *before* SHA regex or opening a connection transaction. The capture path and schema hashing are otherwise unchanged.
- [Tests `f965af63`](https://github.com/Iam-2squared/ark-ai/commit/f965af6383efa5d0aaa42802308e071abbc68a4f): **five authored cases** for too short, too long, very long ASCII/Japanese seal fields; query-only, transaction state, valid re-review and no-disclosure/no-WAL-proof flags are checked. In-memory synthetic SQLite only.
- [CI #43776512501](https://github.com/Iam-2squared/ark-ai/actions/runs/43776512501) was **IN PROGRESS**, [#43776578190](https://github.com/Iam-2squared/ark-ai/actions/runs/43776578190) **QUEUED** at observation.

## Package 3 — offline lexical Personal Context text preallocation fence

- [Source `8d36937c`](https://github.com/Iam-2squared/ark-ai/commit/8d36937c8d706dd8e92356b6ffea868fac01edbc): reject exact `str` input whose codepoint count already exceeds the configured UTF-8 byte budget **before** constructing a temporary encoded copy. Existing strict UTF-8 encoding and byte-count check still reject multibyte overflow.
- [Tests `3c765be9`](https://github.com/Iam-2squared/ark-ai/commit/3c765be9cd8b710bbf06d2373f5a6a912fe1c103): **nine authored cases** including large query/document strings, exact 512-byte ASCII boundary, multibyte overflow, deterministic normal fixture and result denial-only flags.
- [CI #43776637075](https://github.com/Iam-2squared/ark-ai/actions/runs/43776637075) and latest complete-source/test [#43776698907](https://github.com/Iam-2squared/ark-ai/actions/runs/43776698907) were **QUEUED** at observation. These runs were not manually duplicated.

**Total: 3 coherent packages, 21 regression cases AUTHORED; latest exact-HEAD six-platform PASS not yet established at first documentation.** Successful GitHub writes used the normal Contents API after fresh PR HEAD reads. No alternate raw Git/force path.

## Separate read-only investigation — revocation WAL/SHM last-close race

The existing strict [two-process test](https://github.com/Iam-2squared/ark-ai/blob/9b43274d0107fd6dee7046189d7d0f6acf0a909d/tests/test_privacy_revocation_cross_process_run425.py) requires one `REVOKED` winner, one `ALREADY` loser, and one independent durable row. Historical Run902 diagnostics observed a different situation: one durable row and a second child **SIDECAR_REFUSED** while WAL/SHM pathnames vanished after SQLite last-close. That is an actual **FAIL/UNKNOWN**, not a success or permission to retry. The disposable [standalone diagnostic](https://github.com/Iam-2squared/ark-ai/blob/9b43274d0107fd6dee7046189d7d0f6acf0a909d/scripts/diagnose_revocation_wal_processes.py) already has a `--wal-keeper` comparison to isolate closing behavior; its outcome must not be invented or used as an execution-authorization proof. No race test, path custody rule, privacy-veto refusal or keeper semantics changed in Run907.

## Frozen boundaries, remaining blockers, next integration order

Unchanged and untouched: frozen V1/V2/Local UI/Launcher evidence, protected V2 final evaluation, protected V3 Draft PR #5 and approval/identity/provenance/Candidate gates, paused UI Draft PR #9, main, Memory v1 and Planner journal v1 schemas. No real ToolBackend, private export, capture, paid/external compute, credentials, destructive change or approved main merge.

Open failures/gates: cross-platform SQLite WAL/SHM last-close contender rejection, independent source/witness custody, Planner cross-store COMMIT-UNKNOWN quarantine, Memory event/CAS/expiry provenance, trusted-clock audit-before-action, physical-PC local GGUF gate and protected V3 approvals. Prioritized next steps: (1) certify or minimally fix the exact current six-platform CI; (2) isolate WAL/SHM race by disposable controls without false success/retry; (3) strengthen Memory and Planner recovery; (4) only after verified lower-layer GREEN integrate immutable ToolRegistry, exact PermissionGate, durable audit and disconnected Mock Executor; (5) advance privacy-safe Personal Context, proactive/observation and free V3 guard reviews. **Overall NOT_PASSED.**
