# JARVIS Run1244 — Memory row/event native-COMMIT hard-exit regression rebased

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `609a3cdaf7ad3b08ef90f2398378d9984bdc329d`.
- Rebased from Draft PR #425 child branch `research/run1242-memory-put-native-commit-hard-exit`, exact child HEAD `ce811baf91c0ca8d16ea33e65a06f94dbdaa02db`.
- Test-only production `SQLiteMemoryStore.put` regression; no Memory source, DDL, public API or frozen contract changes.
- The rebased test adds an explicit assertion that the frozen `memory_events` table contains only event identity/scope/operation/revision/time fields and does not persist the synthetic private content/metadata payload.

## Regression coverage

- Seed one synthetic private Memory row and its create event.
- A spawned interpreter opens the same local SQLite database and performs a CAS update.
- A connection wrapper delegates native context-manager exit (committing the row/event pair), then terminates with `os._exit` before Python cleanup or the caller receives a MemoryRecord.
- A fresh store instance must recover revision 2, the committed content/metadata, and exactly one create plus one update event.
- Verify global event IDs, SQLite quick-check, exact event-table column shape, and absence of the synthetic private metadata marker from event rows.

## Evidence boundary

This is a synthetic local process-exit test after the native SQLite COMMIT returns. It is not power-loss/fsync certification, independent storage custody, cross-store atomicity, authenticated provenance, consent, or permission to replay an external effect. No live personal data or external service is used.

No production source, Memory v1 DDL/public API, frozen contract, V1/V2 evidence, UI/frontend branch or protected evaluation is changed. No paid/external compute, Candidate generation/promotion, credentials, hardware, destructive operation or main merge is performed. PR #5 and PR #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.

Previous child CI [45315603299](https://github.com/Iam-2squared/ark-ai/actions/runs/45315603299) was GREEN 6/6 on the older parent and original test; it does not certify this rebased, strengthened test. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.
