# Run849 — non-UI startup regression repair and privacy-veto ingress limits

Basis: `7b73bcf17a339d04d53aa2d1675ab3622b60172d` (Run848 checkpoint).
Work branch: `research/jarvis-foundations`, Draft PR #8; no main merge.
Overall ARK/JARVIS **NOT_PASSED**. This is disconnected/local fixture work
only, not an authority, approval, independent witness or hardware test.

## 1. Exact-HEAD CI failure triage

GitHub Actions [#43440474389](https://github.com/Iam-2squared/ark-ai/actions/runs/43440474389)
completed **FAIL 6/6** (Windows/Ubuntu × Python 3.11–3.13) on Run848's
`7b73bcf1`. Inspected Ubuntu 3.12 job `131936473853` and Windows 3.12
job `131936473830`. Both reported the same new/reinterpreted legacy
expectation in
`tests/test_disconnected_readiness_pregetter_run612.py::test_first_denial_read_cannot_activate_second_descriptor[schema]`:
the test asserted the injected `__getattribute__` callback executed once,
while current production preaccess correctly rejected that substituted
schema carrier **before the first getter** (`observed["injection"] == 0`).
Ubuntu 3.12 reported 1 failed / 15,058 passed / 1 skipped. Windows 3.12
reported 1 failed / 14,974 passed / 85 skipped. Ruff passed in the inspected
Ubuntu job. The mismatch is a *test expectation* failure, not proof that
production dispatch occurred; it also cannot be counted as green.

Normal Contents API commit
[`6ed922de`](https://github.com/Iam-2squared/ark-ai/commit/6ed922de58859023ede5543efeaad1c13a7c96e1)
now expects zero reentrant getter calls for **schema, registered-READ
preflight and final report**, and still requires no malicious second
descriptor execution and zero backend calls. The safer production carrier
preflight remains unchanged; no denial is weakened.

## 2. Independent privacy-veto input package

Normal Contents API source commit
[`2fdb2d45`](https://github.com/Iam-2squared/ark-ai/commit/2fdb2d459cebc0df1932443f289fcdae8f3bd000)
limits SHA-256-like pseudonymous owner/scope/witness fingerprints to **exactly
64 characters before the regular-expression matcher**, and refuses
synthetic ledger paths over **4,096 characters before filesystem access**.
Existing exact-path, no-symlink/single-link sidecar and restart fail-closed
checks are unchanged.

New test file
[`84af33a5`](https://github.com/Iam-2squared/ark-ai/commit/84af33a5099e6881ea640468dbce440fca4656dc)
adds **31 authored parameterized cases**: 28 malformed hash combinations
(review/veto × owner/scope × 7 invalid values) with a bounded matcher and
forbidden SQLite-open sentinel; 2 oversized path cases; 1 positive valid
reopen/one-way veto case. Follow-up test-only matcher anchor correction
[`60d47052`](https://github.com/Iam-2squared/ark-ai/commit/60d4705235d018f3eb7852e07a8de50fc1685708)
ensures the guard accepts an exact valid 64-character lowercase hex string
rather than accidentally rejecting it. These are **authored**, not claimed
31 PASS. No actual user data, consent, deletion, identity provider, external
tools or real action.

## CI pipeline (as observed during invocation)

- Fix `6ed922de`: [#43445271968](https://github.com/Iam-2squared/ark-ai/actions/runs/43445271968) **IN PROGRESS** at prior check.
- Privacy source `2fdb2d45`: [#43445662243](https://github.com/Iam-2squared/ark-ai/actions/runs/43445662243) **IN PROGRESS** at prior check.
- Corrected privacy test `60d47052`: [#43445854671](https://github.com/Iam-2squared/ark-ai/actions/runs/43445854671) **QUEUED** at prior check.
- The above results are per exact commit and not transferable to a later
  report/checkpoint HEAD. No duplicate manual CI runs. No full local Ruff,
  pytest or unavailable physical-PC/GGUF evaluation.

## Boundaries and next investigation

Preserve V1/V2/Local UI/Launcher frozen evidence, V3 protected final-evaluation
gate, Draft/unmerged PR #5, Draft/unmerged PR #8 and paused/untouched UI PR #9.
Do not pay, start an external GPU/API, generate a real Candidate, promote,
request secrets, execute real tools, expose private content, auto-retry a
COMMIT-UNKNOWN write or merge main. Previously observed SQLite WAL/SHM
last-close unlink is a disposable diagnostic; a causal fix for ARK's previous
concurrent failures is **not established**.

Priority after exact-head CI: (1) diagnose any fresh failures without
loosening denial invariants; (2) measure Memory/ActionAudit WAl/SHM
last-close race and retained descriptors on disposable stores; (3) improve
Memory global event/restart coherence and Planner persistent UNKNOWN;
(4) join immutable ToolRegistry, exact PermissionGate, audit-before-action
and disconnected Mock Executor only after exact-head prerequisites turn green;
(5) continue privacy-safe Personal Context, proactive and observation
backend contracts and free-only V3 guards. No UI development.

## Subsequent CI finding and safer source correction

Following `6ed922de`, inspected Ubuntu Python 3.13 job
`131952960659` in [#43445271968](https://github.com/Iam-2squared/ark-ai/actions/runs/43445271968).
The schema case was repaired, but the `[report]` case failed
`assert 1 == 0`; Ubuntu Python 3.11/3.12 in this same earlier run also
failed. This revealed that the final inert readiness report had **not yet
pinned its `__getattribute__` hook** before evaluating the first
False-only property. The earlier blanket assumption that all three
carriers rejected preaccess was therefore premature.

Rather than weaken the test to tolerate invoking a caller-substituted
getter, [source repair `80092450`](https://github.com/Iam-2squared/ark-ai/commit/800924502aa35d622987fc86bc0db86ae70887fe)
now pins report `__new__`, `__getattribute__` and `__getattr__`
class descriptors and rejects replacement during `_require_original_denials`
before constructing/inspecting a report. Existing coverage requires
zero first/second injected callbacks for schema, preflight and report.
No start, registry dispatch, authority, frozen evidence or UI is changed.
**The exact source-repair HEAD CI remains UNVERIFIED** until the automatic
six-job workflow has completed.
