# Run1176 — SQLite Memory store path identity

## Finding

`SQLiteMemoryStore` rechecked its path during each operation, but its public `path` attribute was not bound to the path selected at construction. Reassigning it before an operation to a different, valid regular SQLite database could establish a new per-operation epoch and redirect a private read/write. Existing tests covered symlink, hardlink, type, and mid-operation drift, but not a valid alternate database selected before the operation.

## Change

- Retain the exact constructor-created `Path` object as a private path-identity anchor.
- Protect the anchor against ordinary reassignment and deletion.
- Check the current path against that anchor after safe-path validation and before opening either a read-write or read-only SQLite connection.
- Preserve the existing per-operation identity checks, so transient callback-driven swaps and restoration remain fail-closed.
- Keep the public `path` attribute and V1 schema/API shape unchanged; an ordinary path rebind is rejected when the store next opens a database.

## Regression evidence

Synthetic local fixtures create two valid SQLite stores with the same owner/namespace. Rebinding one store to the other database is denied before read or write; an equal-valued but different `Path` object is also denied; the private identity anchor cannot be reassigned or deleted through ordinary attribute operations.

## Limits

This is local process-level path identity hardening. It does not prove filesystem TOCTOU immunity, authenticated custody, physical erasure, cross-process writer identity, fsync/power-loss durability, or authorization to disclose Memory content. No V1 schema, frozen API contract, V2/V3 evaluation contract, Candidate, paid/external compute, UI, credentials, hardware, or main merge is changed. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.