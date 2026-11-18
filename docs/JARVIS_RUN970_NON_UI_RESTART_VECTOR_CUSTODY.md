# ARK AI Run970 — Three disconnected recovery guard-vector corrections

> Evidence scope: 2026-11-18 JST; Draft PR #8 (`research/jarvis-foundations`). This report is technical evidence of saved code/tests, **not** a JARVIS PASS, execution authority, consent, or exact-HEAD CI certification.

## Work basis and committed packages

- **Work-basis HEAD:** `362f14cd0bd23848788a5e5db6001cf44239ee35` (Run969 checkpoint). Its [CI #44320183286](https://github.com/Iam-2squared/ark-ai/actions/runs/44320183286) finished **SUCCESS, six of six jobs** during Run970. That verifies the *preceding* commit only, not the new Run970 changes.
- **Memory expiry-restart receipt:** source `dc520aa788d93abd3341ac5ce8e356d924819b13`, test `7a12ac28145e05d7bc145a1ee14661d5e3cf3564`. `_FIELDS` is now guarded against replacement before the per-scope page aggregation, hashing or retained expiry witness read. Four authored negative cases cover empty, truncated, reversed and equal-valued rebuilt tuple. This does **not** authorize Memory purge or independently prove a trusted clock/cross-scope atomic snapshot.
- **Audit COMMIT-UNKNOWN reviewer:** source `212c6735826fdf86194c3df75a9da3ccfa77fa7d`, test `78f42c3ed9b4d9351937848c1b313f6d307e3c03`. Both `_RESULT_FIELDS` and `_LEDGER_HOOK_NAMES` identities are pinned before ledger, SQLite or claim handling. Eight authored tamper tests and one normal disconnected genesis/no-retry test. Local SQLite membership is never evidence of an external effect; manual review remains mandatory.
- **Planner/WRITE-slot restart bridge:** source `28a3d0f7cadb32d4e1871753ee8e666b98c22da9`, test `e2b251201a68c52c44feadd4a7439a4949c5d1d4`. Pin `_FIELDS`, `_INPUT_TYPES`, `_INPUT_FIELD_NAMES` and `_INPUT_HOOKS` before inspecting any recovered Planner or durable WRITE-slot input. Twelve authored truncated/reversed/rebuilt vector negative cases; no actual planner replay or tool dispatch.

**Total authored:** 25 new regression cases across three isolated modules, with three small production guard repairs. No tests deleted; no frozen contract touched. The test suite was not run locally against the complete repository; GitHub CI is authoritative for exact commits.

## Strict CI provenance

- Prior [#44320183286](https://github.com/Iam-2squared/ark-ai/actions/runs/44320183286): **GREEN 6/6** for `362f14c`, preceding all Run970 changes.
- Memory source [#44327352892](https://github.com/Iam-2squared/ark-ai/actions/runs/44327352892), Atomic source [#44327482717](https://github.com/Iam-2squared/ark-ai/actions/runs/44327482717), Memory regression [#44327646057](https://github.com/Iam-2squared/ark-ai/actions/runs/44327646057), Atomic regression [#44327726610](https://github.com/Iam-2squared/ark-ai/actions/runs/44327726610), Planner source [#44328037759](https://github.com/Iam-2squared/ark-ai/actions/runs/44328037759), Planner regression [#44328099797](https://github.com/Iam-2squared/ark-ai/actions/runs/44328099797) were launched automatically. They were **IN PROGRESS / QUEUED** at first sampling, with no claim of full six-job GREEN for the new exact HEAD.
- Different independent modules were changed while earlier CI was in flight. No duplicate workflow runs were launched.

## Preserved boundaries

Frozen V1, V2 final evaluation, Memory v1, Observation Envelope v1, Local UI, Launcher and V3 Contract 1 and contamination/provenance/reproducibility gates were not changed. PR #5 remains approval-gated Draft/unmerged; paused UI PR #9 untouched/Draft/unmerged; PR #8 Draft/unmerged. main was not merged. No paid/external compute, real Candidate adapter or weights, credentials, live tools, destructive action, physical-PC work, or autonomous effect.

## Next checks

1. Confirm six exact-head Windows/Ubuntu × Python 3.11–3.13 CI jobs for the final code + tests. Any red test must be fixed with normal Contents writes, keeping strict rejection assertions.
2. Test more substantive cross-process Memory WAL/SHM/expiry and Planner COMMIT-UNKNOWN recovered source consistency after exact-head GREEN, still mock-only.
3. Integrate PermissionGate, immutable ToolRegistry and audit-before-action only after lower-layer evidence is GREEN, with no automatic replay.
4. Continue Personal Context/privacy/proactive/observation/V3 free-only guards; UI remains paused.

**Overall ARK/JARVIS NOT_PASSED.**
