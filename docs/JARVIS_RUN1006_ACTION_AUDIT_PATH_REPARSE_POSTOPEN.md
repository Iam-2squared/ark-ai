# Run1006 — Action Audit reparse-point and post-open path admission

**Work basis:** Draft PR #13 exact head `b940525c43d3e3a858352c8702dc4202598597e3`; its exact-head CI was observed GREEN 6/6 before this child was created. This isolated child does not modify PR #13 or PR #8.

## Gap

Action Audit had repeated local `lstat()` checks for symbolic links, regular files and SQLite sidecars, but did not explicitly reject Windows reparse points. Its read/write and read-only connection helpers also returned newly opened SQLite handles without rechecking the path before row-factory setup or PRAGMA access.

## Change

- Pin the platform `FILE_ATTRIBUTE_REPARSE_POINT` bit and the exact local reparse predicate.
- Reject reparse-point ancestors, the main database and SQLite sidecars while preserving existing link-count, file-type and byte-budget checks.
- Recheck path admission immediately after read/write and read-only SQLite opens, before any PRAGMA or audit query.
- Close the opened handle before propagating any failed post-open check.
- Preserve Action Audit v1 DDL, event sequence, outcome bounds and digest-only storage.

## Regression coverage

Seven synthetic cases cover ancestor/main/sidecar reparse rejection before SQLite open, exact attribute typing, read/write and read-only post-open rejection with closed-handle verification, and constructor bootstrap post-open rejection. No private audit history or real action is used.

## Limits and safety

This is best-effort local path admission, not descriptor identity verification, atomic dirfd custody, authenticated audit provenance or TOCTOU protection. It does not prove trusted time, cross-store atomicity, consent, exactly-once external effects or real backend safety. No real ToolBackend, payment, paid service, external compute, credential, Candidate, protected V2 evaluation, frozen-contract change, UI work or main merge is involved.

**Exact-head CI is pending for this child. No PASS is claimed. Overall ARK/JARVIS remains NOT_PASSED.**
