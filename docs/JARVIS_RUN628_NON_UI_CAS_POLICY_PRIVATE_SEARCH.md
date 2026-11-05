# Run628 — non-UI CAS outcome, direct policy, private-search guard

Work basis: Draft PR #8 `research/jarvis-foundations` commit
`8249672fc7c79bafb959347d5227d42e0a8fdcfd` (Run627 follow-up test fix).
Source/test implementations are **not** a new JARVIS PASS, a V3 experiment,
or a deployment. This document only records local/synthetic logic and exact
GitHub evidence available at creation.

## A. Memory COMMIT-UNKNOWN row/token reconciliation

- `src/ark/memory/generation_cas_outcome_review.py` rehashes the **returned**
  snapshot row and verifies it equals the observed generation token's row SHA.
  The hash callback is bracketed with exact-field, metadata, and nested-scope
  custody checks. A second `_snapshot` synthetic callback cannot overwrite
  the first record after its token hash and present a forged
  `ONE_MATCHING_UPDATE_OBSERVED` classification.
- `tests/test_memory_cas_outcome_row_image_reconciliation_run628.py`:
  5 parameterized second-snapshot mutations (including nested scope),
  1 forged matching row from a genuinely divergent update,
  1 post-digest record mutation: **7 authored cases**, not local PASS evidence.
- This does **not** attribute the update to the caller, establish authenticated
  history, permit CAS replay, or prove cross-store atomicity.

## B. Direct PermissionGate request-identity custody

- `src/ark/agency/policy.py`: both direct and registry-bound policy inspect
  the original `ToolCall` class's request/arguments digest descriptors and
  constructor/post-init before evaluating any grants or computing a request
  ID. Iteration and the process-local WRITE token-spend boundary recheck.
- `tests/test_permission_toolcall_identity_contract_run628.py`: 8 patched
  descriptor/hook cases across READ and WRITE, 2 generator-injected digest
  cases and 2 unchanged-policy controls: **12 authored cases**.
- The process-local one-shot set remains neither restart-safe approval nor
  external exactly-once dispatch. No backend is called.

## C. Privacy-safe lexical fixture getter custody

- `src/ark/offline_context_search.py` binds the exact input
  `OfflineContextSearchRecord` type, all frozen field descriptors and both
  Python lookup hooks before inspecting synthetic private text, and rechecks
  them during result construction. Descriptor comparison uses `is`, never
  user-defined equality.
- `tests/test_private_search_input_descriptor_custody_run628.py`:
  5 preinstalled hostile getter/field descriptor variants, 1 hash-callback
  installation and 1 unchanged local search: **7 authored cases**.
- No connected personal data, live MemoryStore scan, external disclosure,
  consent proof or retention grant.

## D. Startup readiness constructor custody (independent CI lane)

- `src/ark/startup_readiness_review.py` pins original `StartupComponent`
  initializer/validator, `ComponentResult` initializer, and
  `StartupSnapshot` initializer before synthetic probe intake, again after
  every iterator callback, before each validation/result construction, and
  after a potentially reentrant result-hash callback.
- `tests/test_startup_constructor_authority_run628.py`: 4 preinstalled
  constructor/hook attacks, 3 generator-timed constructor swaps, 1 hash-timed
  snapshot constructor swap, 1 unchanged dependency-blocked state:
  **9 new authored cases**.
- Startup READY is still just an untrusted, disconnected probe, never a
  backend activation permit.

**Total new authored pytest cases: 35; 4 source+test packages.**

## CI and corrections (do not inflate verification)

- Starting exact-head `8249672fc7c79bafb959347d5227d42e0a8fdcfd`:
  [CI #41992220098](https://github.com/Iam-2squared/ark-ai/actions/runs/41992220098)
  **6/6 GREEN** (Ubuntu/Windows, Python 3.11–3.13).
- Early new commits [#41993450165](https://github.com/Iam-2squared/ark-ai/actions/runs/41993450165),
  [#41993928824](https://github.com/Iam-2squared/ark-ai/actions/runs/41993928824),
  [#41994177474](https://github.com/Iam-2squared/ark-ai/actions/runs/41994177474)
  **FAIL** before pytest due to Ruff `I001` in two new import blocks.
  This is an actual test pipeline failure; do not call those source HEADs green.
- Format-only repairs saved as commits `c57d12d4974260f8de4a43d5943eb43922b33d18`
  (Memory) and `ef05645acb4af2db6a4c5ccbe7bdb5c8a1aa5e06`
  (PermissionGate). Exact repaired source/test
  [CI #41994595408](https://github.com/Iam-2squared/ark-ai/actions/runs/41994595408)
  **IN PROGRESS at initial report write**. All six final HEAD jobs and
  preexisting regressions remain **unverified** until their actual logs complete.
- Repaired `tests/test_private_search_input_descriptor_custody_run628.py`
  `__getattr__` fixture setup via `raising=False` in
  `defc5f7de112b02aaf5ebd282177414a032f1d81`: the absent method is
  intentionally injected for testing, and Python's monkeypatch refused its
  creation with the default `raising=True`. The source behavior was already
  fail-closed; [run #41994595408](https://github.com/Iam-2squared/ark-ai/actions/runs/41994595408)
  Ubuntu Python 3.11 reported **1 FAIL / 8,810 PASS / 1 SKIP**, exactly this
  fixture setup error. Repaired source/test
  [run #41995100643](https://github.com/Iam-2squared/ark-ai/actions/runs/41995100643)
  still awaits full six-platform confirmation.
- Startup source `929df9022e8b2d1bd2d0f6d9c9c5eb00c8f3fb60`
  and independent startup test `db6ba7876f30ed65213dbec18d27b9c1046f8c12`
  are newer than that CI, and require their own full exact-head verification.
- Local `git ls-remote` could not resolve github.com; **no local pytest/Ruff
  PASS is claimed**. Github Contents API writes were used, with PR HEAD
  checked before each write; no raw Git object or ref-update bypass.

## Frozen boundaries and next plan

Read-only review of PR #5 at HEAD
`805b377697472268db02650a89c7a94b1c5337c8` confirmed the
`PRE_PAID_COMPUTE_GATE.md` and `HF_IDENTITY_REVIEW.md` still distinguish
metadata from immutable source/weight evidence and prohibit real Candidate
generation without the approvals and exact bytes. PR #5 remains Draft.
PR #9 (UI) remains paused, Draft, untouched; main and frozen
V1/V2/Local UI/Launcher/V3 Contract unchanged. No paid/potentially billable
GPU/API/service, credentials, protected V2 final evaluation, external effects,
physical-PC action, destructive operation, Candidate promotion or main merge.

**Next:** (1) settle exact repaired CI and repair real regressions from logs;
(2) preserve Memory CAS/row/event checks and manual-only ambiguity;
(3) strengthen durable Planner/Occurrence/PermissionGate through disconnected
mock integration only after exact-head green; (4) re-audit free-only V3 guards
without opening the protected training/evaluation gate. ARK/JARVIS/V3
**NOT_PASSED**.
