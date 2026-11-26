# ARK AI — Run809 Non-UI Protocol Custody / 2026-11-12 JST

This is **FREE-ONLY, disconnected, non-authorizing hardening** on Draft PR #8.
It does not certify local executable safety against a malicious interpreter,
authenticate provenance or a human decision, authorize deletion/replay, or change
frozen V1/V2/Local UI/Launcher contracts. **JARVIS remains NOT_PASSED.**

## Verified work basis

- Initial PR #8 head: `b96703d3c34d84db69343449ff859104657c85f3`.
- Prior complete six-job CI: [#43151742187](https://github.com/Iam-2squared/ark-ai/actions/runs/43151742187), Windows and Ubuntu / Python 3.11–3.13, **6/6 GREEN**, independently verified from all job conclusions before these changes.
- This run changes only **three non-UI source modules** and matching dedicated
  regression tests on `research/jarvis-foundations` (seven normal Contents API
  commits including a focused test correction). No frozen/UI files are touched.

## Package 1 — Memory expiry receipt protocol custody

- Source `src/ark/memory/expiry_cohort_review.py`:
  `650ef0972d09ede3bb407a1d53f7cb0eb0ac49fa`.
- Test `tests/test_memory_expiry_cohort_protocol_run809.py`:
  `fef8a62dd81f10285e684107bc331f9982cdea0a`.
- **18 submitted cases** pin the exact SHA pattern, hash domain, finite scalar
  budgets, imported carrier classes and lookup hooks before reading opaque
  synthetic expiry receipts. Tampered receipt descriptors are refused before
  their getters run; valid reports still deny deletion and clock attestation.
- This does not inspect real memory data, prove cross-scope atomicity, authorize
  a purge, or certify independent retained scope inventory.

## Package 2 — Planner dependency-quarantine protocol custody

- Source `src/ark/agency/disconnected_dependency_quarantine_projection.py`:
  `e7877d36dbcd8d85465ef09c20553d7d868d5de0`.
- Test `tests/test_disconnected_dependency_protocol_run809.py`:
  `29a6250e2d193bf8ce2c368f5ee16038a677c4a0`, corrected fixture commit
  `2c37f1fc3e72204c597a932393caebf7188e2485`.
- **20 submitted cases** cover substituted DAG/ID/limit domains, result and
  input descriptors, imported effects, matrix bridge and heap callbacks, plus
  the normal transitive WRITE-ancestor hold. No returned disposition can
  authorize dispatch, replay, or independently verified external outcomes.
- The initial Ubuntu 3.12 CI [#43156958681](https://github.com/Iam-2squared/ark-ai/actions/runs/43156958681),
  job `130978999276`, reported **three fixture-construction failures**:
  the new test generated input claims *after* replacing the very class/slot
  it intended to test. The correction constructs claims before monkeypatch,
  keeps production invariants unchanged, and explicitly removes artificial
  inherited `__getattribute__` hooks in cleanup. This initial FAIL is not
  hidden or treated as a successful production verification.

## Package 3 — Proposal COMMIT-UNKNOWN tip helper custody

- Source `src/ark/agency/disconnected_proposal_unknown_commit_review.py`:
  `8f23e9e290fe8eaa88362be48f92c75e3c5ce16b`.
- Test `tests/test_disconnected_proposal_tip_helper_custody_run809.py`:
  `40b4f4caae63a0995758862a3311c9d9d52e70df`.
- **5 submitted cases** reject replacement of the local tip-field projector
  before it can reinterpret a proposed CAS as an exact post-commit append.
  An unchanged proposal is still reported `OBSERVED_UNCHANGED` without retry
  authority. Read-only triage never writes to SQLite, executes tools or infers
  human approval from a local hash.

## CI and compatibility gate

- A test-bearing Memory head `fef8a62d...`, run
  [#43156855149](https://github.com/Iam-2squared/ark-ai/actions/runs/43156855149),
  had Ubuntu 3.11/3.12/3.13 GREEN at latest per-job observation; Windows still
  **IN PROGRESS**. This is not whole-head GREEN.
- The first Planner test-bearing run `29a6250e...`, run
  [#43156958681](https://github.com/Iam-2squared/ark-ai/actions/runs/43156958681),
  had a concrete test-fixture failure (3 cases; 13,910 passed in Ubuntu 3.12).
  Its correction awaits exact-head CI.
- Proposal source/test and corrected Planner test commits have their own
  automatically triggered workflows. At this report preparation, the final
  exact-head six-job GREEN is **NOT VERIFIED**. No duplicate workflow rerun was requested.
- No local checkout or full local `pytest`/`ruff`, model inference, GPU,
  physical-device gate, real approval/candidate, protected V2 evaluation or
  end-to-end live tool integration was performed in this run.

## Next review gate

1. Inspect all six jobs at the final checkpoint-result HEAD; retain true CI
   failures and repair only identified issues using normal source/test writes.
2. Once the lower-level exact-head gates are GREEN, strengthen Memory
   CAS/ABA and expiry snapshot readback, Planner restart UNKNOWN isolation,
   and registry-bound audit-before-action through disconnected mock execution.
3. Keep Draft PR #5 protected, Draft PR #9 and all UI work paused, and
   frozen evidence unchanged. No main merge or billable service.
