# Run1073 — Personal Context replay hardening rebase

## Exact work basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `2e408656ae0661626e6bc3fb234006819ef2ccfc` (after Run1071 Memory stat-predicate custody integration).
- Previous isolated package: Draft PR #198, child HEAD `d6b7994ba682a446d07090011c76fba9867d8226`, whose exact-head CI run `44920870108` was GREEN 6/6 on its older parent.
- New rebased child branch: `research/run1073-personal-context-replay-hardening-rebase`.

## Reapplied changes

- Pin the import-time Windows `FILE_ATTRIBUTE_REPARSE_POINT` mask in the disconnected Personal Context replay ledger.
- Reject changed path policy and malformed present `st_file_attributes` before filesystem inspection.
- Reject reparse-point ancestors, database leaves and SQLite sidecars before SQLite access.
- Add a spawned-process crash fixture that exits immediately after native SQLite COMMIT but before the reservation receipt returns; cold readback verifies one hash-only reservation, stale/duplicate denial, SQLite integrity and no synthetic payload bytes in the ledger.
- Stabilize the inherited proactive two-process preparation race by retaining a normal SQLite WAL anchor while child preparations run; production path checks remain unchanged.

## Validation and limits

This is a fresh rebase onto the exact parent above. The previous PR #198 GREEN run does not certify this branch. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.

Synthetic fixture values, spawned local processes and disposable SQLite only. No live personal data, disclosure, consent, scheduler dispatch, ToolBackend, external effect, trusted time, independent custody, power-loss/fsync guarantee, cross-store atomicity or exactly-once external effect is established. No schema/frozen-contract change, paid service, external compute, Candidate, protected V2 evaluation, UI work, credentials, physical hardware or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**
