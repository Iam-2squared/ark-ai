# JARVIS execution-safety integration gate (read-only audit)

Status: **non-normative integration checklist** for Draft PR #8 as inspected at
`10a6f65a17812f0b0aa5feed19fb38ff582c5dd1` (2026-10-08).
This checklist does **not** modify frozen contracts, authorize dispatch, or
claim that unmerged/offline candidates have passed repository CI.

## Verified source facts at this HEAD

- `src/ark/agency/registry.py` (blob
  `27930e56938938d63239730ab8936540c515972e`) defines deterministic
  registry-bound identities and readonly registration mappings. However the
  registry instance's `_revision` and `_registrations` are ordinary
  assignable attributes; a Protocol-conforming object's `execute` attribute
  need not be callable. This source alone is not a secure dispatch boundary.
- `src/ark/agency/policy.py` (blob
  `938dc26bf2074b7d287a0051c6bfa82202ffec94`) checks caller-provided
  `ToolSpec.effect` rather than authoritative registry effect. A caller can
  misclassify WRITE as READ. One-shot consumption is a per-instance Python
  set and is not restart-safe; malformed grant subtypes are not rejected.
- `src/ark/agency/__init__.py` (blob
  `bb6ec5fc68198ac9c02129509c80b40fc39378cd`) has no public
  registry identity exports yet.
- `src/ark/memory/sqlite_store.py` (blob
  `68d30f464f5487b13def452ec49d3707f1ddffbf`) samples a clock
  before opening the write transaction. It needs exact persisted schema,
  row/event integrity, CAS/expiry race, and coherent snapshot proof before
  Personal Context is integrated.
- CI #261 (run `37603417159`) is GREEN for this unchanged PR #8 HEAD
  only, not for any offline source-ready hardening.

## Mandatory execution-lane order (no production dispatch until all GREEN)

1. Save regression fixtures for the exact registry revision and bound-action
   vectors; verify registration-order independence, unknown-tool rejection,
   capability/effect/backend identity changes, and zero backend calls.
2. Save a verified immutable/callable ToolRegistry source and public exports.
   Preserve existing identity vectors; require exact-HEAD Windows/Linux CI.
3. Save exact-type PermissionGate input/grant checks. Snapshot and validate
   all grants without consuming a token on malformed input. Derive effect from
   the active registry, **not** a caller-supplied ToolSpec.
4. Introduce a reviewed trusted approval issuer and authenticated consent
   artifacts. A caller-injected mock verifier and an internal SQLite hash chain
   alone are *not* approval provenance. Expiry, scope, registry revision,
   request identity and replay limits must be durable.
5. Bind one-shot consumption to an execution occurrence atomically and retain
   a reviewed restart recovery policy. Never automatically replay unknown
   outcomes or treat a matching request ID as a fresh occurrence.
6. Make pre-action audit truly fail-closed and durably correlated to one
   occurrence, including crash-injection tests. Independent SQLite files are
   **not** an atomic cross-file transaction. Independently pin any claimed
   authenticated external anchor; do not derive it from the same database.
7. Test only against a disconnected mock executor. A read-only startup probe
   must report WRITE as blocked if any consent/audit/occurrence dependency is
   missing. Do not integrate live PC/filesystem/network side effects.

## Parallel independent lanes

- Memory and Planner: land exact-head row/schema/event integrity, trusted
  clock/locking, CAS, expiry and persistence/recovery separately.
- Observation: fixture-only envelopes and bounded lineage; no live capture.
- Personal Context and Scheduler: minimum necessary opt-in projection and
  read-only readiness; no implicit consent propagation.
- V3: free-only provenance and JSON/identity guards on its separate Draft PR;
  no training, Candidate generation, protected evaluation or promotion.

## Evidence discipline and source-drift warning

The offline consolidated candidate is not byte-identical to the PR #8
implementation for `agency/contracts.py`, `agency/planner.py`,
`memory/contracts.py`, `memory/sqlite_store.py` and `observations.py`.
Do not copy an offline source tree wholesale into GitHub. A local pytest PASS
does not supersede an exact-head CI result; mark dependent gates pending until
matching source/tests are committed and CI is GREEN.

No paid/external GPU compute, paid APIs/services, new accounts/credentials,
destructive/migration actions, frozen-contract changes, protected evaluation,
automatic promotion, physical-PC operations or main merge is authorized here.
