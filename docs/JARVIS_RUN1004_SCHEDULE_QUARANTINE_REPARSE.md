# Run1004 — schedule quarantine SQLite reparse-point path admission

**Work basis:** Draft PR #8 exact head `9539341e9351493458e3ba378ee0b829c5214dc4`. The parent branch's Memory WAL cleanup CI run #44612111623 was in progress when this child was prepared. This isolated scheduler child does not modify the parent branch or its Memory test path.

## Gap

The schedule quarantine ledger's SQLite path admission used no-follow `lstat()` and rejected POSIX symlinks, hardlinked database files and unsafe sidecars. A Windows directory junction is a reparse point but may still report a directory mode and `S_ISLNK=False`; the same gap applies to reparse-point main database or sidecar entries.

## Change

- Pin the platform reparse-point attribute bit as part of the local path-admission protocol.
- Reject reparse-point ancestors, the main SQLite file and `-wal`/`-shm`/`-journal` sidecars before opening SQLite.
- Preserve existing absolute-path, byte-budget, regular-file, link-count, schema and chain checks.

## Regression coverage

Three synthetic `lstat()` results set `FILE_ATTRIBUTE_REPARSE_POINT` while retaining normal directory/file mode bits. The tests cover an ancestor, the main database and a SQLite sidecar. No privileged Windows junction is created and no real schedule is executed.

## Limits and safety

This is best-effort local path admission, not atomic directory-handle custody or protection from hostile concurrent filesystem replacement. Quarantine remains a synthetic overdue classification only; it never authorizes execution, notification, consent, replay or trusted time. No OS clock, timer, model, external service, paid compute, credential, frozen contract, V2 opening, Candidate, UI branch or main branch is touched.

**Exact-head CI is pending until this child PR is opened; no PASS is claimed. PR #8 remains Draft/unmerged. Overall ARK/JARVIS remains NOT_PASSED.**
