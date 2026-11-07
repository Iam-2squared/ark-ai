# Run546 — Detached terminal caller-epoch custody and SQLite READ recovery snapshot

**Classification:** local-only, disconnected and reversible foundations.
No ToolBackend, live planner dispatch, physical device, user consent, trusted
clock, real action verification, database migration or automatic replay.

## Package A — detached terminal verifier caller epoch

- Source: `7fd69498ba51dc6c106a5f1d9349e48af93729cf`
  (`src/ark/agency/disconnected_batch_terminal_projection.py`).
- Regression tests: `a8b1813d28ed4861231f4a80903bb9d051768620`
  (`tests/test_terminal_verifier_input_epoch_run546.py`), seven new
  parameter-expanded cases.
- Before invoking the potentially reentrant terminal projector, retain the
  *original* receipt field carriers and authority property descriptors.
  Revalidate identity and exact output against independently recomputed
  projected fields immediately after projection, after each denied authority
  getter, and after both plan/schedule verifier callbacks.
- This closes an epoch-rebasing gap: a callback that swaps an equal-valued
  receipt field could otherwise be compared only to its own replacement.
  Receipt authority remains False; projected FAILED/BLOCKED labels remain
  hypothetical, never authenticated real outcomes.

## Package B — bounded digest-only READ Journal recovery

- Source: `70dc3a45bd9d0301067374f70a68f727fcd44347`
  (`src/ark/agency/disconnected_read_journal.py`).
- Regression tests: `281a3780cbda94bb06816859c34dc6140f4c5a51`
  (`tests/test_read_journal_recovery_snapshot_run546.py`), eight new cases.
- Add `ReadJournalSnapshot` and
  `DisconnectedReadJournal.recover_receipts(retained)`. With an independently
  retained count and chain tip, scan marked SQLite state in one read
  transaction, reconstruct bounded digest-only receipts, recompute the
  sequence hash, re-scan the snapshot, and return an exact-type immutable
  view after COMMIT and repeated denied-authority checks.
- This is a **read-only recovery input** for later Planner/READ integration,
  not cross-store atomicity, receipt custody independent of local SQLite,
  a claim that the fixture READ executed, a live retry instruction, or proof
  of a ToolRegistry/PermissionGate grant.
- No schema changes, write replay, external result contents, secret paths,
  automatic rollback assertion after COMMIT, or deletion were introduced.

## Evidence and gating

The inherited PR #8 HEAD
`8253c5e9d04ca53fdef84f39cb51ab60de8345ca`
has exact-HEAD 6/6 GREEN run
[41380570427](https://github.com/Iam-2squared/ark-ai/actions/runs/41380570427).
At documentation preparation, terminal test CI
[41385011681](https://github.com/Iam-2squared/ark-ai/actions/runs/41385011681)
and READ snapshot CI
[41385466048](https://github.com/Iam-2squared/ark-ai/actions/runs/41385466048)
were still in progress. Do **not** promote either latest source or this
document to GREEN until the exact commit's six jobs finish successfully.
The 15 new cases are authored, **not** independent local pytest PASS.
Frozen Memory/Planner/V3 contracts and main remain unchanged.

## Next plan / 今後の方針

1. Resolve exact-head CI failures if any, without loosening denials.
2. Only after matching GREEN, connect digest-only READ recovery to stable
   Planner FAILED/BLOCKED evidence and registry-bound request identity.
3. Continue COMMIT-UNKNOWN manual reconciliation, occurrence fencing,
   trusted-clock audit and private retention controls on independent lanes.
