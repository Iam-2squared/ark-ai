# ARK AI Run1016 — Action Audit outcome admission

**Work basis:** Draft PR #8 exact head `aac9ae76df364fe0b8230e36933bf1f0404e0add` on `research/jarvis-foundations`. This package is an isolated Draft child and does not modify PR #8, main, frozen contracts, or UI branches.

## Change

The current Action Audit v1 append path accepted any non-empty outcome string, and persisted outcome TEXT had no byte ceiling. This child ports the previously isolated Run990 hardening onto the current foundation head:

- Keep the existing open outcome vocabulary and public event fields.
- Require exact `str`, non-empty bounded text, at most 256 code points and 256 UTF-8 bytes.
- Reject C0/C1 controls, bidi/Unicode formatting controls, and invalid UTF-8 before opening SQLite or sampling the audit clock.
- Reject persisted outcome TEXT over 256 bytes in SQLite-side hydration admission before Python row materialization.
- Validate persisted labels during tail/history checks and paged event hydration; corruption fails closed and is never repaired.
- Pin the outcome validator as part of the Action Audit local process-integrity checks.

The v1 SQLite schema, migration plan, event shape, and existing caller `ValueError` surface remain unchanged.

## Regression coverage

Synthetic temporary SQLite only:

- Empty/whitespace, code-point overflow, UTF-8 byte overflow, newline/C1/bidi controls, lone surrogate, wrong exact types.
- Invalid caller values are rejected before SQLite connection and before clock sampling.
- A valid 256-byte UTF-8 label round-trips.
- Oversized/control-bearing persisted rows are rejected on read and append without clock sampling or mutation.

## Prior evidence and current validation

The earlier isolated PR #13 exact head `b940525c43d3e3a858352c8702dc4202598597e3` passed CI run [#44518002802](https://github.com/Iam-2squared/ark-ai/actions/runs/44518002802) GREEN 6/6. That evidence applies only to that earlier base/head pair. This child reapplies the semantics on the current PR #8 work basis and requires its own exact-head CI.

## Limits and safety

This is local input/resource-integrity hardening. It is not an authenticated audit chain, independent storage custody, trusted time, human consent, cross-store atomicity, backend attestation, or proof of an external effect. No real ToolBackend executes. No paid service, external compute, credentials, Candidate, protected V2 evaluation, frozen contract, UI branch, PR #5, PR #9, or main merge is touched.

**Current status:** exact-head CI pending; no PASS claimed. ARK/JARVIS remains NOT_PASSED.
