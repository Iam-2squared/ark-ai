# Run1065 — Personal Context replay crash and proactive race fixtures

- Target: Draft PR #8, `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `87ee86a333fb851ef21b64ce91e9b15d15e231f6` (Run1062 foundation; exact-head CI run `44905799382` was GREEN).
- Child branch: `research/run1065-personal-context-crash-fixtures`.
- Test-only rebase of the prior Run1062 Personal Context recovery/race package onto the current foundation.

## Coverage

- Spawn a disposable process that exits immediately after the replay-ledger native SQLite COMMIT but before the reservation receipt returns.
- Cold recovery verifies one hash-only reservation, stale/duplicate denial, SQLite integrity and absence of fixture payload bytes.
- Stabilize the proactive two-process preparation CAS race by retaining a normal SQLite WAL anchor connection for the duration of child preparation. This avoids transient DELETE-journal sidecar unlink timing; production path checks are not relaxed.
- No production source or schema change.

## Evidence and limits

Synthetic scope/content and disposable local SQLite only. No live personal data, disclosure, consent, scheduler dispatch, ToolBackend or external effect. Fresh exact-head CI is required on this rebase; no local pytest/Ruff PASS is claimed. The prior branch's green run on a diverged parent is historical only and does not transfer.

The crash fixture distinguishes local SQLite COMMIT recovery from receipt acknowledgement; it does not prove power-loss/fsync durability, independent custody, trusted time, authenticated provenance, consent, cross-store atomicity or exactly-once external effects. No paid service, external compute, Candidate, protected V2 evaluation, frozen-contract change, UI work, credentials, physical hardware or main merge is involved. PR #8 remains Draft/unmerged.
