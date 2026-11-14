# Run437 — Observation window carrier custody and Windows CI diagnosis

Status: **Draft PR #8 only; source/test changes saved, exact-head CI pending**.
Work basis: `fc0b086d954982ab15f466d78f36f4cc06a8d0aa` (Run436
checkpoint). No frozen contract was edited. This is a disconnected,
privacy-safe development record, not a roadmap PASS.

## Package A — original observation field carriers

The existing `ObservationWindowReview.assert_consistent()` compared each
`ObservationEnvelope` against its deterministic `observation_id` and
checked envelope/tuple object identity. An equal-valued, freshly allocated
field string could therefore replace `source_id`, `adapter_id`,
`privacy_scope`, `content_sha256`, or `parent_sha256` without changing
the canonical digest. Caller-origin provenance can no longer be inferred
solely from an equality-preserving digest.

Commit `908c644d0fa167a665d7871aecdeda4ea03d0099` retains the exact
original field carriers at window construction and checks them both before
and after each reuse-time envelope identity callback. The existing window
digest algorithm, public field shapes, and no-action policy remain unchanged.
The `_field_carrier_epoch` is an in-memory reflection-drift witness, **not**
a signature or trusted source authenticator. It cannot prevent all malicious
modifications within a compromised Python process.

Commit `a8c531abf8fdfac67e099d5939ade733d3491e65` adds
`tests/test_observation_window_original_field_carriers_run437.py`:
18 field × entrypoint parameter-expanded cases, two reentrant construction/
reuse cases, and one unchanged deterministic witness case (**21 added**).
Expected rejection does not constitute an already observed PASS.
No live microphone, camera, screenshot, notification, disclosure or backend.

## Package B — Windows pytest oversized test-name diagnostic

The Windows Python 3.12 job `121260220252` for run
`40223600447` / CI #1221 was read through its actual Actions job logs.
The visible log shows pytest reach 100% progress by
`2026-10-25T19:01:25Z` then start an
`ERROR at setup of test_fixture_rejects_oversized_payload[text-aaaa...]`
report. The parametrized text payload is ~4 MiB; the reported test name
contained a vast run of literal `a` characters, and the retrieved log was
already over 4.2 million characters. The associated Windows jobs remained
`in_progress` at inspection; more recent CI runs remained `queued`.
This is concrete excessive-test-ID/log-output evidence, **not sufficient
to establish the underlying setup error or prove a runner fix**.

Commit `36c1c9ca4f4d54a44ac64656e4cf85db90ced1ab` adds two bounded,
descriptive pytest IDs in
`tests/test_observation_fixture_production_adapters.py`:
`text-over-byte-limit` and `binary-over-byte-limit`.
The 4 MiB content fixtures and their rejection assertions are unchanged.
No test was skipped, expected outcome weakened, CI rerun manually
dispatched, or paid runner created. Inspect new exact-head Windows tests
when GitHub Actions processes the queue.

## Independent read-only audit — detached plan bundle completeness

As of the inspected `synthetic_plan_recovery_bundle_review.py` blob
`bf0d05b39d0e40000d714b50c8b57e5ed46417d2`, the detached bundle
restorer checks each archive's digest/topology, entry order, uniqueness and
internal hold lists. It does **not** receive an independently retained
complete set of WRITE step IDs. A syntactically valid subset may therefore
be indistinguishable to this isolated decoder from the full set when hold
lists are empty. This is a **source-level candidate gap**, not a reproduced
security bypass or a reason to authorize dispatch. The bundle was already
explicitly non-authoritative and source-head CI for its newly introduced
Run434 code remains unverified.

**Deferred until its exact-head dependency is GREEN:** reproduce the subset
case with a negative regression and introduce an explicit caller-retained
expected membership witness without changing frozen plan contracts or
presenting a self-hashed header as independent proof. Keep both automatic
replay and operational dispatch disabled.

## CI / integrity boundaries

- Run436 work-basis checkpoint: `fc0b086d954982ab15f466d78f36f4cc06a8d0aa`.
- Window source: `908c644d0fa167a665d7871aecdeda4ea03d0099`.
- Window regression: `a8c531abf8fdfac67e099d5939ade733d3491e65`.
- Windows diagnostic test-ID correction: `36c1c9ca4f4d54a44ac64656e4cf85db90ced1ab`.
- At last inspected Actions collection: #1250 / `40245948671`,
  #1251 / `40246006387`, #1252 / `40246195602` all `queued`.
  These runs do not yet attest any new tests or fix.
- All authorizations remain explicitly absent: no real issuer/clock, external
  effect attestation, global cross-SQLite atomicity, complete JARVIS PASS,
  real Candidate work, protected V2 final-evaluation opening, or main merge.
  PR #5 and PR #8 stay Draft/unmerged. No spending or hardware actions.

## Prioritized next work

1. Resolve the **actual Windows #1221 pytest setup error**, using completed
   job logs and bounded IDs; test whether queue saturation clears, without
   weakening the suite or manually duplicating runs.
2. Inspect #1252 and successor exact-head CI once jobs finish. Fix any real
   failure through normal Contents API only, preserving test semantics.
3. After Run434 dependency GREEN, reproduce detached bundle membership
   omission and add external retained expected-membership verification.
4. Continue independent Memory/process CAS and privacy veto work; postpone
   multi-store recovery integration until lower-level exact-head CI is GREEN.
