# ARK AI — Run690 / non-UI core evidence

**Scope:** Draft PR #8 `research/jarvis-foundations`, free-only, disconnected fixtures, no UI/frontend changes, no real tool execution, no paid services, no protected V2 evaluation, no Candidate materialization or promotion. All work is isolated from `main` and frozen V1/V2/Local UI/Launcher contracts.

**Work-basis HEAD:** `0c28339a04723a8bc6de97b21de445d194064aa8` (Run689 canonical checkpoint). Incoming Run689 exact-head [CI #42388979329](https://github.com/Iam-2squared/ark-ai/actions/runs/42388979329) completed all **six Windows/Ubuntu × Python 3.11–3.13 jobs GREEN**, independently confirmed before this work. This is NOT Run690's CI verdict.

## A — Memory generation CAS non-UTF-8 rejection (production + 6 tests)

- Production module `src/ark/memory/generation_fenced_cas.py` modified by commit `b5205cf905b890f0b0f54c9b9bc08de2ed1d7577`.
- The optional CAS update now strictly UTF-8-encodes the metadata JSON and content **before beginning the SQLite transaction**. A lone surrogate in user-supplied content/metadata becomes a domain-specific `MemoryGenerationCASRejected` instead of a late SQLite/Unicode encoding exception.
- The frozen v1 `MemoryWrite` contract/schema is untouched. This is a fail-closed check; it does NOT imply trusted inputs or consent.
- New `tests/test_memory_generation_utf8_payload_run690.py` (commit `9cb621928dbe809a134a83a6e874fab61d4f9f68`) includes **4 malformed code-unit cases** (high/low surrogates in content or metadata keys/values) that must leave revision and event history unchanged and **2 valid Unicode cases** that remain writable. This verifies a definitively rejected pre-transaction request, NOT safe replay after COMMIT-UNKNOWN.
- [CI #42392735671](https://github.com/Iam-2squared/ark-ai/actions/runs/42392735671) **IN PROGRESS** at last observation, early Ubuntu Python 3.11 job GREEN.

## B — Durable audit/occurrence link uniqueness (4 tests)

- `tests/test_synthetic_audit_link_restart_uniqueness_run690.py` (commit `e41b1797a03b5c1ebfb87e5634cf6cbd77bef463`).
- **3 replay variants** attempt second linking on fresh SQLite handles: same pair; same reservation with a new audit event; new reservation with the old audit event. Each must fail without replacing the committed witness. **1 distinct-pair positive case** verifies unrelated synthetic records can advance the ledger.
- Registry-bound identities, disconnected preaction audit and occurrence reservation are checked. No backend execution or globally exactly-once external-effect guarantee.
- [CI #42392804944](https://github.com/Iam-2squared/ark-ai/actions/runs/42392804944) **IN PROGRESS** at last observation, early Ubuntu Python 3.12 job GREEN.

## C — Per-step Planner diamond READ bundle (5 tests)

- `tests/test_planner_diamond_independent_read_receipts_run690.py` (commit `e131d4847e0573336d9132e03b3ab98366178706`).
- A four-node root / two siblings / sink DAG retains each fixture READ result and its registered link in an independent READ journal. **Four missing-evidence cases** require rejection when any succeeded step lacks its unique receipt, even after the Planner journal is reopened. The **pending-sink case** accepts only the three succeeded-step receipts, refusing the unused sink receipt.
- This is a disconnected correlation, not proof of real READ execution; it never grants WRITE, dispatch or automatic replay.
- [CI #42392896351](https://github.com/Iam-2squared/ark-ai/actions/runs/42392896351) **QUEUED / IN PROGRESS** at last observation.

## D — Scheduler exact grace cutoff and persistent quarantine (4 tests)

- `tests/test_schedule_grace_exact_boundary_run690.py` (commit `7cf370339c81e4118a459df3f210c7d448f5165e`).
- The synthetic due preview classifies **due-1, due, due+grace and due+grace+1** correctly. The ledger must reject premature expiry at/before grace, then allow one local quarantine only after grace. A cold reader sees EXHAUSTED, never authorized notification/dispatch/replay.
- [CI #42392989966](https://github.com/Iam-2squared/ark-ai/actions/runs/42392989966) **QUEUED** at last observation.

## Boundaries / next steps

- **19 newly authored parametrized test cases, four new test modules, and one production-module guard.** All inputs and clocks are synthetic; no model/physical-device runtime inference.
- Intermediate CI success is not a final exact-head verdict. A new technical-report commit and later canonical checkpoint each trigger a distinct run. All checks must be evaluated by their **actual head SHAs**.
- These local SQLite ledgers do not authenticate users, trusted time, independent source custody, human review, complete privacy erasure or atomic state across databases. Unknown WRITE outcomes remain **NO AUTOMATIC REPLAY**.
- Prioritize: (1) final Windows/Ubuntu × Python 3.11–3.13 CI on the actual checkpoint-result SHA, fixing failures without weakening guard semantics; (2) Memory UTF-8 boundary plus CAS/expiry/COMMIT-UNKNOWN/WAL evidence; (3) Planner per-step READ correlation, terminal and crash recovery; (4) registry-bound durable audit and proactive quarantine local isolation.
- [V3 Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) remains blocked on immutable model/tool/runtime hashes, 120/30 human-reviewed rights/provenance/contamination evidence, hardware/software/cost packet, and separate explicit approvals. [UI Draft PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) is untouched and paused. Keep both Draft/unmerged; no protected evaluation, training, external GPU, billable action, credentials, destructive mutation or main merge.

**Overall ARK/JARVIS/V3: NOT_PASSED.**
