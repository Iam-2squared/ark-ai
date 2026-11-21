# Run1076 — Personal Context replay hardening rebase

## Exact basis

- Original reviewed child: Draft PR #201, `research/run1073-personal-context-replay-hardening-rebase`, exact child HEAD `b390d1939a1f17db9be9d29e5bdd483c757a4517`.
- Original parent at review: `2e408656ae0661626e6bc3fb234006819ef2ccfc`.
- Rebase parent: Draft PR #8, `research/jarvis-foundations`, exact HEAD `663112db8eed74148daedc6dd78e217302c82b15`.
- Rebase branch: `research/run1076-personal-context-replay-rebase`.

## Change

Reapplies the disconnected Personal Context replay path-admission and crash/race fixtures to the latest foundation. The production change pins the Windows reparse-point attribute mask and rejects malformed present metadata, reparse ancestors, database leaves, and SQLite sidecars before SQLite access. The test package includes process exit after native replay-ledger COMMIT and a WAL-anchored proactive cross-process CAS race fixture.

The replay ledger remains hash-only and denial-only. No payload storage, disclosure, consent, scheduler dispatch, ToolBackend, or external effect is added.

## Evidence

Original exact child-head CI run `44926559382` completed GREEN 6/6, but that result is not transferred to this rebase. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.

## Limits

This is pathname metadata admission and synthetic disposable SQLite testing, not atomic directory-handle custody, trusted time, authenticated consent, independent custody, power-loss durability, or exactly-once external effects. No live personal data, paid service, external compute, Candidate, protected V2 evaluation, frozen-contract change, UI, credentials, physical hardware, or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**
