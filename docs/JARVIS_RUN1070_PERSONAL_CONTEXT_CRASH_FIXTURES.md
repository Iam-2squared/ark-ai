# Run1070 — Personal Context replay crash and proactive race fixture rebase

## Exact work basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `5d9e1dfb37d7ff0769545e790da9d5dfbfeb8c50` (Run1067 checkpoint; parent CI run `44912347493` GREEN, 6/6).
- Original package: Draft PR #192, exact child HEAD `c513e4b68a446ceb59da83a3873acf83288b4361`; exact-head CI run `44909161484` GREEN, 6/6 on older parent `87ee86a333fb851ef21b64ce91e9b15d15e231f6`.
- Rebased child branch: `research/run1070-personal-context-replay-hardening-rebase`.
- Fresh exact-head CI is required; the older green run is not transferred.

## Coverage

- Spawn a disposable process that exits immediately after the replay-ledger native SQLite COMMIT but before the reservation receipt returns.
- Cold recovery verifies one hash-only reservation, stale/duplicate denial, SQLite integrity and absence of fixture payload bytes.
- Stabilize the proactive two-process preparation CAS race by retaining a normal SQLite WAL anchor connection for the duration of child preparation. This avoids transient DELETE-journal sidecar unlink timing; production path checks are not relaxed.
- No production source or schema change is made by these two test fixtures.

## Limits

Synthetic scope/content and disposable local SQLite only. No live personal data, disclosure, consent, scheduler dispatch, ToolBackend or external effect. The crash fixture distinguishes local SQLite COMMIT recovery from receipt acknowledgement; it does not prove power-loss/fsync durability, independent custody, trusted time, authenticated provenance, consent, cross-store atomicity or exactly-once external effects. No paid service, external compute, Candidate, protected V2 evaluation, frozen-contract change, UI work, credentials, physical hardware or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**
