# ARK AI Run978 — Non-UI fail-closed compatibility repair and scheduler vector custody

## Scope and work basis

- **Work basis / prior checkpoint:** `dadd82faf033edf9ca05b412dbbbbfa4da83ff81` (Run977).
- **Target:** [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), `research/jarvis-foundations`, no main merge.
- **No UI/frontend modifications.** PR #9 paused; PR #5 remains gated Draft.
- Local, synthetic, disconnected test inputs only. No paid APIs, external GPU, actual Candidate, secrets, real executor, trusted-clock claims, consent, or promotion.

## Package 1 — CI regression repair without protocol relaxation

[Run977 exact checkpoint CI #44405903296](https://github.com/Iam-2squared/ark-ai/actions/runs/44405903296) completed **FAIL 6/6** (Ubuntu/Windows × Python 3.11–3.13). Ubuntu Python 3.11 showed **18,637 passed, 7 failed, 1 skipped**. All seven failures were outdated tests patching a newly pinned protocol object and expecting the old downstream ingress rejection rather than the stronger early refusal:

- Five cases in `tests/test_disconnected_read_journal_bounded_ingress_run905.py` patched `_SHA`, `_REQUEST`, or `_STEP`. The runtime now correctly refuses the substituted regex at the entrypoint with `synthetic READ hash-chain protocol changed`.
- One capacity override in `tests/test_personal_context_replay_ledger_run481.py` patched `_MAX_ROWS` and expected `full`. The runtime now refuses the changed replay protocol before reserving another request.
- One SQLite-preflight case in `tests/test_personal_context_replay_sqlite_preflight_run854.py` patched `_MAX_ROWS` and expected `persisted row budget`. The import-pinned limit now refuses before the private database scan.

Normal GitHub Contents API repair commits:

1. [`fd2b7ddb704c02e2b0cc6adfb64b8a4573486317`](https://github.com/Iam-2squared/ark-ai/commit/fd2b7ddb704c02e2b0cc6adfb64b8a4573486317): retain malicious regex canaries, assert refusal **before** their execution, and add **five** unpatched oversized-input regression cases preserving the original length checks.
2. [`a61688dea7fa95850dc9f2c56ed3f6f3f675b446`](https://github.com/Iam-2squared/ark-ai/commit/a61688dea7fa95850dc9f2c56ed3f6f3f675b446): expect protocol-custody rejection on forged replay capacity; after scoped patch restoration require retained witness unchanged.
3. [`4b104784c9bd56f9c59777a5f3b80a20d43b9609`](https://github.com/Iam-2squared/ark-ai/commit/4b104784c9bd56f9c59777a5f3b80a20d43b9609): expect unchanged replay protocol, reject replaced hash callback and changed limit without private hash hydration; after restoring scoped patches confirm the original persisted witness.

These **seven existing tests were updated**, not deleted; all relevant safety denials remain active. Source protocol guards were **not weakened**.

## Package 2 — Disconnected proactive recurrence-control vector custody

The detached recurrence preview already pins data-class slots, grant denials, SHA/JSON callbacks and finite bounds. Its vector iteration nevertheless relied on names/matrices that were themselves rebindable, allowing shortened or rebased control lists to change the scope of verification or throw an unclassified `zip(strict=True)` error.

- [Source `3c4436b4f81b44640f71af93739022965d8b8262`](https://github.com/Iam-2squared/ark-ai/commit/3c4436b4f81b44640f71af93739022965d8b8262): preserve import-time identities for all three control vectors and both descriptor matrices and reject any rebinding **before** inspecting synthetic schedule inputs or invoking occurrence callbacks.
- [Tests `54cee6b5c4bd823edea3eb3243c9d20b789194cc`](https://github.com/Iam-2squared/ark-ai/commit/54cee6b5c4bd823edea3eb3243c9d20b789194cc): **11** new cases covering five controls × (same-values rebinding or shortening) plus legitimate due preview and its five fail-closed authority properties; assert that a prohibited occurrence callback was never invoked and that the original preview remains deterministic after patch restoration.

No frozen V1/V2, Local UI/Launcher, Memory v1, ToolCall/PlanStep v1, Observation Envelope v1 or V3 protected review contract changed.

## CI and evidence limitations

- **Prior verified GREEN:** Run976 checkpoint `3db9f4f2fc1fb9a126b5d428801f2255af88b1b9`, [CI #44397552241](https://github.com/Iam-2squared/ark-ai/actions/runs/44397552241) 6/6.
- **Run977 found FAIL:** [CI #44405903296](https://github.com/Iam-2squared/ark-ai/actions/runs/44405903296), 6/6 fail at pytest (Ruff successful), with the exact seven test mismatches above.
- **Run978 latest repair tests:** [CI #44415504665](https://github.com/Iam-2squared/ark-ai/actions/runs/44415504665), **IN PROGRESS** at report preparation.
- **Proactive vector source:** [CI #44415872032](https://github.com/Iam-2squared/ark-ai/actions/runs/44415872032), **IN PROGRESS** at report preparation.
- **Proactive tests:** [CI #44416089881](https://github.com/Iam-2squared/ark-ai/actions/runs/44416089881), **QUEUED** at report preparation.
- **Full latest HEAD GREEN:** NOT YET VERIFIED. Added **16** authored cases (five READ ingress + eleven proactive vector); authored is not CI PASS. No local physical hardware or full test execution claimed.

The source hardening is interpreter-local instrumentation custody, **not** authentication of a person, absolute path/WAL/SHM stability, trusted time, consent, protection against malicious same-process code with arbitrary runtime access, or proof of an external exactly-once action.

## Remaining blockers and next plan

1. Confirm six CI jobs at the **exact latest checkpoint HEAD**; if FAIL, inspect logs, make the smallest semantics-preserving fix via normal GitHub path; work independent non-UI lanes during CI.
2. Memory WAL/SHM interprocess races, CAS/ABA and stable persisted event/expiry snapshots; manual/no-replay COMMIT-UNKNOWN proof.
3. Planner restart terminal propagation, ToolRegistry/PermissionGate, exact-one-shot authorization and trusted-clock audit-before-action, disconnected mock executor only after exact-head GREEN.
4. Privacy-safe Personal Context revocation/reuse, proactive occurrence replay/source custody, Observation fixtures, and free-only detached V3 approval/path/provenance guards.

**Overall JARVIS/ARK: NOT_PASSED.** PR #5/#8/#9 remain gated/unmerged; UI paused; no paid or protected actions.
