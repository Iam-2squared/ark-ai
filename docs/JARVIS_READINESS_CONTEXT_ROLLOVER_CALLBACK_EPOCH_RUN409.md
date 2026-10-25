# Run409 — Final callback custody across readiness, private Context and observation rollover

**Scope:** isolated, reversible, disconnected synthetic fixtures on Draft PR #8.
This document describes only the code and regression artifacts at their stated
commit SHAs, not authenticated execution, proof of consent, or a JARVIS PASS.

## Work basis and concurrency

The exact initial HEAD was `5ec2154d390e34ccefa05be1ca7adf20417abc16`,
already containing the separate Run408 Memory query-hash, Mock registry-binding,
mixed-WRITE crash-prefix and partial-erasure work. Its exact-head CI **#948 /
run `40156138953`** completed SUCCESS on the six Ubuntu/Windows Python
3.11–3.13 matrix jobs. Run407's checkpoint remains the historical basis.
No concurrent code paths from the Run408 packages were overwritten.

## Package A — Startup hash completion fence (+7 regression cases)

**Source:** `src/ark/startup_readiness_review.py`, commit
`34dfdaad329d5675be682bfbd202d32259130dd0`.

**Tests:** `tests/test_startup_final_hash_epoch_run409.py`, commit
`aee730ded52bc282287b848e2c75ef8efc3d29f0`.

- Validate original probe carriers **after** the final witness SHA-256 callback,
  not only after JSON serialization. An injected hash callback can otherwise
  rewrite the source readiness graph as the function returns a stale READY or
  BLOCKED result.
- Pin a cached StartupSnapshot's original digest string carrier alongside its
  component carriers, so reflective equal-value substitution during a digest
  callback fails closed rather than becoming the new baseline.
- Regression fixtures cover changes in initial local state, schema revision,
  failure code, dependency set, equal-value dependency tuple, and equal-value
  cached digest carrier. Unmodified blocked dependency propagation remains
  `DEPENDENCY_BLOCKED`.
- All statuses remain synthetic probe assertions; no tool/notification dispatch.

## Package B — Final privacy-veto projection custody (+8 regression cases)

**Source:** `src/ark/personal_context_revocation_review.py`, commit
`34ae0e26c9702063fcba789daf86bd2b6f724539`.

**Tests:** `tests/test_privacy_final_bundle_epoch_run409.py`, commit
`6ebd7b355936b48733ae0013c2199174747b1bb4`.

- A Personal Context bundle is produced *before* the second revocation check
  and the retained-history continuity review. Those later operations are
  reentrant boundaries; without a retained copy the caller could receive a
  different content/scope/provenance carrier than the one actually reviewed.
- Pin the exact bundle tuple, items, content, namespace, memory IDs,
  revision, provenance IDs and digest headers; revalidate immediately after
  each final revocation/continuity read.
- Test changed plaintext, scope, equal-value content/item/tuple/digest
  replacement, plus mutation during the final continuity callback.
- No personal-data erasure, export or consent authorization is performed.
  The SQLite revocation and Memory stores remain independently committed,
  so the post-check time-of-use race is still unresolved.

## Package C — Observation rollover original baselines (+7 regression cases)

**Source:** `src/ark/observation_rollover_review.py`, commit
`5a48a189bac9f9ce857f834f69252fa94db0a0ee`.

**Tests:** `tests/test_observation_rollover_original_epoch_run409.py`, commit
`003233ffa9f5a0c6fb2ccfb1f56f20b7d2713013`. Test-fixture callback
scoping correction: `10381b4a9ab70b63d3f3d18d8593d0fc4d65e536`.

- Capture original observation header/envelope tuple and independently
  retained rollover witness **before** calling the first reentrant window
  consistency/freshness validator. Prevent a callback from rebasing prior
  generations or an observation time into a new locally consistent baseline.
- Recheck after the first validator, freshness validator, current-window witness,
  payload serializer, SHA-256 callback and final validator.
- Regression fixtures cover first-validator generation and same-value SHA
  carrier replacements, reflected time/tuple rebasing, payload mutation that
  another hash callback would restore, and hash mutation that another
  window-consistency callback would restore.
- No media capture, user authorization, authenticated source or notification.

## Exact-head CI and evidence interpretation

A GitHub PR workflow run validates only its own exact head SHA and must not
be transferred to a later Contents commit. Our first package's test HEAD
`aee730ded52bc282287b848e2c75ef8efc3d29f0` had CI **#950 /
`40156608437`**: five jobs SUCCESS and Windows Python 3.11 FAILED
with `ConnectionAbortedError [WinError 10053]` in the **unchanged**
`tests/ui/test_server.py::test_cross_origin_reads_and_writes_rejected[headers4]`.
This is a real failed exact-head run, not proof that startup tests failed, and
not authorization to alter frozen Local UI. No duplicate workflow rerun was
started; separate newer commit-triggered runs are evaluated independently.

**Latest Run409 source+tests head:** `10381b4a9ab70b63d3f3d18d8593d0fc4d65e536`.
Its own exact-head workflow is **#955 / run `40156902277`** (QUEUED when
first inspected); full-matrix GREEN is **not yet established**.
All run IDs / job outcomes in the final checkpoint must be refreshed from
GitHub before reporting additional PASS evidence.

## Immutable and authorization boundaries

Frozen V1/V2/Local UI/Launcher, protected V2 final evaluation, Memory v1,
ActionAudit v1 and V3 Contract 1 were not modified. V3 PR #5 remains Draft,
unmerged, NOT_PASSED. No paid or potentially billable GPU/API/cloud/service,
real Candidate build, protected evaluation opening, hardware action,
credentials, real ToolBackend execution, notification or main merge was used.

## Next plan / 今後の方針

1. Check #955 exact final source/test HEAD across six OS/Python jobs. Distinguish
   genuine source regressions from unrelated Windows socket flakiness; never
   weaken a frozen UI test to force a GREEN badge.
2. Preserve exact prior HEAD evidence and update one canonical
   `docs/PROJECT_STATUS.md` checkpoint after rereading the latest branch.
3. Continue mock-only Planner multi-WRITE crash/restart and retained prefix
   diagnostics, Memory CAS/event integrity, privacy lifecycle races, and
   fail-closed issuer/clock/action interfaces.
4. Keep real execution and external effects disconnected until authenticated
   consent, trusted time, durable audit-before-action, outcome receipts and
   independently approved integration gates are proven.
