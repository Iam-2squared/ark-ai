# Run404 — disconnected multi-WRITE recovery, ActionAudit ingress and approval-claim epochs

Scope: additive / isolated ARK JARVIS foundations on Draft PR #8. This is a
synthetic, read-only/mock-only engineering threat review, **not an evaluation PASS**.

## Package A — all-WRITE restart reconciliation

Source: `src/ark/agency/synthetic_write_plan_recovery_review.py`

Tests: `tests/test_synthetic_write_plan_recovery_run404.py` (15 cases).

- Reconcile **all** registry-declared WRITE PlanSteps, without cherry-picking a
  successful-looking step. At most 128 plan steps are accepted; a plan containing
  no WRITE is not a valid WRITE recovery review.
- Resolve each step to the original immutable ToolRegistry revision, reject
  duplicate WRITE request identities across steps, and check original PlanStep,
  ToolCall, argument carrier, dependency tuple, registry revision and SQLite
  source identities across review callbacks.
- Each step uses the existing disconnected three-/four-store recovery reviewer.
  All steps must agree on the plan tail and independent reservation/audit/link
  witnesses. Re-read the first step and plan at the end to reject visible drift.
- `uncertain_step_ids` includes **RUNNING/UNKNOWN** plus a locally PENDING
  step that already has an occurrence or sidecar link. This intentionally
  distinguishes a journal state from a safe-to-dispatch decision.
- No part of the result authorizes action, automatic retry or external outcome
  inference, including a locally marked SUCCEEDED step. No backend is called.

Limits: no global SQLite transaction across plan, reservation, audit and
sidecar; a repeated read cannot exclude simultaneous or post-check races.
A malicious host process can rewrite both data and the caller-held evidence.
No OS crash, live backend or independently verified durable issuer is modeled.

## Package B — audit continuity at SQLite open boundaries

Source: `src/ark/agency/audit_continuity_review.py`

Tests: `tests/test_audit_continuity_open_epoch_run404.py` (9 cases).

- The original Path object and retained prefix witness are checked immediately
  after `Path.resolve()`, after `Path.as_uri()`, and after the read-only
  SQLite handle is obtained, **before the first SELECT**.
- A returned handle is closed on a detected source/witness drift; no empty
  audit database is created for a missing path. A short SQLite read transaction
  continues to protect the per-database snapshot.
- Existing ActionAudit v1 table DDL, event semantics and caller-clock ordering
  remain unchanged; audit continuity is not a clock authenticity attestation.

Limits: Path object identity is not OS inode custody. Source replacement at
the filesystem level or malicious SQLite VFS behavior is not ruled out.

## Package C — synthetic claim first-bind authority separation

Source: `src/ark/agency/synthetic_approval_claim_review.py`

Tests: `tests/test_synthetic_approval_first_bind_epoch_run404.py` (11 cases).

- Freeze the caller's ToolCall arguments carrier, canonical request identity,
  registry revision and envelope identity **before** the first registry bind or
  envelope integrity callback. Verify at the first/second bind, hash generation
  and immediately before returning a claim or review.
- Refuse reflected mutations in self-consistent callback results; a substituted
  first bind is not evidence that the caller requested the substituted action.
- The synthetic claim and its cancellation set are still caller supplied and
  unauthenticated. No approval token is minted for a real PermissionGate, and
  the review is incapable of certifying human consent.

Limits: process-local change detection is not a cryptographic signature,
trusted-clock source, authentication mechanism, or external cancellation
guarantee. Frozen V1/V2/Local UI/Launcher contracts are untouched.

## Verification and operator boundaries

- CI is responsible for exact-head Linux/Windows Python 3.11–3.13 tests and
  Ruff; **no GREEN claim is made in this document without exact-head evidence**.
- Early intermediate CI runs may fail while a Contents-API source/test package
  is composed. Treat each run's own commit status independently; don't inherit
  a passing CI status from a prior SHA.
- Writes use only ordinary GitHub Contents API with fresh PR HEAD re-reads,
  never force-push, raw Git-object writes, workflow reruns or main merges.
- All actions in this review are local synthetic/mock tests. No real executor,
  paid API/GPU, device, notification, real Candidate, protected V2 final
  evaluation, V3 promotion, approval, or personal-data export/deletion.

## Next plan / 今後の方針

1. Confirm source+tests exact-head CI. Repair actual test/ruff regressions
   with the smallest semantics-preserving ordinary Contents-API write.
2. Add bounded cross-store crash/restart probes for two or more dependent
   WRITEs with truncated histories and independently retained prefixes;
   neither successful local mocks nor orphan reservations may grant replay.
3. Develop an explicit authenticated-clock/issuer interface only in a
   **deny-by-default disconnected mode**, with no real authority until review.
4. Continue Memory CAS/coherent snapshots, privacy revocation, proactive and
   Observation contracts; keep V3 provenance and all paid/frozen gates closed.

## Package D — disconnected caller-clock continuity (additive)

Source: `src/ark/agency/synthetic_clock_sequence_review.py`

Tests: `tests/test_synthetic_clock_sequence_run404.py` (27 fixture cases).

- A bounded stream (maximum 1,024 samples) carries exact integer sequence,
  caller-provided source digest, wall timestamp and monotonic timestamp.
  Strict sequence continuity, nondecreasing wall time and increasing monotonic
  time reject local regression or duplicate timing evidence.
- The local hash chain can be checked against a separately retained prefix
  after a simulated restart. Earlier sample mutation, generator termination
  callbacks, invalid types, truncated history and infinite streams are all
  fail-closed. A caller may not replace historical observations mid-review.
- The initial EMPTY witness intentionally conveys no clock readiness;
  populated witnesses always report
  `trusted_clock_verified=False`,
  `dispatch_authorized=False` and
  `automatic_replay_authorized=False`.
- All inputs are locally supplied fixtures: there is **no** external
  time source, signed timestamp, trusted monotonic device, attested identity,
  OS clock sampling, human authority, or real action pathway. This is a
  reversible interface rehearsal only, not an integration approval.
