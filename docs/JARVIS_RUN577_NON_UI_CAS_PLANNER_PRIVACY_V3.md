# ARK JARVIS Run577 — non-UI source integrity and recovery boundaries

Status: **Draft, NOT_PASSED.** Read this as an exact-source evidence note, not an
approval, external action, training result, or official phase gate. Work basis:
PR #8 `7afc6d12770f49e59c2d52785eedd0d1bf940dbd` and PR #5
`d829170436894eb592677d4cd8a96268bb90e4ce`. All changes are on
isolated Draft branches and were submitted via normal GitHub Contents API.

## Implementation packages

1. **Memory CAS token descriptor custody.** In
   `src/ark/memory/generation_fenced_cas.py`, the original
   `MemoryGenerationCASToken` denied-authority class descriptors are pinned
   at module import. Observation refuses a substituted false-only property
   before the SQLite read. The opt-in generation-fenced writer refuses it
   before opening the WRITE transaction and checks it at subsequent callback
   boundaries. A retained token remains a local CAS observation, not
   authenticated consent, external effect authority, or a retry permit.
   `tests/test_memory_cas_original_token_authority_run577.py` has
   **5 authored cases** (4 rejected preinstalled swaps across both paths,
   1 intact-generation CAS control).
2. **Planner journal source identity and restart recovery.** In
   `src/ark/agency/planner_journal_review.py`, the original concrete Path
   carrier is retained on construction and validated prior to recovery,
   append, or re-opening SQLite. Equal-valued path replacement and Path
   subclasses with custom `__fspath__` are rejected; no backend dispatch
   occurs. `tests/test_planner_journal_path_epoch_run577.py` has
   **6 authored cases** (malicious path, four retarget combinations,
   intact FAILED root / BLOCKED dependent recovered after restart).
   The observed pre-correction CI failed an inherited test expecting
   `must be a Path` when the new identity check rejected first; the
   original diagnostic was restored for wrong-type paths without removing
   the equal-carrier identity fence at commit
   `5c48264d976ceaa94f824703f0e4aa73cf3e1188`.
3. **Privacy veto report last-callback custody.** In
   `src/ark/offline_attention_revocation_review.py`, the synthetic
   revocation/attention result fields are independently rechecked after
   *each* False-valued denial getter, including the last; checking only
   original inputs after an overridable getter could otherwise return a
   reflectively altered receipt. `tests/test_attention_revocation_last_denial_run577.py`
   includes **4 authored cases** (three reentrant report mutations and
   one intact non-authorizing review). This does not create real notification
   permission or atomic consent/revocation verification.
4. **Unapproved V3 passive shape oracle identity.** On PR #5,
   `src/ark/learning/offline_readiness_transition.py` pins both the
   independent and child-review `_plausible_shape` functions at import
   and rechecks them around caller-controlled snapshot callbacks.
   `tests/v3/test_passive_shape_oracle_original_run577.py` adds
   **4 authored cases** for preinstalled replacements, a mid-review
   replacement, and inert local-template behavior. Initial tests hit an
   observed Ruff I001 import grouping failure, corrected in two narrow
   test-only edits; no security predicate was relaxed.

**Total: 19 newly authored pytest cases**, not a statement of locally
executed PASS. GitHub Actions, when GREEN, validate their own exact
branch HEAD only; later source or checkpoint commits require their own CI.
The code here is local-first, non-UI, and reversible.

## Verification and safety boundaries

- Prior exact-head PR #8
  [#41606353491](https://github.com/Iam-2squared/ark-ai/actions/runs/41606353491)
  and PR #5
  [#41606170447](https://github.com/Iam-2squared/ark-ai/actions/runs/41606170447)
  each completed **6/6 GREEN**, but precede this work.
- PR #8 intermediate test HEAD
  [#41613348987](https://github.com/Iam-2squared/ark-ai/actions/runs/41613348987)
  completed **6/6 GREEN** for the isolated Memory patch. The earlier
  Planner path-test run
  [#41613634992](https://github.com/Iam-2squared/ark-ai/actions/runs/41613634992)
  exposed one inherited error-text expectation (Ubuntu 3.13: 7,515 PASS,
  1 SKIP, 1 FAIL); corrected at `5c48264...`. Later
  [#41614027859](https://github.com/Iam-2squared/ark-ai/actions/runs/41614027859)
  validates that correction. The new privacy source/test run
  [#41614527651](https://github.com/Iam-2squared/ark-ai/actions/runs/41614527651)
  still needs exact-head verification.
- PR #5 source-only
  [#41613863558](https://github.com/Iam-2squared/ark-ai/actions/runs/41613863558)
  completed **6/6 GREEN**; test runs
  [#41613916835](https://github.com/Iam-2squared/ark-ai/actions/runs/41613916835)
  and
  [#41614361408](https://github.com/Iam-2squared/ark-ai/actions/runs/41614361408)
  both failed on observed Ruff I001 import formatting; latest exact
  test-only import correction at `1a83b171117443ea849e5cefbfafd7741426e747`
  is under
  [#41614606829](https://github.com/Iam-2squared/ark-ai/actions/runs/41614606829),
  pending at note composition. No V3 training, snapshot approval,
  protected V2 opening or Candidate generation.
- Frozen source hashes remain: Memory contract
  `b6e93821ecd69270a7634aceb20775dc36e9953c`;
  Planner contract `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`;
  V3 contract `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`.
  Existing V1/V2/Local UI/Launcher freezes were not changed.
- No paid/billable compute or external API, external GPU, new accounts,
  secrets, physical PC operation, live capture/notification, real ToolBackend
  action, protected evaluation, Candidate, irreversible mutation, or main
  merge. PR #5/#8 are Draft. Completed UI PR #9 stays **Draft, untouched,
  and UI/FRONTEND DEVELOPMENT IS PAUSED**.
- Internal SHA-256 reports and caller-supplied clocks do not authenticate
  a real writer, human approval, trusted time, genuine privacy consent,
  independent custody, or cross-database atomicity. Ambiguous COMMIT /
  UNKNOWN WRITE cannot be auto-replayed.

## Next plan / 今後の方針

1. Inspect exact latest PR #8/#5 six-job CI, correct observed failures
   without weakening safety predicates, and keep independent non-UI CI
   lanes productive without duplicate workflow launches.
2. Extend Memory generation CAS, expiry/erasure/revocation, and
   uncertain-COMMIT retained multi-observer proofs in isolated free fixtures.
3. Extend Planner FAILED/BLOCKED restart recovery, Registered READ evidence,
   ToolRegistry/PermissionGate and durable occurrence/audit-before-action
   under disconnected/mock executors only.
4. Continue privacy-safe Personal Context, scheduler replay prevention,
   observation fixtures, and free-only V3 identities/reproducibility.
   Preserve every frozen contract and protected gate; JARVIS is NOT_PASSED.
