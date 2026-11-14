# Run744 — Non-UI CI failure repair, synthetic Windows SQLite sidecar budget, Planner post-COMMIT-UNKNOWN fixture

Saved source/test evidence: 2026-11-10 JST. This document is an engineering record, **not** a JARVIS completion result, trusted runtime clock, executed real tool action, user approval, or authenticated provenance.

## Basis and independent observations

- Repository `Iam-2squared/ark-ai`; Draft PR #8 `research/jarvis-foundations`; first verified work-basis HEAD `7ef9c27e54908588fef695ab9d75f78c8da74c8c` (Run743 checkpoint).
- [Run743 checkpoint CI #42658796633](https://github.com/Iam-2squared/ark-ai/actions/runs/42658796633) finished **6/6 FAIL** (Ubuntu and Windows × Python 3.11–3.13). Ruff succeeded; pytest failed in the same six new `tests/test_private_diagnostic_result_denial_run743.py` parametrized cases. The exact observed exception was `RetainedDiagnosticChainRejected("diagnostic segment review protocol changed")`, not the fixture's expected `"result changed"`.
- Source inspection proves `_protocol()` holds original class-level denial descriptors and executes before processing caller segment bytes. Replacing either denial `property` makes the substitute getter **unreachable**. The test had incorrectly expected its malicious getter to run. This is a **test expectation defect**, not evidence that the protocol should allow the getter.
- Main, PR #5, UI PR #9 and frozen evidence/contracts are outside the work; no main merge or live tool integration.

## Package A — exact fail-closed CI repair

- Normal GitHub Contents API commit [`754a5ba`](https://github.com/Iam-2squared/ark-ai/commit/754a5ba123237c46a4dfdeb48305797a16b0e681) changes the six incorrect tests to expect **early `protocol changed` refusal** and assert malicious getter call count **zero**.
- The existing success-path test remains, the substitution tests remain parametrized, and **no production safety rule was relaxed**.
- This does **not** claim the late-getter mutation test mechanism was exercised. The import-time descriptor pin prevents this particular injected callback from running, so a separate permitted reentrant seam would be required to exercise the later receipt-field recheck.

## Package B — synthetic Windows SQLite sidecar path budget

- Source commit [`0dcc5d9`](https://github.com/Iam-2squared/ark-ai/commit/0dcc5d967eff9630a959b8b9034cb3c67737f8b5) now requires every synthetic SQLite name (`main`, `-wal`, `-shm`, `-journal`) to fit the same 240-character lexical cap, instead of testing only the main file.
- Test commit [`186b72d`](https://github.com/Iam-2squared/ark-ai/commit/186b72d9b9e288250a164e29882e311151080fbf) adds **11 authored cases**: exact 232-character main/240-character `-journal` acceptance, six overlong rollback sidecar rejections with no path disclosure, mutated-limit protocol rejection, and three deterministic no-authority checks.
- This is **strictly detached lexical review**: no Windows `CreateFile`, handle, reparse-point, ACL, hardlink, SQLite connection, WAL observation, identity/custody proof, or dispatch authorization. The 240-character ceiling is a local synthetic policy, not an OS-wide maximum.

## Package C — Planner crash/restart observation

- Test commit [`033a441`](https://github.com/Iam-2squared/ark-ai/commit/033a4416a3ee8e9b6d524b6ad65ffde11b7aa4a8) adds **2 authored tests** in a new, non-UI module.
- Inject failure **after** the local synthetic journal commits (from its post-commit result-check callback): the API raises, but a fresh journal handle still observes one durable RUNNING event. Recovery treats it as ambiguous, denies both dispatch and automatic replay, and stale-revision retry is rejected. A parallel test injects failure **before** commit, requiring the original empty tail to persist.
- These tests are designed to differentiate uncertain caller result from actual database transaction state; they do **not** create external effects, prove real execution exactly-once, resolve human consent, or authorize replay. If the exact-head CI fails, diagnose actual logs instead of assuming these tests pass.

## CI / evidence exactness

- Run743 checkpoint SHA `7ef9c27e...` **FAIL 6/6**: run `42658796633` above. This result is **not** a verdict for the repair.
- Repair commit `754a5ba...`: [CI #42667912622](https://github.com/Iam-2squared/ark-ai/actions/runs/42667912622) **IN PROGRESS** at last read.
- Sidecar source commit `0dcc5d9...`: [CI #42668310671](https://github.com/Iam-2squared/ark-ai/actions/runs/42668310671) **IN PROGRESS** at last read.
- Sidecar test commit `186b72d...`: [CI #42668385589](https://github.com/Iam-2squared/ark-ai/actions/runs/42668385589) **IN PROGRESS** at last read.
- Planner test commit `033a441...`: [CI #42668526280](https://github.com/Iam-2squared/ark-ai/actions/runs/42668526280) **QUEUED** at last read.
- Neither 11 new Windows fixture cases nor 2 new Planner crash tests have **exact-head multi-platform GREEN** evidence yet. A future report/checkpoint commit creates a different HEAD and CI, which must be evaluated separately. No duplicate CI run requested, no local full suite or target-PC verification performed.

## Boundaries, defects and next

1. Prioritize exact-head Windows/Ubuntu × Python 3.11–3.13 CI, diagnose new failures from concrete job logs, and make only minimal semantics-preserving repairs. Do not transfer GREEN between SHAs.
2. Retain current **manual-only** COMMIT-UNKNOWN policy; neither a matching snapshot nor a Python post-commit exception authenticates a writer or permits an automatic retry.
3. Advance Memory SQLite row/event consistency, global high-water and expiry/CAS, and Planner persisted READ terminal lineage only after lower-level exact-head invariants hold.
4. Continue registry-bound ToolRegistry, exact-type PermissionGate, occurrence/clock/audit-before-action and disconnected mock executor; then privacy-first Personal Context and observation/scheduler backends.
5. Frozen V1/V2/Local UI/Launcher contracts and evidence untouched; PR #5 and paused UI PR #9 remain Draft/unmerged; no UI work, paid/external GPU/API, real Candidate training, protected V2 opening, actual tool, secret, irreversible operation or main merge. JARVIS/V3 PASS remains **NOT_PASSED**.
