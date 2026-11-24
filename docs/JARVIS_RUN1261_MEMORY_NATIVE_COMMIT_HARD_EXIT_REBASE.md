# JARVIS Run1261 — Memory row/event native-COMMIT hard-exit regression rebased

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `0901cd16ad2f7508cab351175699256ba4abdf83`.
- Rebased test-only package from Draft PR #437, exact source child HEAD `95c8ef36990dcfc1e1d7bff1482f03983ae5075b`.
- Test body carried forward unchanged from the exact-head-GREEN child; no Memory production source, DDL, public API, schema, or frozen contract changes.

## Regression coverage

- Seed one synthetic private Memory row and its create event.
- A spawned interpreter opens the same local SQLite database and performs a CAS update.
- A connection wrapper delegates native context-manager exit (committing the row/event pair), then terminates with `os._exit` before Python cleanup or the caller receives a MemoryRecord.
- A fresh store instance must recover revision 2, the committed content/metadata, and exactly one create plus one update event.
- Verify global event IDs, SQLite quick-check, exact frozen event-table column shape, and absence of the synthetic private metadata marker from event rows.

## Evidence boundary

Source child PR #437 CI [45342870576](https://github.com/Iam-2squared/ark-ai/actions/runs/45342870576) was GREEN 6/6 on parent HEAD `e3448745e237fa320641ad7b38a67098dfd640df`. This new rebase has a different exact parent and requires fresh exact-head Windows/Linux × Python 3.11–3.13 CI; no local pytest/Ruff PASS is claimed.

This is synthetic local process-exit evidence after native SQLite COMMIT returns. It is not fsync/power-loss certification, independent storage custody, cross-store atomicity, authenticated provenance, consent, or permission to replay an external effect. No live personal data or external service is used.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, destructive operation, frozen-contract change, UI/frontend work, or main merge. PR #5 and PR #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
