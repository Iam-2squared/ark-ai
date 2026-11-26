# ARK AI — Run621 / Four non-UI constructor-custody work packages

> **Saved source and tests; exact latest-head 6/6 CI GREEN NOT YET VERIFIED.** This is entirely local/disconnected safety work, not JARVIS completion, human permission, authenticated storage, trusted time or backend dispatch.

## Basis / scope

- Invocation work-basis HEAD: `26edea8071eaaabcf618d030b8d5171711f7d363` (Run620 technical-report HEAD), Draft PR #8, `research/jarvis-foundations`.
- Run620 reported four earlier source/test packages, but did not create a Run620 checkpoint. The authoritative status at start was still Run619. Starting Run620 exact-report CI [#41951692763](https://github.com/Iam-2squared/ark-ai/actions/runs/41951692763) **FAILED six jobs**: 2 legacy nested WRITE triage assertions expected `descriptor changed` while the existing safety wrapper actually raised `local WRITE recovery validation denied` (Ubuntu 3.12: 8,645 PASS, 1 SKIP, 2 FAIL). This invocation repaired the test-only expectation without changing the refusal or executing counterfeit constructors.
- Current implementation remains in Draft PR #8; PR #5 and #9 remain Draft/unmerged. No frontend/UI, main, frozen contracts, protected evaluations or actual external effects changed.

## Package 1 — Memory generation-CAS token constructor

- `src/ark/memory/generation_fenced_cas.py`: pin import-original `MemoryGenerationCASToken.__init__` in the existing denial-only check. Compute event and row digests first; recheck constructor immediately before and after witness construction, including reentrant digest callbacks, while preserving the original SQLite transaction and CAS semantics.
- `tests/test_memory_generation_constructor_custody_run621.py`: **5 authored parameter-expanded cases**: two preinstalled initializer attacks (observe/update), two reentrant digest-time attacks (observe/update), one valid CAS/denial check.
- Scope is only local row/event continuity; an ambiguous COMMIT still requires human investigation and must never trigger automatic retry.

## Package 2 — Personal Context read-only replay recovery

- `src/ark/personal_context_replay_recovery.py`: pin import-original `OfflineContextRecoveryReview` and its initializer in both pre-read admission and post-observer/digest validation. Forged constructors never execute.
- `tests/test_context_replay_constructor_custody_run621.py`: **5 authored cases** (class or initializer preinstalled, two reentrant read variants, one normal non-authorizing result).
- Legacy post-final-read tests (five parameter-expanded cases) now observe the authentic in-flight result via a passive test-only frame hook, rather than replacing the protected result constructor. An additional old test injects a real SQLite append during comparison hashing instead of by installing a counterfeit constructor, retaining durable-tip regression coverage.
- Read-only witness agreement never proves consent, revocation freshness, independent custody, permitted disclosure or safe replay.

## Package 3 — Proactive schedule restart

- `src/ark/offline_schedule_resume_review.py`: pin original `OfflineScheduleResumeReview.__init__`, before all ledger reads and again immediately before/after construction. Statically inspect protected denial descriptors with `vars(...).get`, not dynamic `getattr` that could execute malicious `__get__`.
- `tests/test_schedule_resume_constructor_static_denials_run621.py`: **5 authored cases** (preinstalled forged constructor or hostile descriptor, two reentrant substitutions from ledger/preview callbacks, one original denial-only review).
- One earlier test accepts the stricter early descriptor rejection, rather than assuming a forged `False` getter is invoked after object construction. No real timer, notification, scheduler dispatch or trusted-clock provenance was introduced.

## Package 4 — Action Audit append/read receipt constructor

- `src/ark/agency/audit.py`: pin original `ActionAuditEvent.__init__` on append/read ingress, immediately around SQL INSERT/COMMIT and read hydration, and before/after event construction. Verify returned read-event field identities. Existing audit schema is unchanged and event records still contain only action identity digests, not raw arguments.
- `tests/test_action_audit_constructor_custody_run621.py`: **5 authored cases** (2 preinstalled append/read, clock-time reentrant substitution, read-schema-callback substitution, 1 normal no-content audit).
- Even a committed local audit event does not prove trusted time, actor/consent identity, successful external execution or externally exactly-once effects. A post-COMMIT error must never be treated as proof of rollback.

## CI and limitations

- **20 new parameter-expanded tests AUTHORED (5+5+5+5); not a local PASS count.** Nine preexisting parameter-expanded expectations/fixture paths were repaired without weakening safety: 5 context late-read, 1 context late durable append, 2 Run620 WRITE triage, 1 proactive earlier rejection.
- Run620 starting exact-report CI [#41951692763](https://github.com/Iam-2squared/ark-ai/actions/runs/41951692763): **FAIL six** from the 2 old triage cases, repaired on this branch. A Run621 intermediate CI [#41952958540](https://github.com/Iam-2squared/ark-ai/actions/runs/41952958540) showed the same 2 failures plus original context test fixture failures (now addressed). Those intermediate failures cannot be counted as green or final-head evidence.
- Newer independent source/test CI has started automatically; e.g. [#41953291362](https://github.com/Iam-2squared/ark-ai/actions/runs/41953291362) was IN PROGRESS, and [#41954023862](https://github.com/Iam-2squared/ark-ai/actions/runs/41954023862) was QUEUED when last checked. **Latest combined source/test/report/checkpoint HEAD all-six GREEN is NOT established.** No duplicate manual workflow dispatch.
- The local container could not clone from `github.com` (DNS) in prior sessions. No successful local pytest, Ruff, physical Windows/CPU/GGUF benchmark or human review is claimed. On an actual CI FAIL, inspect jobs/logs and perform only the minimal safety-preserving repair.
- V3 PR #5 still requires an immutable HF revision, locally materialized base/tokenizer hashes, approved 120/30 dataset provenance and contamination decisions, exact runtime/export identities, permitted device and separately authorized cost/timeout/preflight gate. This invocation only read `docs/v3/PRE_PAID_COMPUTE_GATE.md` and `HF_IDENTITY_REVIEW.md`; no protected training/validation action.

## Next plan / 今後の方針

1. Check exact final source/test/report/checkpoint SHA against all six Ubuntu/Windows Python 3.11–3.13 CI jobs; on FAIL, use real logs and the normal guarded GitHub Contents path for the smallest fix. Do not claim a PASS early.
2. Strengthen the independent retained Memory event-prefix/CAS/COMMIT-UNKNOWN manual investigation boundary, then Planner journal crash recovery and immutable Registry-bound, exact-type PermissionGate.
3. Integrate only disconnected audit-before-*mock*-action, durable occurrence fencing and restart-safe local permission evidence once lower-level exact-head GREEN is confirmed. No real ToolBackend or automatic UNKNOWN WRITE replay.
4. Progress privacy-safe Personal Context, observation and proactive backend fixtures; keep frozen UI paused and free-only V3 guards isolated.

**Hard stops:** no paid/external GPUs/APIs, Candidate/adapter/weights, private disclosure, live notification/tool action, unreviewed credentials or connections, physical-PC claim, irreversible mutation, V2 protected evaluation opening, Candidate promotion, contract changes or main merge. **ARK/JARVIS/V3 NOT_PASSED.**
