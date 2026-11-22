# Run1128 — startup readiness lease helper custody

**Status:** isolated, non-UI research package; fresh exact-head CI required.  
**Base:** Draft PR #8 work-basis HEAD `c336f9ba5e7c08bc1f1715073def7c92607d8ef1`.  
**Branch:** `research/run1128-startup-lease-helper-custody`.

## Finding

The disconnected startup lease reviewer pinned its requirement/result class descriptors and the tuple that carried their original descriptor vectors. However, the module-level verifier functions themselves were still reboundable. Replacing one verifier with a no-op could bypass the corresponding class check; replacing the protocol verifier together with an empty requirement descriptor vector could skip the vector check before a forged requirement descriptor was read.

## Change

- Capture the three import-original requirement, result, and protocol verifier functions in one immutable tuple.
- Retain that tuple in the review function's default argument and compare the live module globals with the captured function identities before using any verifier.
- Recheck the helper identities through the existing requirement, snapshot, and result epochs, including after reentrant snapshot-integrity callbacks.
- Keep the original protocol verifier as the callable used after identity admission; do not accept a caller-substituted no-op verifier.

## Regression coverage

The new synthetic tests cover:
- a valid fresh exact-component lease with all startup/dispatch/notification authority flags remaining false;
- lane-scoped behavior when an unrelated component is blocked;
- required-component BLOCKED, schema mismatch, duplicate requirements, expiry and clock-regression denial;
- replacement of each of the three module-level guard helpers with a no-op before a forged descriptor callback;
- helper replacement during a reentrant snapshot integrity callback.

## Boundaries

No SQLite schema, persisted row format, frozen V1/V2/Local UI/Launcher contract, V3 contract, Candidate state, evaluation gate, or real backend is changed. The lease remains a caller-clocked diagnostic only: it does not establish real machine readiness, trusted time, authenticated consent, dispatch authority, notification authority, or hardware access. This is an in-process dependency-identity guard, not a Python sandbox.

Fresh Windows/Linux × Python 3.11–3.13 CI on the exact PR head is required before any PASS statement. No local test run is claimed.
