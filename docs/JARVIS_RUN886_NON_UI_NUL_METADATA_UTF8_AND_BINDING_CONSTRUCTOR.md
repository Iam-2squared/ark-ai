# Run886 — Observation NUL CI repair, Context UTF-8, disconnected receipt constructor custody

**Scope:** Non-UI, local-first, synthetic-only. This document is descriptive engineering evidence, not trusted provenance, approval, consent or JARVIS PASS. No paid/external compute or live ToolBackend.

## Work basis and observed CI regression

Work-basis SHA: **6488e07c72910ee0e00351a403ce0a5438960079**, branch **research/jarvis-foundations**, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). [CI #43665496926](https://github.com/Iam-2squared/ark-ai/actions/runs/43665496926) **FAIL 6/6** (Windows/Ubuntu × Python 3.11–3.13). Logs confirmed two specific failures in **tests/test_observation_nul_metadata_consistency_run885.py**: the strict disconnected synthetic fixture failed to reject NUL source/privacy labels before hashing private fixture bytes. Ubuntu 3.12: 2 failed / 15,881 passed / 1 skipped; Windows 3.12: 2 failed / 15,783 passed / 99 skipped. This differs from the earlier reverted change that incorrectly banned NUL in the *frozen direct v1* ObservationEnvelope identity.

## NEW: three independent packages

1. **Fixture-only NUL repair**, normal Contents API commit **c89c3fcbbbbbc877794d14ca5ed13ecea269e73f**, modified **src/ark/disconnected_observation_fixture.py**. On the optional synthetic fixture admission path, exact string source_id and privacy_scope containing ASCII NUL are now refused with a fixture NUL separator error *before* the SHA-256 payload call. All seven already authored Run885 direct/fixture distinction cases remain unchanged. **src/ark/observations.py** stays at original blob **10c3b6e1d9f4635394e44dfa8893d3a5b9fccb30**. Direct v1 JSON-escaped NUL identities are deliberately accepted. No new tests are counted for this repair.

2. **Personal Context reflected metadata UTF-8 preflight**, source commit **b068665621191a1681eb9e355230eb653372c49f**, new tests commit **68724e0aabd7d3854f0830220b5f3605aaf1d1e4**. Files **src/ark/personal_context_review.py** and **tests/test_personal_context_metadata_utf8_budget_run886.py**. After exact MappingProxyType/64-entry/4,096-codepoint checks, each metadata key/value must encode as strict UTF-8 occupying at most 4,096 bytes, before any private Memory content digest/projection. Eight invalid multibyte/surrogate cases assert prehash rejection; four exact-byte-boundary cases assert inert non-authorizing output. **12 newly authored tests**. No frozen Memory v1 schema or storage/write contract change.

3. **Disconnected READ receipt constructor and slots**, source commit **c90f76cefc01f642a4a344ac0edcda93b091c54e**, new tests commit **ceac12b5c2e504a878a619e885a09776637c471e**. Files **src/ark/agency/disconnected_fixture_binding.py** and **tests/test_disconnected_binding_constructor_slot_custody_run886.py**. Before constructing an inert receipt, pin its exact class original __init__, __new__, and five data slot descriptors, additionally to preexisting negative-authority property guards. Two constructor/ five slot-getter substitution tests require zero counterfeit callbacks, and one normal fixture case retains digest and negative authorization. **8 newly authored tests**. No real external tool dispatch, Toolbox v1 identity alteration or automatic replay.

**Total NEW Run886 regression cases authored: 20** (12 + 8), **NOT yet verified exact-head GREEN**. The prior seven Run885 fixture cases are reused without double counting. Modified three non-UI implementation files, created two non-UI test files. Frozen V1/V2/Local UI/Launcher evidence and protected V2 evaluation unchanged. PR #5/#8/#9 remain Draft/unmerged; PR #9 UI is paused and untouched.

## CI pipelining (observed 2026-11-15, approximately 11:43 JST)

| Exact work HEAD | Actions run | Observed result |
| --- | --- | --- |
| 6488e07c72910ee0e00351a403ce0a5438960079 | [43665496926](https://github.com/Iam-2squared/ark-ai/actions/runs/43665496926) | **FAIL 6/6**, Run885 fixture mismatch |
| c89c3fcbbbbbc877794d14ca5ed13ecea269e73f | [43668846035](https://github.com/Iam-2squared/ark-ai/actions/runs/43668846035) | IN PROGRESS |
| b068665621191a1681eb9e355230eb653372c49f | [43668927621](https://github.com/Iam-2squared/ark-ai/actions/runs/43668927621) | IN PROGRESS |
| 68724e0aabd7d3854f0830220b5f3605aaf1d1e4 | [43668960061](https://github.com/Iam-2squared/ark-ai/actions/runs/43668960061) | IN PROGRESS |
| c90f76cefc01f642a4a344ac0edcda93b091c54e | [43669055846](https://github.com/Iam-2squared/ark-ai/actions/runs/43669055846) | QUEUED |
| ceac12b5c2e504a878a619e885a09776637c471e | [43669079067](https://github.com/Iam-2squared/ark-ai/actions/runs/43669079067) | QUEUED |

No redundant manual CI runs. No claim of latest-head six-job PASS. No independent local pytest/Ruff: execution container could not resolve github.com checkout DNS. CI runs remain the integration test source.

## Boundaries and Next plan / 今後の方針

Continue zero-cost/no-new-paid-service only. No external GPU, real Candidate adapter/weight/training/promotion, protected evaluation opening, actual hardware action, credentials, live tool dispatch, destructive operation, or main merge. Do not infer human review or trusted clock from these synthetic digests. Preserve all frozen contracts.

1. Verify exact-source/test/checkpoint-HEAD Windows/Ubuntu × Python 3.11–3.13 outcomes. On FAIL, inspect job logs and fix only the smallest semantics-preserving defect through ordinary Contents API, never weaken frozen direct Observation v1 NUL behavior.
2. Reproduce Windows SQLite WAL/SHM last-close and Privacy Revocation cross-process sidecar race with bounded, path-safe diagnostics. Ambiguous WRITE/COMMIT-UNKNOWN remains quarantined; no automatic replay.
3. Harden Memory CAS/expiry/event custody and Planner terminal/UNKNOWN restart recovery, then integrate immutable registry-bound permissions, audit-before-action and disconnected Mock Executor only after relevant exact-head GREEN.
4. Continue privacy-safe Personal Context/proactive scheduler/Observation fixture evidence and detached free V3 guard checks. PR #5 stays protected Draft; PR #9 is UI-paused Draft.

**Canonical overall latest checkpoint:** docs/PROJECT_STATUS.md, updated once near the end of this run on a freshly observed PR HEAD. This report itself does not assert checkpoint commit success.
