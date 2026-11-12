# ARK AI Run820 — atomic ledger epoch custody and cross-domain manual quarantine

## Baseline and scope

**Work-basis HEAD:** `204a81f58c2238ba98810bf6c3123f96a90fd483` (Run819 checkpoint). Existing [CI #43223842934](https://github.com/Iam-2squared/ark-ai/actions/runs/43223842934) was independently read as **GREEN, all six** Windows/Ubuntu Python 3.11–3.13 jobs. [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8) remains isolated and unmerged. Two compatible NON-UI, FREE-ONLY work packages and **27 newly authored parametrized/standalone test cases** are included. The new tests are not automatically PASS evidence.

### Package A — Atomic preaction UNKNOWN: per-instance and connection epoch

**Source:** `src/ark/agency/disconnected_atomic_unknown_outcome_review.py` at commit `c7d756b03ab8ba63b0d8f9a0015d255e08efa871`. **Tests:** `tests/test_atomic_unknown_ledger_epoch_run820.py` at `66d22466afef3c2fb07944a8a4c35e8cf2041759` (**6** cases).

The earlier reviewer pinned the *class* `_open` but invoked `ledger._open` on a mutable instance. An instance-shadowed method could replace the read-only SQLite connection while bypassing that class check. Now the single expected instance field (`_path`) and its object identity are pinned before input validation and rechecked after the SQL connection starts, after the scan and before the result. The reviewer invokes the original class method directly, and also refuses class-level lookup-hook replacement. Tests cover the normal inert `UNCHANGED` case, a shadowed `_open`, a foreign instance field, a late path rebind during `sqlite3.connect`, late method shadowing, and a replaced class `__getattribute__` before malicious code runs.

**Residual:** an already-modified path before the first read has no independent provenance attestation. The opened SQLite epoch is only local; it does not authenticate a writer, consent, an external tool effect, or a once-only action. No automatic retry.

### Package B — Detached Memory + Planner + preaction quarantine inventory

**New source:** `src/ark/agency/disconnected_recovery_quarantine_inventory.py` at `a9a2cfac3d66fe8519d0db2d565ed950e81e73b9`, Ruff import-order correction `54d5d9d7764b69ee1de96c5783c0a294708f7388`. **New tests:** `tests/test_recovery_quarantine_inventory_run820.py` at `0958b950908a6d078dd67fb8bc2d8430f0db045b`, import-order correction `c5f9d61dba3c8a9974e48a20c20d2a854ef0fa4e` (**21** parametrized/standalone cases).

This new optional, strictly disconnected composition checks exact immutable dataclass carrier definitions and deny-only authorities from three existing lower-layer local reviewers:

- `MemoryAmbiguityPair`: recompute its original local reconciliation hash, require an allowed disposition and SHA-256 evidence shapes.
- `DisconnectedPlannerSlotBridge`: recompute the original bridge digest; enforce ordered bounded step/UNKNOWN inventories and valid reserved count.
- `AtomicUnknownOutcomeReview`: validate bounded, sorted, unique occurrence IDs and internally consistent `UNCHANGED`, `LOCALLY_RECORDED`, `PREEXISTING`, `ADVANCED_OTHER` state/count/presence combinations.

The resulting local diagnostic is `MANUAL_REVIEW_REQUIRED` or `QUARANTINED`, **never READY**. It publishes only plan identity, change category, bounded counts and a domain-separated digest. Consent, replay, external effects, trusted clock, authenticated custody and cross-store atomicity remain explicitly False. It opens no database and performs no tool call. Recomputed local hashes do not authenticate adversarial historical inputs.

### Validation and CI at report preparation

- Previous Run819 checkpoint `204a81f58c2238ba98810bf6c3123f96a90fd483`: [#43223842934](https://github.com/Iam-2squared/ark-ai/actions/runs/43223842934) **GREEN 6/6**.
- Package A test HEAD `66d22466afef3c2fb07944a8a4c35e8cf2041759`: [#43230577779](https://github.com/Iam-2squared/ark-ai/actions/runs/43230577779) had Ubuntu 3.11, 3.12, 3.13 **GREEN** and Windows **IN PROGRESS** at last read.
- Package B initial source [#43231034047](https://github.com/Iam-2squared/ark-ai/actions/runs/43231034047) and test [#43231195238](https://github.com/Iam-2squared/ark-ai/actions/runs/43231195238) **FAIL** on Ruff I001 import ordering; actual Ubuntu job logs inspected. The only changes in follow-up corrections were import moves. Final revised source/test HEAD `c5f9d61dba3c8a9974e48a20c20d2a854ef0fa4e` [#43231449304](https://github.com/Iam-2squared/ark-ai/actions/runs/43231449304) was **QUEUED** at the last check. **No GREEN claim for final HEAD yet.**
- No local full checkout, local pytest/Ruff, physical-PC GGUF execution, external GPU, paid API, duplicate workflow dispatch, destructive operation or live executor operation is claimed.

## Boundaries and next plan / 今後の方針

Keep PR #5 Draft/unmerged and its protected evaluation/Candidate gates untouched; keep Draft PR #9 untouched and all new UI/frontend PAUSED; preserve frozen V1/V2/Local UI/Launcher contracts and historical evidence. Do not merge PR #8 without required approval.

1. Verify all six exact-head CI jobs for corrected package A and B; on failure use actual logs, smallest semantics-preserving fix, and independent work while new CI runs.
2. Extend Memory CAS/ABA/COMMIT-UNKNOWN source/read-session custody and durable Planner UNKNOWN quarantine without permitting automatic replay or deletion.
3. Connect the new diagnostic inventory to restart readiness only after lower-layer exact-head GREEN and independent contract review. It is **not** an approval, trusted clock, or atomic cross-store witness.
4. Continue privacy-safe Personal Context, proactive/scheduler restart and observation fixture backends with only free, reversible and disconnected work.

**ARK/JARVIS overall: NOT_PASSED.**
