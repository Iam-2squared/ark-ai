# Run1443 — Action Audit process-level first-open

**Scope:** test-only child PR. No Action Audit production code, schema, outcome
vocabulary, frozen contract, or executor integration is changed.

## Coverage added

Two spawned processes begin Action Audit construction at the same release
barrier against one absent database. Each then appends a distinct synthetic
ToolCall. A cold third instance must observe one valid schema and a dense,
chronological two-event sequence with IDs 1 and 2.

The unique marker values exist only inside ToolCall arguments. The persisted
audit stores their digests, not the raw marker text. The test also verifies the
supported schema version and SQLite quick_check after both processes exit.

## Evidence boundary

This is process-level local SQLite WAL/bootstrap and append-sequence evidence.
It does not prove trusted time, external action provenance, independent audit
custody, power-loss durability, cross-store atomicity, or real backend dispatch.

**Work basis:** parent Draft PR #8 branch research/jarvis-foundations at
963e8e67c63b36a376208d29efe06e23cb87be7b.

**Validation:** exact-head CI is pending until this child PR is opened.
