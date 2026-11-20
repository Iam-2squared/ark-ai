# Run1024 — startup readiness lease guard-vector custody

## Gap

The disconnected startup lease reviewer already pins exact requirement/result class descriptors and the three false-only result properties. However, those checks iterate module-level name vectors and parallel tuples of import-original descriptors. Run1024 pins those ten objects by identity. A further review found that the tuple containing the ten references was itself a replaceable module-level input; an empty or equal-valued rebind could bypass the intended reference-set comparison or turn it into an incidental `zip(strict=True)` error.

## Change

The lease protocol now captures the identities of all five descriptor-name vectors and all five corresponding original-carrier tuples. The Run1025 child captures the import-original reference tuple in the guard function's default argument and rejects any module-level rebind before invoking the startup source guard or touching the snapshot/requirements. The existing per-field descriptor checks and repeated in-review protocol checks remain in place.

## Regression coverage

`tests/test_startup_lease_guard_vector_custody_run1024.py` tests empty and equal-valued replacement of each descriptor vector, each original-carrier tuple, and the root reference tuple itself. A poisoned snapshot integrity callback proves the denial occurs first. The clean synthetic lease remains denial-only.

## Limits

This is local Python process-integrity hardening for a disconnected fixture reviewer. It does not authenticate a physical machine, trusted clock, human consent, credential, backend, notification, or device; it does not grant startup or dispatch authority. No UI, frozen contract, paid service, external compute, real hardware action, or main branch is involved.

The package is based on PR #61's exact-head green identifier-control implementation. This child requires its own exact-head six-job CI. PR #5 remains Draft/unmerged; PR #8 remains Draft/unmerged.


## Run1025 child — root reference tuple

- Pin the identity of `_ORIGINAL_GUARD_VECTOR_REFERENCES` in the guard function's import-time default argument.
- Reject both an empty replacement and an equal-valued tuple clone before the snapshot integrity callback.
- This is still process-local defensive validation, not protection against arbitrary mutation of all Python function internals or a security sandbox.
- The change is isolated on `research/startup-lease-pin-vector-root-run1025`, based on exact PR #91 head `177c827f3d2da6061dd74046177830ff9c3d5dac`.
