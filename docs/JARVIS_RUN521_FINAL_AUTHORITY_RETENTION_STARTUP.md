# ARK AI — Run521 JARVIS local-only safety evidence

This document records three isolated, reversible implementation/test packages on
[Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). They do not enable
live ToolBackend calls, automatic replay, trusted time, actual notifications,
personal-context disclosure, data deletion, or external effects.

## Exact work basis and changes

Initial PR #8 source basis:
`b2b0b0f5290238c2401c3189ff6c629421245374`
(Run520 canonical checkpoint; source and frozen contract state unchanged at that point).

1. **Retained registered READ review post-denial fence**. Source
   `src/ark/agency/disconnected_registered_receipt_review.py`, commits
   `39102daeb7f20c680ad7408f5b7c4da099a0d2a9` and
   `bb5d83b777b49b8ecdf1aa6fef202f8d76767e82`.
   Output fields are rechecked *after* every denied-authority property getter,
   and separately retained link/witness plus exact registered call/grant/fixture
   are reverified after those getters. No journal v1 schema change; no SQL
   append, backend dispatch, replay permission, clock attestation, or historical
   actor proof. `tests/test_registered_receipt_final_denial_run521.py`,
   source+test HEAD `897f41a0bc96ae249d1d622c67f49bcb9c2b3064`,
   adds **12 authored cases** including six output fields and five original
   inputs mutated by False-valued terminal callbacks.

2. **Personal Context retention inventory terminal custody**. Source
   `src/ark/personal_context_retention_review.py` commit
   `2fc71d79fbc61230870e28027433c9e0d175d7b3`.
   After the last denial-only `context_use_authorized` property the reviewer
   rechecks all output fields, the original scope/source and retained item
   epochs. `tests/test_retention_last_denial_custody_run521.py` at
   `49874d2bcef64d887d68009b249bfe4c03c6bffc` adds **11 cases**
   for output, item state/revision, scope and source mutation.
   A result is content-minimized and cannot establish real consent, erase
   WAL/backups, authorize cleanup, or certify an independent revocation witness.

3. **Startup readiness post-lookup/traversal integrity**. Source
   `src/ark/startup_readiness_review.py` commit
   `3306176b671c084cdc3a7141297c515b686ad470`.
   A cached `state()` now re-derives graph consistency after the final
   effective-state getter; `root_blockers()` rechecks after dependency
   traversal. `tests/test_startup_post_traversal_custody_run521.py`,
   latest source+test HEAD `e84155f14d0fa4becd5803c4f63fad0371f2a551`,
   adds **8 cases**, including reentrant reflected graph edits.
   `READY` remains a detached assertion, not a capability grant.

**PR #8 total: 31 newly authored pytest cases.** Authored cases are not
independently observed local PASS results; no full-checkout local pytest/Ruff
was available due to repository network/DNS limitations in the execution
environment. GitHub-hosted public-repo CI is the verification path.

## Exact-head CI at the documentation creation boundary

- Previous Run520 exact checkpoint HEAD
  `b2b0b0f5290238c2401c3189ff6c629421245374`:
  [CI 41274924675](https://github.com/Iam-2squared/ark-ai/actions/runs/41274924675)
  completed **SUCCESS / six jobs GREEN**. This does not prove Run521 changes.
- Retained READ source+test HEAD
  `897f41a0bc96ae249d1d622c67f49bcb9c2b3064`:
  [CI 41278284115](https://github.com/Iam-2squared/ark-ai/actions/runs/41278284115)
  **IN PROGRESS** at sampled time (Ubuntu 3/3 green; Windows still running).
- Retention source+test HEAD
  `49874d2bcef64d887d68009b249bfe4c03c6bffc`:
  [CI 41278438118](https://github.com/Iam-2squared/ark-ai/actions/runs/41278438118)
  **QUEUED** at last sampled time.
- Startup final source+test HEAD
  `e84155f14d0fa4becd5803c4f63fad0371f2a551`:
  [CI 41278527291](https://github.com/Iam-2squared/ark-ai/actions/runs/41278527291)
  **QUEUED** at last sampled time. This is the final source/test commit
  for these three packages; earlier GREEN must not be inherited.

## Hard boundaries retained

- Both [PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) and
  [PR #8](https://github.com/Iam-2squared/ark-ai/pull/8) remain Draft/unmerged.
  `main` shared base `7a843f17eb96ed13d66f23b58b06406b3002e405`.
- Frozen V1/V2/Local UI/Launcher evidence, Memory v1 and agency contracts,
  protected V2 evaluator, and V3 frozen Contract are not modified here.
- No paid API, external GPU/compute, new credentials, model weights, real
  Candidate, protected final evaluation, new account connection, real
  ToolBackend execution, notification, manual-owner decisions, destructive
  erasure or automatic WRITE replay is performed.
- SQLite witnesses and untrusted Python-carrier identity checks prove *local
  consistency only*. They cannot authenticate historical writers, provide
  independent custody, show a trusted clock/consent, or attest physical effects.

## Next plan / 今後の方針

Resolve exact-head six-platform CI and fix only observed failures. After
registered READ lower-layer CI is GREEN, bind the retained `act_`→`req_`
link to read-only Planner DAG recovery without changing journal v1 or
granting Tool dispatch. Independently prioritize Memory CAS/coherent
snapshots, UNKNOWN WRITE manual-only recovery, audit-before-action trusted
clock, occurrence replay fencing, Scheduler deduplication, and privacy-safe
Personal Context revocation lifecycle. Overall ARK/JARVIS remains NOT_PASSED.
