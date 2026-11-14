# ARK AI Run767 — non-UI atomic callback, proactive path and observation ingress

**Work basis:** `b00648918b03b33022fafaed1d4d71b60e4eddcc` (Run766 checkpoint).
**Scope:** Draft PR #8, `research/jarvis-foundations`; free-only local fixtures, no UI.
**Completion claims:** source/test commits saved; exact final-HEAD full six CI GREEN **not yet established**.

## A. Atomic recovery binder/custody preaccess guard

Source commit `1e4c8b0475857948db30ff7a3175d2b0b7db7a1e` updates
`src/ark/agency/disconnected_atomic_binding_snapshot_review.py`.

- Captures import-original `derive_registered_atomic_intent` and
  `review_atomic_input_carriers` as immutable comparison witnesses.
- `_original_reader()` now refuses either substituted function *before*
  private registry, call, retained witness or SQLite inspection. The guard is
  repeated at the existing reentrant boundaries.
- Regression commit `615214fc543dfc88bc3af8327cf50c852f9bcb18` adds 2
  parameterized fail-closed callback substitution cases in
  `tests/test_atomic_binding_callback_originals_run767.py`.
- This protects an in-process reviewer, **not** authenticated source identity,
  external audit custody, consent, permission or exactly-once tool effects.
  All matching/absent/conflicting results remain quarantine-only.

## B. Synthetic proactive SQLite path ingress

Source commit `819803df184e85a0c3d6ee607a150653d998f009` updates
`src/ark/proactive_synthetic_review.py`:

- `SyntheticProactiveLedger.__init__` rejects executable `Path` subclasses
  before SQLite may call `__fspath__` and create a ledger.
- `prepare()` rejects a reflectively substituted subclass source before
  policy identity validation or the SQLite preparation boundary.
- Regression commit `66e6fe1da47dcdd0b1909089a65ed2af489ea00b`
  adds 3 cases (invalid construction, invalid preparation, normal exact
  `Path` bootstrap) in `tests/test_proactive_exact_sqlite_path_run767.py`.
- Exact Path type alone **does not** establish canonical filesystem custody,
  symlink-race freedom, authenticated time or notification authorization.
  No notifications were sent.

## C. Private observation label ingress / fixture-only tests

Test commit `7d93fe632294d1ac4996147889252d3c8b86610d`
adds `tests/test_observation_label_preaccess_run767.py`, 12 cases:

- Invalid source/privacy labels: embedded NUL, invalid UTF-8 surrogate,
  UTF-8 byte-budget overflow.
- The closed-chain reader must reject the caller label before accessing
  an intentionally uninitialized private envelope.
- The binary fixture adapter must reject the label before calling a replaced
  private-payload hash callback.
- Tests are synthetic bytes only; no camera, microphone, screen, media
  acquisition, model weights or personal data was used.

## Measured CI evidence and next gates

- Previous Run766 exact HEAD `b00648918b03b33022fafaed1d4d71b60e4eddcc`:
  GitHub Actions `#42829555412`, **6/6 success** (Ubuntu and Windows,
  Python 3.11/3.12/3.13). It is **not** Run767 evidence.
- A source `#42837476616`: Ubuntu 3/3 GREEN, Windows 3 still in progress
  at the 23:50 JST sample.
- B source `#42837626966`: Ubuntu 3.11 GREEN, remaining five in progress
  at the 23:50 JST sample.
- C tests `#42837942342`: in progress at the same sample.
- A tests `#42838089589`: in progress at the same sample.
- B tests `#42838176503`: queued at the same sample.
- The forthcoming report/checkpoint commits each trigger their own CI;
  do not claim success before exact HEAD and six job conclusions agree.
  No duplicate workflows were dispatched.

## Immutable and free-only boundaries

- `main`, frozen V1/V2/Local UI/Launcher contracts/evidence untouched.
- Draft PR #5 (V3 protected gate), Draft PR #8, and paused Draft PR #9
  remain Draft/unmerged. No frontend/UI work.
- No paid GPU/compute/API, Candidate creation, protected final evaluation,
  real ToolBackend action, credentials, external account connection, physical
  machine operation, irreversible mutation, promotion or main merge.
- Distinct Memory, Planner, authorization, audit, privacy, proactive databases
  have no cross-store atomicity. **An ambiguous real WRITE remains UNKNOWN
  and manually quarantined; never auto-retry**.
- Re-check exact final-HEAD CI, then advance Memory retained-CAS/highwater,
  Planner crash/recovery, and registry-bound audit-before-action only on
  independent GREEN foundations. Fail closed at all payment/approval gates.

## D. Proactive startup metadata helper identity

Source commit `5e0594fce26a6b0938145aee68b4e11d9d4d7794` updates
`src/ark/proactive_startup_fence_review.py`.

- Pin import-time `dataclasses.fields`, `_epoch`, and `_snapshot_epoch`
  implementations. A replaced metadata reader could access trigger receipts,
  policy identities or readiness components before the deny-only review.
- Extend the preaccess original-definition check and its existing reentrant
  rechecks to refuse these helper replacements without invoking them.
- Test commit `d4c7f931f4123309178e4e5b7c43fc5203969999` adds
  3 parameterized cases with intentionally unreadable private carriers.
- These are synthetic readiness claims, not startup/notification approval.

**D CI:** Source `#42838865493`, tests `#42838961935`, both queued
at the 23:55 JST sample. The preceding report commit `e6fd3ce2...`
has `#42838555084` queued. Exact final-HEAD 6/6 GREEN remains unverified.

**Run767 totals:** 4 coherent non-UI packages; 3 source files changed,
4 new test files, 20 parameterized regression cases, one technical report
and one canonical checkpoint scheduled at the end of the invocation.
