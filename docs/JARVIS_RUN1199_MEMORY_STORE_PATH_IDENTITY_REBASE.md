# Run1199 — Memory SQLite constructor-bound path identity

## Exact basis

- Parent: Draft PR #8, branch \`research/jarvis-foundations\`.
- Exact parent work-basis HEAD: \`2df6b261554428cd01871f2723ce87c4dd05e4b4\`.
- Child branch: \`research/run1199-memory-store-path-identity-rebase\`.
- Source commit: \`f11f81d59d4bc545529a8a16735c4f9692e4ee47\`.
- Focused test commits: \`106f441dcb75b62c7933f64935b75715906e569b\` and correction \`637fc260b2df066bffc41e577fade983adc2f5a6\`.
- Rebased the isolated Run1176 path-identity finding onto the latest observed Draft PR #8 foundation without changing the Memory v1 schema or public constructors.

## Finding and change

The local SQLite path preflight rejected aliases and unsafe path types, but a caller could reassign \`SQLiteMemoryStore.path\` to another valid regular database before an operation. A new constructor-bound Path identity now prevents that redirection.

- The exact original Path object is retained in a non-shadowable slot while \`__dict__\` remains available for existing test-only callback injection.
- Ordinary assignment/deletion of the private identity slot is rejected.
- Each read/write connection checks the constructor identity before filesystem inspection, after reentrant path preflight, after path URI resolution, and after SQLite open/connection setup.
- A connection opened during a callback-time path rebind is closed before the operation can proceed.
- The public \`path\` attribute remains available; an ordinary rebind fails closed on the next database operation.

## Synthetic regression coverage

Temporary local SQLite fixtures cover:
- redirecting to another valid database is denied before path I/O;
- an equal-valued but different Path object is rejected before write;
- the identity slot cannot be ordinarily reassigned, deleted or shadowed through \`__dict__\`;
- a reentrant \`Path.lstat\` callback that rebinds the path is rejected before SQLite open;
- a SQLite-open callback that rebinds the path causes the opened handle to be closed.

No live personal data, external storage, real tool dispatch or user files are accessed.

## Limits and validation

This is an in-process constructor-identity guard, not a Python sandbox, atomic directory-descriptor custody, filesystem TOCTOU defense, authenticated storage provenance, physical erasure, fsync/power-loss proof or cross-store atomicity. Reflective mutation by arbitrary code in the same process remains outside this boundary. Memory v1 DDL/public API and frozen evaluation contracts are unchanged.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No paid/external compute, Candidate, protected V2 evaluation, credentials, physical hardware, destructive operation, UI/frontend work, frozen-contract change or main merge is involved. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
