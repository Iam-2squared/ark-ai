# Run790 — exact scalar recovery, bounded private retention and DAG terminal oracle

**Saved report authoring at:** 2026-11-11T10:50:21.495Z UTC (local JST: 2026-11-11 19:50:21).
**Initial work-basis HEAD:** `a9daf09086102635b9771e8cccfc2446f80593c0` on
`research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8).
The basis [CI #42998644954](https://github.com/Iam-2squared/ark-ai/actions/runs/42998644954)
was read directly: **all six Windows/Ubuntu × Python 3.11–3.13 jobs completed GREEN**.
That result is the prior baseline, not proof of Run790's new code.

## Work package A — synthetic atomic recovery witness custody

- Source [`disconnected_atomic_recovery_quarantine.py`](../src/ark/agency/disconnected_atomic_recovery_quarantine.py)
  at commit `6139b6ff0b7779491eed15b4d9b0cfa50dc15116`:
  retained count/tip are captured with the ledger's exact-scalar witness validator
  **before** registry derivation; rechecked across SQLite inspection, denied-authority
  getters, and result construction. No patchable dataclass `__eq__` is used
  for witness continuity. The original witness descriptors and validator
  callback are pinned before private inspection; the final deny-only result
  is verified after construction.
- Regression [`test_atomic_recovery_scalar_witness_run790.py`](../tests/test_atomic_recovery_scalar_witness_run790.py)
  at `1fc038d57395c7ac3687b1d3b322338f914bb4bc`:
  **two** recorded/unrecorded cases with a poisoned witness equality hook,
  **three** pre-SQLite control-plane substitution cases. The ledger remains
  disconnected, digest-only and manual-review-only.
- [CI #43006091566](https://github.com/Iam-2squared/ark-ai/actions/runs/43006091566)
  was **IN PROGRESS** at last read; Ubuntu **3/3 GREEN**, Windows still executing.

## Work package B — cached retention inventory admission

- Source [`personal_context_retention_recheck_review.py`](../src/ark/personal_context_retention_recheck_review.py)
  at `7582e2aafdac82cead23c6e09b4b747bd7fc3a05`:
  exact private-inventory scalar types, lowercase scope/inventory digest grammar,
  SQLite-range observation time, revoked boolean and an **at-most-1000-item**
  budget are now required before any Memory/revocation SQL review.
  Nested item revision is bounded to positive SQLite range. This keeps a
  reflectively malformed cached receipt from triggering unbounded inventory
  traversal or private storage access.
- Regression [`test_context_retention_cached_shape_run790.py`](../tests/test_context_retention_cached_shape_run790.py)
  at `98ae6c745efe05be918fdce1a943c8c2737281fb`:
  **six** malformed/oversized cached-receipt cases and **one** positive
  synthetic expiry review. A fixture-only retention diagnostic never
  authorizes deletion, disclosure or Memory mutation.
- [CI #43006329359](https://github.com/Iam-2squared/ark-ai/actions/runs/43006329359)
  was **QUEUED/STARTING** at last read. No 6/6 claim is made.

## Work package C — exhaustive disconnected Planner propagation

- [`test_disconnected_terminal_dag_oracle_run790.py`](../tests/test_disconnected_terminal_dag_oracle_run790.py),
  saved at `d8effc055524762199c5f134fd28e76973ca0d15`, contains an
  independent sequential dependency oracle over **four five-step DAG shapes**
  and **all 32 failure subsets each (128 cases)**. It asserts the correct
  terminal state for reachable synthetic failures and rejects declarations
  that a blocked descendant also executed/failed. Valid outcomes are verified
  by the independent detached receipt verifier and remain False-only for
  dispatch, WRITE, replay, and authenticated failure.
- [CI #43006552878](https://github.com/Iam-2squared/ark-ai/actions/runs/43006552878)
  was **QUEUED** at last read. This is fixture-only and does not run a tool.

**Combined submitted regression cases:** 5 + 7 + 128 = **140**.
These are *submitted cases*, **not** an asserted completed CI pass.
No local pytest or Ruff result is claimed in the connector-only environment.
After the exact-head individual jobs report, the next package may use their
actual logs to correct only verified failures.

## Current barriers and next integration order

1. Revisit the exact-head source/test runs, inspect individual six-job outcomes
   and the newest checkpoint HEAD; if FAIL, use the smallest semantics-preserving
   normal Contents API change and work in another non-UI module while it runs.
2. Memory: coherent cross-owner events, generation CAS/ABA and manual-only
   COMMIT-UNKNOWN receipt custody. No automatic unknown-WRITE replay.
3. Planner and Action: terminal persistence, exact authority from immutable
   ToolRegistry, restart-safe one-shot claims, trusted-clock
   **audit-before-action** and only a disconnected mock executor once every
   prerequisite is exact-head GREEN.
4. Privacy/Proactive/Observation: source/field custody, expiry/revocation,
   occurrence replay fences and in-memory fixture-only observations.
5. V3: free reproducibility, path/identity and approval-artifact guards,
   **without** paid compute or protected V2 evaluation.

**Limitations:** local SHA-256, internal SQLite receipts and Python descriptor
checks are not independent authentication or a security sandbox. Cross-store
read-only observations are not globally atomic. No human approval, consent
issuer, live side effects, model loading or training success was established.

**Unchanged boundaries:** frozen V1/V2/Local UI/Launcher contracts, protected
V2 evaluation, V3 Contract 1 and all frozen evidence; Draft PR #5 remains
unmerged under pre-paid-compute approval, Draft PR #9 remains untouched and
new UI/frontend development is paused. No billable APIs, GPUs, credentials,
new accounts, destructive operations, physical-PC actions, Candidate
generation/promotion, real tool dispatch or main merge occurred.
**ARK / JARVIS / V3: NOT_PASSED.**
