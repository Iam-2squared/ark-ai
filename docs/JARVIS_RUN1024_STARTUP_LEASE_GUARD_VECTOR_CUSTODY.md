# Run1024 — startup readiness lease guard-vector custody

## Gap

The disconnected startup lease reviewer already pins exact requirement/result class descriptors and the three false-only result properties. However, those checks iterate mutable module-level name vectors and parallel tuples of import-original descriptors. If one vector is rebound to an empty tuple or an equal-valued clone, `zip()` can silently skip or substitute the checks before the snapshot integrity callback.

## Change

The lease protocol now captures the identities of all five descriptor-name vectors and all five corresponding original-carrier tuples. The public review entrypoint checks that complete vector set before invoking the startup source guard or touching the snapshot/requirements. The existing per-field descriptor checks and repeated in-review protocol checks remain in place.

## Regression coverage

`tests/test_startup_lease_guard_vector_custody_run1024.py` tests empty and equal-valued replacement of each descriptor vector and each original-carrier tuple. A poisoned snapshot integrity callback proves the protocol-vector denial occurs first. The clean synthetic lease remains denial-only.

## Limits

This is local Python process-integrity hardening for a disconnected fixture reviewer. It does not authenticate a physical machine, trusted clock, human consent, credential, backend, notification, or device; it does not grant startup or dispatch authority. No UI, frozen contract, paid service, external compute, real hardware action, or main branch is involved.

The package is based on PR #61's exact-head green identifier-control implementation. This child requires its own exact-head six-job CI. PR #5 remains Draft/unmerged; PR #8 remains Draft/unmerged.
