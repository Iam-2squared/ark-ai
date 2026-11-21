# Run1071 — Memory SQLite stat-predicate custody

## Exact work basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `5e66b1155ca007f0c479d05d8ef0c445cacb4bcc` (after exact-head-GREEN ToolCall argument-admission and proactive schedule-preview packages were integrated; fresh parent CI is tracked separately).
- Child branch: `research/run1071-memory-stat-predicate-custody`.
- Source commit: `e6e622bf173caa4acc8e45e110799fc8a1a4bc98`.
- Test commit: `155d32b6e4e4161bca0cd34ef5b3445681790702`.

## Change

Memory SQLite path admission now pins the import-original `stat` module and the exact `S_ISDIR`, `S_ISLNK`, `S_ISREG`, and `S_IFMT` predicates it uses for ancestor, database-leaf, and diagnostic checks. A same-process replacement is rejected by the existing path-policy guard before `lstat`, directory creation, or SQLite access. The existing reparse-point attribute and helper identity pins remain intact.

## Regression coverage

Five synthetic cases replace each individual stat predicate and the module binding. Each requires the existing fail-closed `MemorySchemaError` before any filesystem `lstat`. No alias, reparse point, private database, or real Memory content is opened.

## Limits

This is local in-process dependency-identity hardening, not a Python sandbox, atomic directory-handle custody, authenticated storage, protection against a fully compromised interpreter, trusted writer provenance, cross-store atomicity, or power-loss durability. Memory v1 schema/API and event contract are unchanged. No WRITE retry, privacy disclosure, real ToolBackend, Candidate, training, protected evaluation, paid service, external compute, credentials, hardware, UI, or main merge is involved.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.

**ARK/JARVIS remains NOT_PASSED.**
