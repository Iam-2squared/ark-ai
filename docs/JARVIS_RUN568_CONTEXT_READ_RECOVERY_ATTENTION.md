# Run568 — fail-closed context/READ recovery and detached proactive attention

Work basis (PR #8 before this invocation): `8eb74a3be88aaca96cf15b5f40219dc4993943dd`. All work is on Draft, unmerged `research/jarvis-foundations`; no main change, paid provider, external GPU, physical-PC action, Candidate or protected V2 evaluation.

## 1. CI-grounded Personal Context inherited-test corrections

Initial exact-head [CI 41549026979](https://github.com/Iam-2squared/ark-ai/actions/runs/41549026979) completed **FAILURE (six jobs)**. Its Python jobs showed eight inherited tests failing because the newer original-property guard correctly rejects a constructor or denial replacement with `context preview authority definition changed`, earlier than the previous `constructed` message. The corrections are:

- `d778efbe`: construct an honest preview **before** intentionally substituting the binding-stage denial callback, preserving actual late-callback assertions.
- `09c76410`: align two existing serialization/authority expectations to the early original-definition refusal.
- `6821bfca`: align an existing forged-result-constructor test to the same early fail-closed boundary.

The corrected exact-head [CI 41554736530](https://github.com/Iam-2squared/ark-ai/actions/runs/41554736530) is separately tracked; only GitHub's final six-job conclusion establishes GREEN.

## 2. Disconnected READ recovery import-pinned authorization descriptors

- Source `9a5939c1` now pins the three deny-only `DetachedReadRecoverySchedule` properties at module import, and rechecks them at entry and every state epoch, **before hashing or graph classification**. No untrusted property can become the baseline merely by returning `False`.
- Existing late-callback tests adjusted at `7a32f4aa`, and **10 new parameter-expanded cases** added at `71d796db`: six prior false/true class-property replacements before hashing, three in-flight hash callback replacements, one deterministic no-replay case.
- Initial [CI 41555089253](https://github.com/Iam-2squared/ark-ai/actions/runs/41555089253) exposed six inherited tests that still replaced the original result class/property and expected later failure after processing. Follow-up changes `0d273f62` and `32056379` preserve late nested-decision and getter-callback coverage using instance attribute interception rather than replacing the import-pinned class definitions.
- At this note's preparation, latest source+test CI is **not asserted GREEN**; consult exact HEAD/individual GitHub jobs. The disconnected `READY_MOCK_ONLY` classification never grants ToolRegistry dispatch, external outcome truth or automatic replay.

## 3. New standalone proactive attention-budget review

- Source `ef3bfe93` adds `src/ark/proactive_attention_preview.py`, independently reversible and not connected to any scheduler service.
- Synthetic policy and content-free surfaced markers are exact-type and bounded; source/trigger scope hashes must match; occurrence identities must be unique, strictly chronological and not from the future; at most 256 history markers are accepted.
- Deterministic dispositions: `ALREADY_RECORDED`, `UNCHANGED_SUPPRESSED`, `COOLDOWN_HOLD`, `WINDOW_BUDGET_HOLD`, `REVIEW_ONLY`. The rolling window's lower endpoint is **exclusive** and cooldown releases at the exact configured boundary. Hash-only output binds policy/history and candidate observation/clock separately using domain-separated SHA-256.
- Test `6470df69`: **31 new parameter-expanded pytest cases** covering honest deterministic paths, exact cooldown/window boundaries, repeated occurrence and unchanged observations, malformed/cross-scope/reordered/future history, invalid policies, preinstalled false-denial properties before hashing, in-flight mutation and a final getter mutating output evidence.
- A `REVIEW_ONLY` disposition is **not** a notification authorization. Four original denial descriptors remain false: notification, action, trusted clock and consent. No notification, scheduling timer, data export, real sensor, external interaction or live account is activated. Caller-provided time and hashes are **not authenticated evidence**.

## Boundaries, evidence and integration

The new component is detached from scheduler state; no migration, real-time signaling, durable one-shot grant, trusted clock or live permission integration is implied. Frozen V1/V2/Local UI/Launcher, Memory/Planner contracts and PR #5's V3 Contract are not edited here. Real Candidate training, protected evaluation, promotion and main merge remain independently gated. Both PR #5 and PR #8 remain Draft and unmerged.

**New authored parameter-expanded tests in this run:** 10 READ + 31 attention = **41**; these are counts of authored tests and must not be reported as locally executed PASS evidence. All green/failure decisions must be tied to exact CI head and job IDs; never substitute older branch results.

## Follow-up

1. Confirm six-job result for corrected Context head and newest READ + proactive source/test head. Resolve any inherited expectations with semantics-preserving tests; do not weaken early safety refusal.
2. Review detached proactive attention result contracts/fixture boundaries against `docs/PROACTIVE_AUTONOMY_CONTRACT.md`; only integrate after exact-head GREEN and scoped permissions, a trusted clock, revocation freshness, local persistence and audited notice-delivery rules exist.
3. Prioritize Planner FAILED/BLOCKED recovery, Registered READ partial-success audit, Memory generation/expiry/COMMIT manual reconciliation and restart-safe Scheduler occurrence/replay protection, without enabling external actions.
