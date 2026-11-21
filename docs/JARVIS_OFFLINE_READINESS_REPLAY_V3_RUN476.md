# ARK AI Run476 — offline startup, request-bound replay and non-authorizing receipts

2026-10-30 JST. **Synthetic, free-only, disconnected development.** All
packages are independent/reversible and are **NOT** live JARVIS capability or
approval to execute an external action. No local PC/GPU, user data, new account,
paid service, real Candidate, protected V2 final evaluation or main merge.

## Work basis and exact source/test evidence

- PR #8 original basis: `f91dc62c18fc17b7796d584ef4872c44b9f4fbd6`, Draft.
- PR #5 original basis: `23fe76a18a2197cf19ff7daa9ac403e64d23cb4b`, Draft.
- PR #8 final ten-file? **Eight files**: four source/test packages, final source/test HEAD
  `455407fde900085056c546041e427ddeea9b370f`.
- PR #5 final **two files**, final source/test HEAD
  `7e887160853017b98373cfa88cbeeec9c7deef0a`.
- **Total five packages, 63 authored synthetic cases, 10 normal Contents API source/test commits.**
  No manual workflow dispatch, no raw object/ref bypass or force-push.

### 1. Scheduler offline due preview — 16 cases

- Source `src/ark/disconnected_schedule_preview.py`
  blob `69d1d3a7d436afb9635bc6959049982d7269075d`.
- Test `tests/test_schedule_preview_authority_fence_run476.py`
  blob `0f5028d4d6de15d53c495d15d8ce4a536bc93e56`.
- A same-class result whose clock, notification, Tool, replay or consent property
  is replaced with an authority-bearing value now fails closed. The due
  timestamp remains caller asserted, with no timer, notification or dispatch.

### 2. READ preflight/cycle authority — 8 cases

- Source `src/ark/agency/disconnected_read_cycle.py`
  blob `e40072cff42c3796ffe1c5202b515f0354f8e973`.
- Test `tests/test_read_cycle_authority_fence_run476.py`
  blob `8662c29c3caf36519fd70bba0286835a0475f385`.
- An exact-type forged preflight or completed shadow-cycle receipt may not
  advertise external verification, dispatch, clock/consent or replay authority.
  No ToolBackend runs and caller PlanGraph remains unchanged.

### 3. Opt-in request-bound fixture result — 16 cases

- New source `src/ark/agency/disconnected_fixture_binding.py`
  blob `f65d08e04760a72458ec64abbc6421194d1e234e`.
- New test `tests/test_disconnected_fixture_request_binding_run476.py`
  blob `e37608b3d4eff76c6a0ccc652955b7d13713b13d`.
- Independently reexecute only an in-memory deterministic fixture and bind
  existing v1 input/result hashes to an **exact request ID** in a new hash
  domain. Identical outputs from distinct request IDs yield distinct
  request-bound digests. This does not change frozen v1 hashes, and is neither
  authenticated evidence nor a durable exactly-once authority.

### 4. V3 runtime identity deletion — 10 cases

- Source `src/ark/learning/runtime_guard.py`
  blob `9b1092a91396efdf1e5fb9a8cd89449ef918bbc1`.
- New test `tests/v3/test_runtime_identity_field_disappearance_run476.py`
  blob `0599309951a21c725a217700b81248b1fc11e0f5`.
- Missing frozen environment/hardware or measured runtime identity during a
  synthetic validation callback becomes RuntimeIdentityMismatch, not a raw
  KeyError/AttributeError. No GPU probing, training, weights or compute startup.

### 5. Detached local startup readiness — 13 cases

- New source `src/ark/disconnected_local_readiness.py`
  blob `cb09258e6588552306cd3c5f670d5a6adc1b5d6e`.
- New test `tests/test_disconnected_local_readiness_run476.py`
  blob `62b2e54ea2e8c62bffba20d2861a07c19e73863e`.
- Opt-in diagnosis combines an **already-opened query-only SQLite connection**,
  a retained bounded schema seal and exact registered READ-only preflight.
  Schema is rechecked after preflight. A detached digest is returned with
  explicit NO startup, Tool, authentication or cross-store atomicity authority.
  It never opens a file path, reads application rows, or contacts a backend.

## Observed validation, not invented PASS

- Previous PR #8 source/test #1557, run `41028977437`: all six
  Ubuntu/Windows jobs GREEN; this certifies **Run475** only.
- Previous PR #8 checkpoint #1559, run `41029300776`: reported completed
  success for its old checkpoint HEAD.
- Previous PR #5 source/test #1553, run `41028538883`: 6/6 GREEN
  on old Run475 source/test HEAD.
- At the last Run476 check, PR #8 fixture binding CI **#1565**
  run `41036476964` was IN PROGRESS with Ubuntu 3.12/3.13 GREEN;
  other jobs were still running. PR #8 final startup CI **#1571**
  run `41036936776` had not finished.
- PR #5 current final V3 CI **#1567**, run `41036617556`
  had Ubuntu 3.11–3.13 and Windows 3.11 GREEN, other Windows jobs ongoing.
- This is **not** an exact-current-HEAD 6/6 GREEN claim. No independent
  local whole-repository pytest/Ruff execution is asserted. All ten file
  blobs were fetched from their exact final source/test HEADs and verified.

## Boundaries and next safe work

Frozen V1/V2/Local UI/Launcher evidence, Memory v1 DDL, protected V2 final
evaluation, V3 Contract 1, provenance/contamination/reproducibility, human
approval and main merge gates remain unchanged. PR #5/#8 remain Draft and
unmerged. This evidence does not assert real user consent, authenticated clock,
SQLite writer provenance, cross-database atomicity, external exactly-once
outcomes, paid compute approval, real Candidate training or JARVIS PASS.

Next: check **#1571/#1567 exact HEADs**; on real failure inspect job logs
and apply the smallest normal Contents API correction while continuing an
unrelated free lane. Then prioritize durable Memory CAS and coherent snapshots,
UNKNOWN WRITE recovery, trusted-clock audit-before-action, occurrence replay
fencing, privacy lifecycle and contract-preserving V3 free-only review.
