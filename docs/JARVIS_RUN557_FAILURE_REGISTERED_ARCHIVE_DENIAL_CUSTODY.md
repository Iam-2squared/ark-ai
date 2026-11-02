# Run557 — Detached failure archive and registered READ join denial custody

These are strictly disconnected mock-only reviews. No real ToolBackend
dispatch, write authorization, authenticated FAILED/BLOCKED outcome,
dependency completion, independently attested SQLite history or replay
permission is established.

## Package A — Hypothetical FAILED/BLOCKED create-only archive

The archive review now retains the **import-time original descriptors** for
five deny-only properties on `ArchivedDisconnectedFailure`. The definition
check runs before restarting file/fixture review, before a new archive can be
created, during witness construction and before the exclusive create path.
A forged `False` getter cannot be silently accepted as the original
safety implementation. A preinstalled forged descriptor blocks local file
creation instead of leaving a new ambiguous file.

- Source commit `8edffb782d92742b55c365aad36bc14c4b559330`
- New tests `tests/test_failure_archive_import_denial_custody_run557.py`,
  commit `77ec96c613e48ae22b67c173ab31d8fb59a196cc`:
  **13 authored parameter-expanded cases** (five pre-create, five restart,
  one verifier-callback swap, one first-read swap, one unchanged control).
- Existing archive test updated to expect the stronger pre-create denial,
  commit `f316c234a0f1e026fdd8719df15fa3644a73c37e`.
- Lint-only import fixes `84ee46b56ca8efe33505fd43becfad36851e836b`
  and `ea605c3d4aaec9125b4d30b72d5643bed52fa516`.

## Package B — Composite registered READ/mock-cycle archive

The composite bridge now pins the original denial definitions of its
**three independent review types**: its output, the archived mock cycle,
and the ToolRegistry-bound registered READ receipt set. It checks these
definitions before inspecting any delegated source and across delegated
callbacks, eliminating a preinstalled or late forged false-valued getter
that could otherwise be re-baselined as the new denial.

- Source commit `d7a5836a24bf09d6b2a0367cb48f116bc704c359`
- New tests `tests/test_registered_archive_original_denial_custody_run557.py`,
  commit `66212881f31d1d018a5ab785450f89c34128ed82`:
  **18 authored parameter-expanded cases**, across 15 class-property
  substitutions, two late delegated callback swaps, and one unchanged
  disconnected fixture.
- Existing regression diagnostic and Ruff import formatting updated via
  `1b98eb50f105232cc05a9eecdea8fef521972822` and
  `b0e15ae24894c3e470c1c80fdbaa428fe1da1268`.

## Validation status and boundaries

- Earlier PR #8 exact-head run `41448215128` **SUCCESS** before these
  source changes.
- Run `41457133756` **FAILED** (Ruff I001 on new tests).
  Run `41457625511` **FAILED** (Ruff I001 persisted).
  The subsequent import-order correction is saved; the corrected
  source/test HEAD run `41458256896` was **IN PROGRESS** when this
  technical note was authored, not certified GREEN.
- The 31 new tests above are **authored test cases**, not independent
  local pytest PASS counts. Exact-head CI status must be checked again.
  No frozen contract, main merge or human-review gate changed.

### Further work

After exact-head GREEN, consider binding retained hypothetical
FAILED/BLOCKED terminal receipts to separately audited registered READ
step evidence, with explicit handling of partial success and
non-atomic cross-SQLite snapshots. Do not infer real effects,
authenticated failure, permission or safe automatic replay.
