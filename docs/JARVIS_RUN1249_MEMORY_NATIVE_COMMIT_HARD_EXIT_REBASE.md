# JARVIS Run1249 — Memory row/event native-COMMIT hard-exit regression rebased

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `99654a0ecc75fe53de7f38d92db42095391df6e4`.
- Rebased test-only package from Draft PR #427, source child HEAD `112651a6426c9b477821572d485095885fe73283`.
- Test file carried forward unchanged from the prior exact-head-GREEN child.
- No Memory production source, DDL, public API, schema, or frozen contract changes.

## Regression coverage

- Seed one synthetic private Memory row and its create event.
- A spawned interpreter opens the same local SQLite database and performs a CAS update.
- A connection wrapper delegates native context-manager exit (committing the row/event pair), then terminates with `os._exit` before Python cleanup or the caller receives a MemoryRecord.
- A fresh store instance must recover revision 2, the committed content/metadata, and exactly one create plus one update event.
- Verify global event IDs, SQLite quick-check, exact frozen event-table column shape, and absence of the synthetic private metadata marker from event rows.

## Evidence boundary

The source child CI [45321938271](https://github.com/Iam-2squared/ark-ai/actions/runs/45321938271) was GREEN 6/6 on its older parent. That result does not certify this rebased child. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.

This is synthetic local process-exit evidence after native SQLite COMMIT returns. It is not fsync/power-loss certification, independent storage custody, cross-store atomicity, authenticated provenance, consent, or permission to replay an external effect. No live personal data or external service is used.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, destructive operation, frozen-contract change, UI/frontend work, or main merge. PR #5 and PR #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
