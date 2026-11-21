# ARK AI — Run616 non-UI core: recovery CI repair, CAS/attention/audit constructor custody

## Scope and starting evidence

- Work-basis HEAD: `7f000533573c6e0378fbef0151762ec71fa24958`, Draft PR #8 (`research/jarvis-foundations`).
- The preexisting Run615 source/tests for synthetic reservation review and mixed-plan WRITE recovery were NOT made here. Their latest source-head CI #41919481918 failed three legacy tests because an earlier and stricter constructor/authority preflight now rejects the spoofed disposition before the tests' old expected failure point.
- This invocation changes only non-UI, reversible, offline core work. No account connection, paid service, GPU, real notification, live tool/backend dispatch, physical PC, protected V2 evaluation or frozen contract change.

## Work package A — mixed-plan recovery test correction

- Test-only commit `b9ec19d28554afa4fb7f168a1f5858c3f37f4593` updates three old error assertions in `tests/test_disconnected_recovery_result_carriers_run470.py`.
- The existing product code now rejects a rebound disposition constructor at the earliest `mixed-plan authority descriptor changed` preflight, not the historical later disposition-carrier check. Tests explicitly require that **no** counterfeit factory callback runs and that no mutating disposition is created.
- This is a strengthening of executed-callback absence, not weaker permission validation. Actual WRITE is still never dispatched or automatically retried. Source-head #41919481918 failure was independently read from GitHub CI logs; its old expectation is not silently declared GREEN.

## Work package B — Memory generation-CAS ambiguous outcome

- Source `ddf30b8afd767f335ab8c9c01d14ecfee30f2590`, tests `6640032eca5afef7dd005702d16f01813ebb0255`.
- Pin original `MemoryCASOutcomeReview.__init__` together with the already pinned class and deny-only authority descriptors; validate before opening a SQLite read and again before invoking result construction. Call the pinned original type, not an imported symbol that can be rebound during an arbitrary hashing callback.
- Three new authored parameter-expanded regression cases cover preinstalled actual constructor replacement (without SQLite open), hash-phase replacement (no forged constructor call), and a deterministic unchanged/manual-only result.
- A matching SQLite row or event prefix is **not** independent proof of caller attribution, trusted time, consent, safe retry or any external effect.

## Work package C — detached proactive attention

- Source `66e54b075b05269c78478230f383936a788fb329`, tests `b29832e5991b83d88dd1ab0e1d1fc067990f0e33`.
- Pin the original inert `AttentionBudgetPreview.__init__`, check the original definition again after digest callbacks, and refuse a forged constructor even if notification/consent properties remain False.
- Three authored cases test preinstalled and digest-time substituted constructors plus the unchanged REVIEW_ONLY non-authorizing result.
- Earlier CI #41921436538 found 10 old tests using an injected `__init__` to observe generated previews. That instrumentation is now rejected *before* either preview is returned.
- Test-only correction `06946ccdbf6d1b22f600fe7cb02249d55f717fed` changes those old tests to capture original results through a passive `__getattribute__` read hook instead, preserving the later JSON/hash reflective-mutation assertion for each scalar and for both source previews. No requirement to detect post-callback drift was dropped.
- A synthetic attention REVIEW_ONLY result is never user consent, notification delivery, trusted clock, or execution authority.

## Work package D — read-only audit continuity

- Source `97147523238601b78799d4321a466a8e41c5e4a7`, tests `ca2a3f8c7b51a3e8e6443ac6e2e6b32879631517`.
- Pin original `AuditContinuityWitness.__init__`; preflight it before database access, continuously recheck through SQLite/history/hash callbacks, and use pinned witness type at final construction.
- Four authored regression cases cover original class actual constructor replacement before and during row processing, swapped imported constructor factory, and an unmodified one-event retained prefix.
- This local SQLite audit is not a signed or external authorization ledger and does not prove exactly-once effects, authenticated actors, historical writer identity or verified time.

## Evidence, limitations and gate continuity

- Exact compare from work-basis `7f000533...` to `06946cc...`: **8 commits and 8 paths** (three non-UI source, three new test files, two legacy test repairs). **10 new parameter-expanded pytest cases authored (3+3+4), not locally executed PASS claims.**
- Container GitHub clone was not available: DNS lookup for github.com failed. Use GitHub Actions for actual executed test evidence, and never conflate authored cases with observed PASS counts.
- Prior Run614 checkpoint CI #41911020066 is 6/6 GREEN; Run615 original constructor source/test HEAD CI #41919481918 had three legacy test failures. During this invocation, correction CI #41920989072 and Memory case CI #41921290194 reached Ubuntu 3/3 GREEN. Proactive source/test intermediate CI had 10 legacy test failures; the subsequent instrumentation repair must be tested at its own exact HEAD. Do not infer final head six-job GREEN until observed.
- Frozen V1/V2/Local UI/Launcher evidence, main, PR #5 (V3 approval gate), and paused Draft PR #9 UI branch remain unchanged. PR #5/#8/#9 remain Draft/unmerged; ARK/JARVIS/V3 stay **NOT_PASSED**.
- UNKNOWN WRITE and COMMIT-UNKNOWN remain manual/quarantined: no auto-replay, automatic Candidate promotion, real GPU/model training, real tool/notification, protected evaluation, or approval-required merge.

## Next plan / 今後の方針

1. Verify the exact latest HEAD across Ubuntu/Windows Python 3.11–3.13, fix only real CI failures using the ordinary GitHub Contents path, and avoid duplicate reruns.
2. Continue Memory CAS ambiguous COMMIT manual reconstruction with coherent retained row/event history, without falsely attributing the writer.
3. Advance Planner durable recovery and registered ToolRegistry/PermissionGate/audit-before-*mock*-action/occurrence fencing after dependent exact-head GREEN.
4. Continue privacy-safe Personal Context and proactive/observation back-end work, and free-only V3 identity/approval/path guards. Keep all frontend and PR #9 work paused.
