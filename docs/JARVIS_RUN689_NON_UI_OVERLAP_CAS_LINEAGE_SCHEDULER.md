# Run689 — Parallel RUNNING, Dual CAS, Bounded Lineage and Independent Quarantine

**Work basis:** Run688 canonical checkpoint-result `32f3f706000592f8626f4b4fc9fa88d40794143f`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), `research/jarvis-foundations`. **Current package-complete source/test HEAD before this report:** `45928b30f295f249ebc160bf0b4a139d0a0ca8d0`. Changes consist only of four new non-UI, mock/disconnected test files; 21 parametrized regression cases. No production source, frozen contract, UI/frontend, candidate, model, real action, paid compute or main merge.

## A. Planner concurrent RUNNING independence (4 cases)

`tests/test_planner_overlapping_running_disjoint_restart_run689.py` at `27063120ac555cdc89f6a4e5f6b80a494b239303` interleaves RUNNING transitions for two disjoint roots in one SQLite plan journal. Terminating the root of a diamond with FAILED or CANCELLED must block only its dependent descendants, leave the other root RUNNING and ambiguous across a cold reopen, reject redundant RUNNING, and permit an **explicit** terminal transition for that independent root. The test keeps `dispatch_authorized` and `automatic_replay_authorized` false. This is not permission to resolve or retry an ambiguous external WRITE.

## B. Concurrent scopes, independent Memory CAS (6 cases)

`tests/test_memory_disjoint_dual_generation_cas_run689.py` at `3b5ec1eda414fcae40d9ce03ddfca77e4330c604` retains tokens for two distinct source IDs across identical scope, different namespace and different owner cases. Both update orders are exercised through separate SQLiteMemoryStore handles. The test verifies each row's revision, unchanged create-event identity, advanced event-prefix digest and refusal to reapply an already-consumed token. No caller authenticity, consent, retention policy, cross-store transaction or whole-system erasure is inferred from these local CAS reviews.

## C. Observation lineage maximum boundary (8 cases)

`tests/test_observation_closed_chain_budget_boundary_run689.py` at `bb49765c3fdfba56d5b92513e360bb123dee9c70` reviews fixed synthetic linear envelope chains of 1, 16, 64 and 256 records. It asserts digest-only deterministic outcome and no source/consent/dispatch authority. A 257-record chain is out of budget; invalid parent links at the head, center and tail of a 256-record chain must fail closed. These are local, fabricated envelopes, not audio/video capture, provenance authentication or independently retained chain evidence.

## D. Trigger-specific quarantine recovery (3 cases)

`tests/test_proactive_independent_quarantine_restart_run689.py` at `45928b30f295f249ebc160bf0b4a139d0a0ca8d0` keeps two independently identified local schedules in separate SQLite quarantine ledgers. After one trigger quarantines its first expired occurrence, a restart must preserve its advanced cursor while the second trigger retains the original cursor and expired preview. All preview outputs deny notification, tool execution, trusted clock and automatic replay. No real scheduler side effect is enabled.

## CI and gated completion

- Incoming Run688 exact-HEAD [CI #42383639432](https://github.com/Iam-2squared/ark-ai/actions/runs/42383639432): Windows/Ubuntu × Python 3.11–3.13, **6/6 GREEN**.
- Run689 A [CI #42388341258](https://github.com/Iam-2squared/ark-ai/actions/runs/42388341258), B [CI #42388374783](https://github.com/Iam-2squared/ark-ai/actions/runs/42388374783), C [CI #42388401301](https://github.com/Iam-2squared/ark-ai/actions/runs/42388401301) and D [CI #42388600608](https://github.com/Iam-2squared/ark-ai/actions/runs/42388600608) were automatic PR-triggered, **IN PROGRESS / QUEUED at first sampling**. New exact-HEAD 6/6 GREEN and all 21 cases across platforms are **not** asserted without subsequent verification.
- No manual equivalent workflow was triggered. If an exact failure appears, inspect the failed-job log and change only the faulty source/test via the normal GitHub Contents path, then continue independent work while CI runs.

## Authorization and frozen state

V1/V2/Local UI/Launcher contracts/evidence remain frozen. Protected V2 final evaluation remains unopened. [V3 PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) remains Draft/unmerged with immutable model/runtime/hash, data rights/provenance, GPU/budget and distinct explicit preflight/full authorization prerequisites unresolved. [UI PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) remains Draft/unmerged and completely untouched. PR #8 remains Draft/unmerged; main unchanged.

No paid service/API, external GPU, weights/Candidate work, credentials, physical-PC action, real tool dispatch, destructive change, protected evaluation or merge. All findings are conditional on exact-HEAD tests. Overall ARK/JARVIS/V3 **NOT_PASSED**. Local synthetic identity/digests are not independent writer authentication, human review, trusted-clock evidence, cross-store atomicity or global exactly-once external effects. **COMMIT-UNKNOWN => NO AUTOMATIC WRITE REPLAY.**

## Next plan / 今後の方針

1. Resolve complete six-job platform evidence for the actual Run689 checkpoint-result HEAD. Diagnose and correct genuine CI failures through the normal GitHub Contents write path without changing frozen boundaries.
2. Deepen step-specific Planner READ correlation and audit-before-action joins after relevant exact-head GREEN; maintain UNKNOWN WRITE quarantine.
3. Extend Memory scope/expiry ABA, coherent WAL snapshot and privacy veto coverage under true independent actors with content-free evidence.
4. Continue disconnected startup, proactive and observation backend contract work; do not resume UI, protected evaluation, paid compute or candidate work without required explicit approval.
