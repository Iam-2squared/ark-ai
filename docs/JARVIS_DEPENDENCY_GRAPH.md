# ARK JARVIS Dependency Graph

This graph is a working dependency map for continuous ARK development. Roadmap version labels are evidence and compatibility boundaries, not execution stop points.

## Current safe work graph

```text
frozen V1/V2/Local UI/Launcher ───────────────┐
                                               │ unchanged compatibility baseline
V3 frozen contract ──> resource/export guards ┤
                                               │
planner contracts ──> immutable plan state ───┤
                                               ├─> local orchestration integration
memory contracts ──> persisted integrity ──> personal-context retrieval
                     │                         │
                     └─> retention/deletion ───┘

tool contracts ──> durable one-shot ledger ────┐
action audit ────> schema/integrity hardening ├─> trusted-clock ActionExecutor
                                               └─> mock backend integration tests

trusted ActionExecutor + personal context + planner
    └─> later local UI / voice / vision / computer-action adapters
```

## Execution order when all paths are actionable

1. Keep the exact-head CI baseline green before stacking broader foundation changes.
2. Harden planner views and exact transition types.
3. Harden persisted memory integrity, schema validation, concurrency, retention, and physical deletion.
4. Add restart-safe one-shot authorization storage and harden action-audit persistence.
5. Connect a trusted-clock, audit-before-action executor to mock backends only.
6. Build owner/namespace-isolated personal-context retrieval on validated memory records.
7. Advance V3 resource/evidence and export-path guards independently without training, Candidate generation, or protected evaluation.
8. Only after the above foundations are stable, connect local UI/voice/vision/computer-control adapters behind the same permission and audit boundaries.

## Parallelism

Planner, memory, durable authorization/audit, personal-context contracts, and V3 reproducibility guards are independent enough to progress in parallel. CI wait time should be used for any unblocked sibling node. Real action adapters depend on durable authorization plus fail-closed audit. Personal-context integration depends on memory integrity. Training results are not a dependency for any of these foundations.

## Hard boundaries

The graph does not authorize paid/external compute, real Candidate generation, protected/frozen V2 evaluation opening, Candidate promotion, frozen-contract changes, destructive actions, credentials not already authorized, or main merge. Reaching one of those boundaries blocks only that path; safe sibling paths continue.
