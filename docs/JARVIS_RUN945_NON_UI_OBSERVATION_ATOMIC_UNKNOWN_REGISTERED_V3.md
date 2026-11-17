# ARK Run945 — disconnected observation validator custody and unknown-write prefix boundaries

**Scope:** Draft PR #8, non-UI, zero-new-paid-service synthetic foundations. No frozen contract or approval gate was changed. Work-basis checkpoint: `04781c26aa00ad74ae90bd59f3b33e6b1d9126fb` (Run944).

## Code and regression packages

1. **Observation metadata validator custody**: `bb903297cb7d7562ccb0d55089e4ab29f45d2f43` pins the import-original observations identity guard, digest guard and digest validator. The disconnected fixture now refuses their replacement before constructing a synthetic envelope, instead of delegating through mutable module bindings. This protects metadata preflight from a replacement Python callback and is *not* an interpreter sandbox or independent source attestation. The six-case regression file is `tests/test_disconnected_fixture_validator_identity_run945.py` at test/fix commits `c8533704c41ede00c26aa8cbee37036a5693cbba` and `b00fad2f990ea9bd013f27d18ac8607d567b33d1`. The second commit positions its reentrant fault injection **after** the real safe preflight so it tests the post-preflight guard rather than injecting an executable callback prematurely. No raw sensor input is used.
2. **Atomic intent retained-prefix triage**: `260959995f21cb4fdedd04f1a9de9ee54c3a7329` adds 12 cases covering every local outcome classification across genesis/one-commit/two-commit retained witnesses, plus refusal of three changed retained tips. Two SQLite commits are local history, not external action evidence, trust, cross-store atomicity, or authorization to retry.
3. **Registry-bound WRITE continuity**: `a63c7a87aaa8245c0be2af474abd271959ce876d` adds four regression cases for changed registered backend version, scope, request body and a valid capability grant on WRITE. The same occurrence may not be reinterpreted as a different bound action, and a valid capability grant alone never dispatches a WRITE. The fault backend raises if called; no real backend is run.
4. **V3 synthetic packet cold-process mismatch**: `2cd795805939d3d10887f628d5ce0bec1b48e110` adds seven cases where structurally valid and *canonical* JSON still carries contradictory device, capacity, tokenizer probe, VRAM measurement, wall-time or precision-loss data. The exact bytes are rechecked in a detached Python interpreter and fail closed. No Candidate/GPU/paid compute/training/protected evaluation/promotion occurs.

**Total: 29 new authored pytest parameter instances** (6 + 12 + 4 + 7), plus one source hardening. Authored is not a test PASS claim. Normal Contents writes were used for every source/test change, with exact branch HEAD re-read immediately before writes. No force pushes, low-level Git-object updates, UI updates or main merges.

## Dependency and authority boundary

- A local `ObservationEnvelope` content hash plus schema validation does not authenticate a device, user, actual time or consent. The optional disconnected adapter refuses altered metadata-validator bindings before reading private fixture labels, but cannot claim trust against a malicious Python runtime.
- A locally committed `AtomicIntentClaim` and an `AtomicUnknownOutcomeReview` row classification are **never** evidence that an external tool did or did not run. Ambiguous outcomes remain manual quarantine; no automatic retry.
- A registered `BoundAction` identity and a capability grant do not replace one-shot WRITE authorization or the trusted-clock audit-before-action gate. Changed occurrence/action binding is refused, not reconciled into an executable approval.
- A synthetic V3 packet passing exact canonical byte and cross-binding checks is never authenticated runtime provenance, cost approval, training approval, protected V2 evaluation access or Candidate promotion.
- The independent lower-level GREEN gate must precede any later integration. PR #5 Draft/unmerged, PR #9 paused/Draft/unmerged, V1/V2 and Local UI/Launcher freezes unchanged.

## Verification and next plan

At invocation start, Run944 checkpoint `04781c26aa00ad74ae90bd59f3b33e6b1d9126fb` CI [#44097401425](https://github.com/Iam-2squared/ark-ai/actions/runs/44097401425) was **COMPLETED GREEN 6/6**. This is *only* the previous HEAD; do not reuse it as new code evidence. Run945 source and per-package CI checks were running or queued at latest in-session checks. CI on the ultimate checkpoint HEAD must be evaluated separately.

Next: (1) resolve exact latest HEAD Windows/Ubuntu × Python 3.11–3.13 CI; (2) if a new test fails, inspect its actual job log and correct only the minimal faulty fixture semantics; (3) tighten Memory WAL/SHM last-close/CAS and Planner COMMIT-UNKNOWN recovery; (4) build only reversible, disconnected integration after lower-level GREEN; (5) keep all paid/real-execution/protected/frozen lanes blocked pending explicit consent. Overall ARK/JARVIS remains **NOT_PASSED**.
