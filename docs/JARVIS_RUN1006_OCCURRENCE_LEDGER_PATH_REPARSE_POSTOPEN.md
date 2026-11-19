# Run1006 — durable occurrence fixture path reparse and post-open checks

**Work basis:** Draft PR #14 exact head `00fee30e4004a56bb73d7161070c6a31661bc9e3`; its exact-head CI was observed GREEN 6/6 before this child was created. This isolated child does not modify PR #14 or PR #8.

## Gap

The synthetic occurrence ledger rejected POSIX symbolic links, non-regular files and unsafe SQLite sidecars before opening. It did not inspect Windows reparse-point metadata. Its read/write connector and read-only count path also lacked a post-open pathname recheck before returning the handle to transaction/query code.

## Change

- Pin the platform `FILE_ATTRIBUTE_REPARSE_POINT` bit and exact local predicate as part of the fixture protocol.
- Reject reparse-point ancestors, main database and SQLite sidecars before opening.
- Recheck the same pinned path immediately after read/write and read-only SQLite opens; close the handle on rejection.
- Route the read-only count through the checked connector and revalidate source object identity after open.
- Preserve the existing reservation table, digest fields, replay checks and non-authorizing receipt semantics.

## Regression coverage

Seven synthetic cases cover ancestor/main/sidecar reparse rejection before SQLite open, exact attribute typing, post-open write/read rejection with closed-handle verification, and create-enabled constructor post-open rejection. Only disposable local SQLite and synthetic filesystem metadata are used.

## Limits and safety

The ledger remains a disconnected synthetic fixture, not a production PermissionGate, trusted approval issuer, trusted clock, authenticated storage or proof of external exactly-once effects. Repeated `lstat()` checks do not provide atomic dirfd custody or eliminate TOCTOU. No backend is dispatched and no real WRITE, consent, paid service, external compute, credential, Candidate, V2 opening, frozen-contract change, UI work or main merge is authorized.

**Exact-head CI is pending for this child. No PASS is claimed. Overall ARK/JARVIS remains NOT_PASSED.**
