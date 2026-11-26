# Run750 — free-only non-UI CI repair, detached READ recovery and Memory CAS global history

**Scope:** Draft PR #8 `research/jarvis-foundations`, exact initial work-basis `62f0b80cf9133b513c34b9d982035bb929a33ad6`. Neither main, frozen V1/V2/Local UI/Launcher, V3 PR #5 nor paused Next UI PR #9 was modified. **ARK/JARVIS/V3 NOT_PASSED.** This is synthetic offline source/test evidence, not physical PC or external-effect evidence.

## Package A — correct CI lint, preserve PermissionGate semantics

- [CI #42707127293](https://github.com/Iam-2squared/ark-ai/actions/runs/42707127293), exact Run749 checkpoint HEAD `62f0b80c`, completed **FAIL all six jobs**. Ubuntu 3.11 job `129466756005` stopped at Ruff I001 in `tests/test_registered_permission_static_inspection_run749.py`; no pytest verdict exists for that run. The import block needed multiline formatting, not a policy behavior change.
- Commit `09c10d3d334cb7a1b19f0c2770e66342aa8e62df`: corrected only the test import formatting. No production code changed in this package. No duplicate equivalent CI was manually launched.

## Package B — detached READ recovery integrity

- [Source `821d5ed`](https://github.com/Iam-2squared/ark-ai/commit/821d5ed9b2c68c9fee5c82786480eb5f97ff7e5f): the opt-in offline recovery scheduler now pins the original `ReadRecoveryStep.__new__` together with its constructor/lookup hooks, and pins the step field/hook ordering vectors by **object identity**. A replaced constructor or equal-valued replacement vector is rejected before a caller-owned recovered step is read.
- [Tests `400544d`](https://github.com/Iam-2squared/ark-ai/commit/400544dca6ab1ea90ac5c52b920190af4139fcff): seven new cases (four hook substitutions, two vector substitutions, one normal non-authorizing baseline). [CI #42715152885](https://github.com/Iam-2squared/ark-ai/actions/runs/42715152885) failed all six jobs due solely to an observed Ruff I001 test-import blank-line complaint; test execution had not started. [Formatting correction `8fdfb59`](https://github.com/Iam-2squared/ark-ai/commit/8fdfb596738cd5afc7d881d387949c509a9dba9b) removed the extra blank line without changing assertions or source behavior.
- These steps still return **READY_MOCK_ONLY** diagnostic hints; no ToolBackend dispatch, automatic replay, real-world effect or approved actor identity.

## Package C — Memory CAS manual review cannot skip cross-scope high-water validation

- [Source `47e0b89`](https://github.com/Iam-2squared/ark-ai/commit/47e0b89d4408b75438c99d9a952ff1c19f4a1d05): preserves the original global SQLite Memory event high-water validator, checks it **before any private CAS review I/O**, and checks its identity again at existing staged custody boundaries. A runtime no-op substitution of the mandatory history check now fails closed rather than accepting a row-local witness without global append history scrutiny.
- [Tests `476d578`](https://github.com/Iam-2squared/ark-ai/commit/476d5784ffc0fe4a7e438fad9a315c07cd290a83): four new synthetic cases (no-op, throwing and noncallable check replacements before an uninitialized disposable store is touched; valid local unchanged review remains manual-only). No SQLite schema or frozen Memory v1 behavior was changed.
- This is **process-local mutable-function custody only**. It does not authenticate historical writer identity, independently anchor SQLite events, guarantee cross-process atomicity, resolve WAL/symlink/TOCTOU races, or authorize re-execution of an ambiguous COMMIT.

## CI and integrity limits

- At first post-repair read, [CI #42715601514](https://github.com/Iam-2squared/ark-ai/actions/runs/42715601514) on complete source/test head `8fdfb596738cd5afc7d881d387949c509a9dba9b` was **IN PROGRESS**; the prior `476d578`, `47e0b89` and `400544d` jobs did not provide exact-head GREEN evidence because of the now-corrected Ruff I001.
- New recovery/Memory tests **11 cases authored, all-platform PASS UNPROVEN** as of this report; no full local pytest, physical Windows GGUF, trusted clock, irreversible action, durable permission or no-cost external GPU claim.
- Source/test terminal HEAD `8fdfb596738cd5afc7d881d387949c509a9dba9b`. This engineering report and the later canonical PROJECT_STATUS checkpoint have **separate future commit SHAs**; they are not falsely embedded before GitHub returns them.

## Next plan / 今後の方針

1. Confirm the exact final checkpoint HEAD and all six Windows/Ubuntu Python 3.11–3.13 jobs; if FAIL, read the **actual job log**, fix only the proven defect through Contents API and switch to independent work while CI executes.
2. Advance transactional Memory CAS/ABA/expiry, coherent snapshots and manual-only COMMIT-UNKNOWN, retaining independent event/file custody caveats.
3. Advance Planner persisted exact READ recovery, immutable registered ToolRegistry/PermissionGate and restart-safe authorization/audit-before-action/occurrence over a **disconnected mock** executor only after lower layers independently GREEN.
4. Continue privacy-safe Personal Context, proactive and observation back-end contracts and zero-spend V3 identity/provenance/approval path inspection. No UI, paid service, Candidate, protected V2 evaluation or main merge absent explicit separate gate.
