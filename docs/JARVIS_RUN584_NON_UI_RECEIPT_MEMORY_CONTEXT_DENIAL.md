# Run584 — synthetic occurrence receipts, Memory CAS witness and privacy-bound context

**Scope:** local-first, free-only NON-UI ARK foundations. No external ToolBackend
execution, consent or issuer authentication, user-device action, paid compute,
model training, Candidate generation or V2 protected evaluation. This report
documents implementation and authored tests, **not** full-system PASS.

## Package 1 — inert durable occurrence receipts

- Source commit: `6858b7a7619f04144647338588f3758f83715851`
  (`src/ark/agency/durable_occurrence_review.py`).
- Test commit: `450b96eabe201a979a00619cbf3be3e5f3b74f79`
  (`tests/test_occurrence_receipt_authority_run584.py`, **10** pytest cases).
- Pins three original receipt property descriptors at import time. A
  preinstalled True/False replacement is refused before a synthetic reservation.
  Post-commit property mutation is denied, while the durable one-shot reservation
  stays spent and no backend is called. Reviews every denial getter and rechecks
  the original receipt fields to prevent reentrant report retargeting.
- No claim of actual tool permission, authenticated token issuer, or exactly-once
  external execution. Rejection after COMMIT is **not** a rollback or retry grant.

## Package 2 — exact retained Memory generation witness

- Source commit: `7a7361cc3af9d0d1a3fc2775095a90498f193edd`
  (`src/ark/memory/generation_cas_outcome_review.py`).
- Tests: `e87809fa5e84ef8878be2785e23e24bc6a528056`;
  fail-closed diagnostic expectation corrected at
  `05f812145f8a70c45aacc03c6ef85341d3bf70b1`
  (`tests/test_memory_cas_retained_carrier_run584.py`, **13** cases).
- The read-only COMMIT-UNKNOWN reviewer now compares every retained witness
  field by original Python object identity as well as validating its canonical
  values. A callback cannot substitute an equal-value but newly allocated
  digest or Memory ID and have it accepted as the earlier observed carrier.
  Negative tests cover four read snapshots and three retained string fields.
- Snapshot failures can be intentionally wrapped as an unavailable-generation
  manual-triage error. No automatic retry, commit attribution, clock trust,
  privacy consent, store migration, or frozen Memory v1 change.

## Package 3 — original Personal Context denial descriptors

- Source commit: `d6229a167ab6635b5248e996d4a1e2ea62e341d8`
  (`src/ark/personal_context_request_binding.py`).
- Test commit: `9e4131d69d0c9667532641c1d682535b9dca7ea8`
  (`tests/test_context_binding_original_denials_run584.py`, **10** cases).
- Import-time pins all preview and request-binding False-only authority
  descriptors, instead of accepting the first callable's dynamic replacements.
  The original descriptors are verified at entry and through result review.
  Checks reject preinstalled replacements even when they still return False.
- This is limited to local synthetic fixtures. A hash, request ID and
  deny-only receipt do not prove fresh revocation, consent, retention permission,
  external export or notification authority.

## Evidence and controls

- **Previous PR #8 exact checkpoint HEAD**
  `168ebd360679e2ddf3c565c5de5f098f43e7f19a`,
  [Actions #41653887845](https://github.com/Iam-2squared/ark-ai/actions/runs/41653887845):
  **6/6 GREEN**, Ubuntu/Windows Python 3.11–3.13. This result predates
  all Run584 source/test changes and is not evidence of their CI success.
- Run584 automatic CI includes
  [occurrence source #41657584493](https://github.com/Iam-2squared/ark-ai/actions/runs/41657584493),
  [Memory source #41657689834](https://github.com/Iam-2squared/ark-ai/actions/runs/41657689834),
  [occurrence tests #41657900026](https://github.com/Iam-2squared/ark-ai/actions/runs/41657900026),
  [Memory tests #41658002206](https://github.com/Iam-2squared/ark-ai/actions/runs/41658002206),
  [privacy source #41658177092](https://github.com/Iam-2squared/ark-ai/actions/runs/41658177092),
  [privacy tests #41658267180](https://github.com/Iam-2squared/ark-ai/actions/runs/41658267180).
  Several were still running or queued at last observation. The Memory test
  expectation correction triggers separate automatic CI, not a manual rerun.
  **Do not claim latest exact-HEAD six-job GREEN until independently verified.**
- **33** is the number of authored pytest cases (10+13+10), not successful
  local execution or physical-PC GGUF evidence. Source/test changes were made
  through normal GitHub Contents API, with the branch HEAD re-read before each.
- Frozen PR #8 Memory contract
  `b6e93821ecd69270a7634aceb20775dc36e9953c` and Planner contract
  `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9` unchanged;
  PR #5 V3 contract
  `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23` unchanged.
  PR #9 UI remains untouched, Draft/unmerged.
- There is no genuine release readiness, authenticated history custodian,
  external exactly-once effect, human approval, trusted clock or
  authoritative privacy consent. **ARK/JARVIS/V3 NOT_PASSED.**

## Next / 今後の方針

1. Obtain exact HEAD CI for the three packages (and fix only actual failed
   semantics-preserving assertions/formatting through normal safe writes).
2. Strengthen registry-bound exact PermissionGate + audit-before-action
   durable occurrence linkage without enabling backend dispatch.
3. Continue Memory generation/expiry/revocation and COMMIT-UNKNOWN manual-only
   evidence, Planner FAILED/BLOCKED persistence, Personal Context withdrawal.
4. Then Scheduler replay quarantine and Observation offline fixture contracts.
   V3 free-only identity/provenance review remains isolated; no protected V2
   opening, real weights, paid compute, Candidate promotion or UI work.
