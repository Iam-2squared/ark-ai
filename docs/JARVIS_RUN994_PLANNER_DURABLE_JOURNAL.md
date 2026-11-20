# Run994 — Durable Planner journal and fail-closed recovery

## Scope and basis

- Repository: Iam-2squared/ark-ai
- Isolated branch: research/planner-durable-journal-run994
- Exact base: Draft PR #8 checkpoint head 326001af654078227641546a8f30c6954fcea4a3
- Module: src/ark/agency/planner_journal.py
- Regression suite: tests/test_planner_journal_run994.py
- No existing Planner, ToolRegistry, PermissionGate, Action Audit, frozen contract or UI source is modified.

## Durable state model

The journal stores a bounded append-only event stream in a separate local SQLite database:

- one genesis row binds plan ID, canonical PlanGraph topology digest and initial all-PENDING status digest;
- each transition row binds sequence, step ID, from/to state, expected step revision, resulting full status digest, previous hash and event hash;
- one metadata frontier is advanced with a sequence/hash compare-and-swap in the same SQLite transaction as the event insert;
- bootstrap is serialized by BEGIN IMMEDIATE, schema version is checked, and the exact managed table definitions are verified before use;
- persisted rows are type/domain checked and the entire retained prefix is replayed through the existing PlanGraph transition policy before recovery or another append.

No timestamp, raw ToolCall arguments, tool result or backend output is stored. The topology digest binds request identities and dependency edges without serializing raw arguments.

## Transition and recovery semantics

PlannerJournal.transition() does not mutate the caller's graph. It replays the durable prefix into a new PlanGraph, verifies the supplied graph is current, applies exactly one existing PlanGraph transition, and commits the event plus metadata frontier atomically. It returns the new graph and a receipt; the caller must replace its old graph with that returned graph.

A stale graph, stale expected sequence, stale step revision, invalid transition, malformed schema or broken hash/replay prefix fails closed. A COMMIT exception is surfaced as PlannerJournalCommitUnknown. The caller must recover the durable frontier and must not blindly retry the transition.

Recovery preserves RUNNING states and reports their sorted IDs in ambiguous_running_step_ids. A RUNNING step may represent an external operation whose outcome is unknown; it is never reset to PENDING, automatically replayed or treated as completed. The journal itself has no execution or dispatch API.

## Regression coverage authored

Eleven synthetic tests cover:

1. Content-minimized genesis and cold recovery.
2. Durable transition replay and terminal descendant BLOCKED propagation.
3. RUNNING recovery quarantine without automatic replay.
4. Stale graph and stale sequence rejection.
5. Invalid transition rejection without an event append.
6. Two independent SQLite connections racing the same sequence, with exactly one append.
7. Event hash tampering detection.
8. Wrong topology rejection.
9. Unexpected schema-object rejection.
10. Invalid plan identity rejection before database access.
11. Non-genesis graph rejection and missing-plan recovery behavior.

All fixtures use synthetic plan/tool identities and disposable local SQLite files. Exact-head CI is required before treating the tests or implementation as validated.

## Limits and safety

The hash chain detects accidental or local row mutation when the retained metadata frontier remains trustworthy. It is not an authenticated event chain, independent custody, anti-rollback witness or protection against a local attacker who can rewrite the entire database. SQLite durability depends on the host filesystem and storage stack.

This journal does not establish trusted time, authenticated user consent, durable one-shot authorization, exactly-once external effects, cross-store atomicity, tool dispatch or real crash outcome attribution. The caller-supplied PlanGraph is only a local input snapshot. Recovered RUNNING steps remain ambiguous and require explicit future policy; no automatic retry is allowed.

No paid service, external compute, Candidate generation/promotion, protected V2 evaluation, credential/account connection, physical hardware action, real ToolBackend, frozen-contract change, main merge or UI/frontend work is included. PR #5 remains gated Draft/unmerged; PR #9 remains paused and untouched. Overall ARK/JARVIS remains NOT_PASSED.


## Run1030 rebase onto current foundations

- New exact work basis: Draft PR #8 branch `research/jarvis-foundations`, HEAD `b585c61a6e3ca1a9f456175b2a96053a908a500c`.
- Re-applies the durable append-only Planner journal and deterministic recovery implementation on the current foundation head; no existing PlanGraph or frozen contract source is modified.
- Historical PR #18 head `976aea9d1b5573045ebc18045b3b2ce9d879b9c2` passed CI #44538278870 (6/6); that result is not transferred.
- Fresh exact-head CI is required. Recovered RUNNING remains ambiguous and never automatically replays.
