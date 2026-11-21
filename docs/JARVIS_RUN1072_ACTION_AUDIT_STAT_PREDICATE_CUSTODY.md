# Run1072 — ActionAudit stat-predicate custody

## Exact work basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `5e66b1155ca007f0c479d05d8ef0c445cacb4bcc`.
- Child branch: `research/run1072-action-audit-stat-predicate-custody`.
- Source commit: `a6a5816e0fce85424c11925cae391dbd7cee7d01`.
- Test commit: `f80c37ea113a55abecee74b2a6a85d92b6542357`.

## Change

ActionAudit now pins the import-original `stat` module and the exact `S_ISDIR`, `S_ISLNK`, `S_ISREG`, and `S_IFMT` functions used by its SQLite path admission and bounded diagnostics. A same-process replacement is refused by the existing reparse-policy guard before `lstat`, parent creation, or SQLite access. The reparse attribute mask, path rules, ActionAudit v1 schema and event contract are unchanged.

## Regression coverage

Five synthetic cases replace each stat predicate and the module binding. Each requires the fixed fail-closed policy diagnostic before filesystem inspection. No privileged junction, audit database, live request, or external effect is used.

## Limits

This is local in-process dependency-identity hardening, not a Python sandbox, atomic directory-handle custody, authenticated audit history, trusted clock, consent, independent custody, cross-store atomicity, or external-effect proof. No paid service, external compute, Candidate, training, protected evaluation, frozen-contract change, UI, credentials, physical hardware, or main merge is involved.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.

**ARK/JARVIS remains NOT_PASSED.**
