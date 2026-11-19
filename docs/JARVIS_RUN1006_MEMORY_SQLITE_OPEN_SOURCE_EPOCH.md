# Run1006 — Memory SQLite open source-epoch pin

**Work basis:** Draft PR #37 exact head `712e295d490af74e6725aad99dee64359d9cda47`; exact-head CI #44622976063 was observed GREEN 6/6. This isolated child does not modify PR #37 or its parents.

## Gap

Memory's read/write and read-only connectors already rechecked filesystem path admission after SQLite returned a connection and closed the handle when that check failed. However, they read `self.path` again for the post-open check. A reentrant `sqlite3.connect` wrapper or callback could replace `self.path` after the original database was opened. The second check could then validate a different, safe path while the returned handle still referenced the original path.

## Change

- Snapshot the exact `Path` object before preflight and SQLite open.
- Use that same object for the URI, post-open filesystem recheck and source-identity comparison.
- Reject any equal-valued or different-valued `self.path` replacement during the open boundary.
- Close the just-opened connection before propagating the source-epoch failure.
- Preserve Memory v1 DDL, public API, CAS/event behavior, expiry semantics and the existing reparse-point checks.

## Regression coverage

Four synthetic cases cover both read/write and read-only open paths, crossed with equal-valued replacement Path objects and replacement paths pointing to a different existing database. The test changes the store's path only after a disposable SQLite handle opens, requires rejection and verifies that the original handle is closed.

## Limits and safety

This is an in-process source-epoch consistency check, not a security sandbox, authenticated filesystem custody, atomic dirfd identity or TOCTOU protection. It uses only synthetic local SQLite fixtures. No private Memory data, real backend, consent, trusted clock, external compute, paid service, credentials, Candidate, V2 opening, frozen-contract change, UI work or main merge is involved.

**Exact-head CI is pending for this child. No PASS is claimed. Overall ARK/JARVIS remains NOT_PASSED.**
