# ARK Run502 — detached failure execution, Memory expiry preview, local V3 identity bundles

**Scope:** three independent, zero-paid-service, opt-in implementation/test packages.
This is reproducible **source/test evidence**, not a JARVIS PASS, real-world action
receipt, trusted provenance, authenticated human decision, or training permission.

## 1. Detached Planner failure-aware fixture

- Source: `src/ark/agency/disconnected_batch_failure_fixture.py`, blob
  `31994a9c3966916c260f53dfa862debfda12f408`.
- Tests: `tests/test_disconnected_batch_failure_fixture_run502.py`, corrected
  blob `6ef4f4c6987b953d9a60704a8331b324684b8c38`.
- Verifies the existing, independently retained plan digest, exact dependency
  wavefronts and terminal projection. Caller-selected failure IDs are explicit
  **hypotheses**, not execution evidence. For each runnable `SUCCEEDED` step
  the only executor is `execute_disconnected_fixture_tool` for fixed
  in-memory operations. A `FAILED` step and all `BLOCKED` descendants are
  omitted from even this mock invocation.
- Results are bounded canonical JSON with duplicate-key rejection, request/
  operation/input/result digest checks and denied external-authority flags.
  The domain-separated scenario fingerprint includes plan/schedule/projection
  identity, failure mask, terminal states and per-step mock-result digests.
- **38 authored parameterized pytest cases**. The first test CI exposed one
  incorrect assertion about wave order: an independent root step E executes
  before downstream C. The test assertion was fixed without reordering
  execution or changing source semantics.
- This does not use a real backend, issue a PermissionGate grant, record
  durable authorization, validate an external success, or authenticate an
  injected failure. It is not yet connected to the live Planner.

## 2. Read-only Memory expiry candidate preview

- Source: `src/ark/memory/expiry_candidate_preview.py`, blob
  `3b7021160929b41792e2ba9e98c7c00e0e6b7bd3`.
- Tests: `tests/test_memory_expiry_candidate_preview_run502.py`, blob
  `856d4410231d1f8f9cbb7cbd225777d9f3a70730`.
- Opens an existing `SQLiteMemoryStore` through its read-only connection,
  starts one SQLite read transaction, validates the frozen v1 schema and
  hydrates at most `limit + 1` due rows (limit 1..1000), ordered by
  `memory_id`. The extra row establishes `has_more`, so a partial page
  cannot be mistaken for complete purge eligibility.
- Checks scope and expiry eligibility at every row callback. The report
  contains only scope/row/page hashes and counts, not content or source IDs.
  A retained preview hash can be independently rechecked against a later
  read; a changed CAS revision or expiry causes rejection.
- **34 authored parameterized pytest cases**: equal-time expiry boundaries,
  owner isolation, pagination, no mutation, stale report after CAS update,
  invalid integer/boolean inputs, and denied deletion/consent/trusted-clock.
- The clock value is caller-supplied and **not attested**. No `purge_expired`,
  database write, deletion, live context access or privacy decision occurs.
  A matching preview is neither erasure proof nor permission to erase.

## 3. V3 pre-paid-compute local identity bundle check (isolated PR #5)

- Source: `src/ark/learning/identity_bundle_verify.py`, corrected blob
  `e3abcac3d170e3021135682724769324480312bd`.
- Tests: `tests/v3/test_identity_bundle_verify_run502.py`, blob
  `27007741e26f5ff09cf25e13761ff8e58c7c1a4c`.
- A bounded, lexically ordered set of up to eight pre-existing canonical JSON
  files is checked against **independently supplied per-file SHA-256 pins**
  through the existing read-only identity verifier. Each file is verified
  twice to detect common non-atomic replacement during the scan. Labels,
  hashes, top-level key sets and byte counts form a domain-separated bundle
  fingerprint; the verifier can require a separately retained root digest.
- **31 authored parameterized pytest cases**: replacement between passes,
  labels, alias/duplicate rejection, invalid paths and pin types, tampered
  root/receipt, and denied training/Candidate/evaluation authority.
- A first CI reported Ruff B007 (unused loop variable `name`); corrected to
  `_` in an ordinary source update. No permission/guard semantics changed.
- This **does not** inspect remote Hub identities, verify model weights,
  establish upstream data rights, authorize external GPU use or produce any
  Candidate. Multiple local file reads are not an atomic OS snapshot.

## Exact-head CI / known failures

- Previous Run501 source/test and documentation matrices on PR #8:
  `41194150033`, `41194245215`, `41194404044`,
  `41194501319` — all **6/6 GREEN** by job-level verification.
- Initial PR #8 Run502 fixture CI `41197996397`: **FAIL** on one expected
  wave-order test, which was corrected by commit
  `b10794bf0d1d55e4049f19d6f3a6f6aa06ffd642`.
- Initial PR #5 Run502 bundle CI `41198206139`: **FAIL** Ruff B007,
  corrected by commit `bc6263e87415c40961d66e6de9ca89e89b495d21`.
- Corrected PR #5 run `41198490837`: **6/6 GREEN** (Windows/Ubuntu,
  Python 3.11–3.13), checked from all six job conclusions.
- Corrected PR #8 source/test CI `41198507228`: was **IN PROGRESS** at
  document composition; no all-GREEN claim until job-level confirmation.
- Independent local full pytest/Ruff was **not executed**: local
  `git ls-remote` failed due to `github.com` DNS resolution. CI is
  commit-scoped and should not be transferred to another HEAD.

## Frozen boundaries / integration decisions

No frozen v1 Memory or Agency contract changed. Their previously frozen blob
identities remain `b6e93821ecd69270a7634aceb20775dc36e9953c` and
`13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`. The V3 Contract blob
remains `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`.

**Next safe dependency order:** (a) exact-head PR #8 CI GREEN; (b) separate
fixture outcome from authenticated tool execution; (c) feed only approved and
trusted-clock-bound results into a durable audit-before-action/permission
boundary; (d) keep UNKNOWN WRITE quarantined across restart, with no automatic
replay; (e) design a dedicated user-approved and race-safe purge operation
later, without upgrading this read-only expiry preview into authorization.

PR #5 remains **Draft/unmerged** under its controlling gate. There was no
protected V2 final-evaluation opening, real adapter/Candidate generation,
external GPU, paid action, automatic promotion, main merge or live device read.
Overall JARVIS/V3 remains **NOT_PASSED**.
