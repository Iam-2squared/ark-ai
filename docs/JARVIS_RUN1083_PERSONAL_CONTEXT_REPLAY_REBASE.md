# Run1083 — Personal Context replay crash and path-admission rebase

## Exact basis
- Parent: Draft PR #8, `research/jarvis-foundations`
- Parent HEAD at branch creation: `916aae6c6578086fee5e83c77c23375712676c90`
- Prior reviewed child: Draft PR #204, `research/run1076-personal-context-replay-rebase`
- Prior child HEAD: `2d7a1bebc63076129714ef45b582c1a03dae7dce`
- Prior exact-head CI: see the exact run returned for that child head in the PR/Actions history; this result does not transfer to this rebase.

## Rebased change
Reapply Personal Context replay-ledger path admission and process-crash recovery coverage:
- Pin the Windows reparse-point attribute mask and reject malformed present metadata, reparse ancestors, database leaves and SQLite sidecars before SQLite access.
- Exercise process exit after native replay-ledger COMMIT but before the reservation receipt returns.
- Stabilize the proactive two-process CAS preparation race with a WAL anchor while leaving production checks unchanged.

The replay ledger remains hash-only and denial-only. No payload storage, live context, disclosure, consent, scheduler dispatch, ToolBackend or external effect is added.

## Scope and limits
- Synthetic disposable SQLite and spawned local processes only.
- This is pathname metadata admission, not atomic directory-handle custody, trusted time, authenticated consent, independent custody, power-loss durability or exactly-once external effects.
- No paid/external compute, Candidate, training, protected V2 evaluation, frozen-contract change, credentials, UI/frontend work or main merge.
- PR #8 remains Draft/unmerged. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required for this rebased child.
