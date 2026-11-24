# JARVIS Run1242 — Memory row/event recovery after native COMMIT hard exit

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `883006bfdfbd9c9d0408b78d350b767e451d7955`.
- Child branch: `research/run1242-memory-put-native-commit-hard-exit`.
- Test-only production `SQLiteMemoryStore.put` crash regression; no Memory source, DDL or public API changes.

## Regression coverage

- Seed one synthetic private Memory row and its create event.
- A spawned interpreter opens the same local SQLite database and performs a CAS update.
- A connection wrapper delegates the native context-manager exit (thereby committing the row and event), then terminates with `os._exit` before Python cleanup or the caller receives a MemoryRecord.
- A fresh store instance must recover revision 2, the committed content/metadata, and exactly one create plus one update event.
- Verify global event IDs, SQLite quick-check, and that event projections contain only event metadata rather than Memory content/metadata.

## Evidence boundary

This is a synthetic local process-exit test after the native SQLite COMMIT returns. It is not power-loss/fsync certification, independent storage custody, cross-store atomicity, authenticated provenance, consent, or permission to replay an external effect. No live personal data or external service is used.

No production source, Memory v1 DDL/public API, frozen contract, V1/V2 evidence, UI/frontend branch or protected evaluation is changed. No paid/external compute, Candidate generation/promotion, credentials, hardware, destructive operation or main merge is performed. PR #5 and PR #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.
