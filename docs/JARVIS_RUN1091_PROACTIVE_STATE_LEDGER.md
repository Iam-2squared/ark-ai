# Run1091 — durable synthetic proactive eligibility state

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `d7de07d4d5d1239d3748b43d590dd102a2547c1c`.
- Child branch: `research/run1091-proactive-state-cas`.
- Source: `src/ark/proactive_state_ledger.py`.
- Tests: `tests/test_proactive_state_ledger_run1091.py` (11 test functions).
- Design basis: `docs/PROACTIVE_SCHEDULER_PROTOTYPE_EVIDENCE_20260929.md`.

## New state foundation

The existing `SyntheticProactiveLedger` persists content-free prepared-trigger deduplication, while the disconnected schedule preview/quarantine bridge handles due-slot preview and expired-slot quarantine. The earlier prototype evidence identified a separate missing piece: restart-safe notification-rate and unchanged-observation state.

This child adds a separate, reversible SQLite state ledger:

- One row per hashed owner/namespace scope and hashed policy revision.
- Exact revision compare-and-swap under `BEGIN IMMEDIATE`; independent store instances cannot both advance the same revision.
- Persisted last observation digest, accepted observation/evaluation times, last eligible-preview time, rolling-window proposal timestamps, decision and a deterministic row checksum.
- `TOO_SOON` does not consume a new observation; `COOLDOWN` and `WINDOW_BUDGET` persist the new digest so an unchanged observation remains suppressed after the cooldown/window boundary.
- Rolling-window timestamps at the exact lower boundary are excluded, freeing a slot deterministically.
- Reopen/read-only recovery returns the current state; stale CAS revisions fail closed. The store never automatically retries an ambiguous write.
- Only digests and bounded time/state metadata are persisted. Raw observation payloads are not accepted by this API.

## Deliberate non-authority

`ELIGIBLE_PREVIEW` means only that the synthetic local rate policy did not suppress this preview. It is **not** a notification, consent, permission, trusted-clock proof, ToolBackend dispatch, automatic replay or external-effect receipt. Every authority property on the result is hard-coded false.

All timestamps are caller-supplied and unauthenticated. Clock-regression checks are local consistency checks only. The row checksum detects accidental mismatch but is not an authenticated MAC, independent witness or protection against an actor able to rewrite and recompute the database. This first version is a mutable CAS projection, not an append-only audit history or power-loss proof.

## Regression coverage

The 11 test functions cover:

1. Initial content-minimized denial-only preview state.
2. `TOO_SOON -> COOLDOWN -> ELIGIBLE_PREVIEW -> WINDOW_BUDGET` and exact rolling-window boundary recovery.
3. Unchanged observation suppression after cooldown.
4. Restart recovery and stale revision rejection.
5. Two independent store instances racing the same CAS revision (one winner).
6. Clock and observation-time regression.
7. Policy-revision isolation and exact integer/digest ingress.
8. Equal-millisecond proposal accounting when intervals are explicitly zero.
9. Schema drift and row-checksum corruption.
10. Read-only reopen refusing to recreate a missing database.
11. Future observation and NUL-bearing policy identity rejection.

No local pytest/Ruff result is claimed. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required after opening the Draft child PR.

## Boundaries

No real timer, notification, proactive action, model call, camera/microphone, live personal data, ToolBackend, credentials, paid API/service, subscription, purchase, GPU/external compute, Candidate, protected V2 evaluation, frozen contract change, or main merge is involved. Existing V1/V2/Local UI/Launcher evidence, Memory/Planner/Tool/Observation contracts, V3 Contract 1 and PR #5's evaluation gate are unchanged. PR #8 remains Draft/unmerged; PR #9 and all UI/frontend work remain paused and untouched. This isolated state package is not integrated into a live scheduler. ARK/JARVIS remains NOT_PASSED.
