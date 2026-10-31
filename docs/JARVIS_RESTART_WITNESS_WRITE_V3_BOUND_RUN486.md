# ARK AI — Run486: disconnected restart triage, Planner WRITE custody, bounded V3 snapshot JSON

**Scope:** free-only synthetic/local, Draft/unmerged. This document records source/test evidence, **not** a human approval, trusted timestamp, complete JARVIS PASS, or permission for any real Tool/GPU/Training/evaluation. GitHub CI outcomes are exact-HEAD-specific, not transferably trusted across subsequent edits.

## Work packages

### 1. Three-store synthetic restart witness comparison (PR #8)

- `src/ark/disconnected_restart_witness_bundle.py`, Blob `33d56e112f3a2c4fdb07800788d4730bdb7b5e58`.
- `tests/test_disconnected_restart_witness_bundle_run486.py`, Blob `09d759b3360bd96020439324689df687d115f0f4` — 13 test functions, **17 pytest cases** after parametrization.
- Binds caller-retained **Memory witness** (epochs/chain), **Personal Context replay witness** (count/chain), and **Scheduler due witness** (count/fingerprint) to exact respective local SQLite stores. Bounded two-pass read-only rechecks detect stale/rewritten exact tips, forged authority fields, object-carrier retargeting and some callback mutations.
- The result explicitly denies startup, execution, replay, personal-context use, independent custody, trusted clock and atomicity. Two passes are **not** one atomic snapshot. Caller-retained witnesses and each SQLite writer are unauthenticated, and appended-prefix provenance is unproven.
- Initially #1683 / `41118079511` failed a Ruff B017 test diagnostic. Normal Contents API test repair `cd23e57e1f4bdcff358d130c3d208ff295d4a2ec` uses the exact domain exception; resulting #1686 / `41118343631` requires its own six-job result.

### 2. Planner UNKNOWN WRITE restart binding (PR #8)

- `src/ark/agency/disconnected_write_restart_binding.py`, final checked source Blob `96eb2afd1c4b58b26a5d2856797e41b6bf20aab4`.
- `tests/test_disconnected_write_restart_binding_run486.py`, Blob `0ecef132eedd1190e9c3d61d32fa9a067f9dab73` — 13 test functions, **15 pytest cases** after parametrization.
- Joins exact-type synthetic Planner recovery dispositions to SQLite WRITE reservations by `(plan_id,step_id,slot_id)` under read-only transaction and retained witness. Claims of UNKNOWN/RUNNING/previously-reserved WRITE remain quarantined; never dispatch or retry externally.
- Initial #1688 / `41118551159` caught one real failing regression on Ubuntu 3.11: adversarial `ledger.inspect` callback appended a SQLite reservation while returning a stale, equal-valued result (observed **1 failed, 5049 passed, 1 skipped**). Semantics-preserving fix added an **independent SQLite row/tip recheck after the callback**, source commit `ebc0470db85ddca90dd0b38e58cf0bd5597be5c2`, triggering #1689 / `41118860216`. The failing test is retained, not removed or weakened. Verify current #1689 before declaring GREEN.
- Local database uniqueness and CAS do **not** establish external exactly-once effects, independent consent/identity, trusted clock, audit-before-action, or cross-store atomicity.

### 3. V3 bounded free-only execution snapshot ingestion (PR #5)

- `src/ark/learning/execution.py`, Blob `3292658f155bd69c68cb683631cdf46bc66f0b03`.
- `tests/v3/test_execution_snapshot_loader_budget_run486.py`, Blob `b69c2a9701b919a2951c6939bac259284fe30f9e` — 12 test functions, **23 pytest cases** after parametrization.
- Existing `load_snapshot` read of the entire JSON file is now bounded to 1 MiB; nesting is limited to 128 JSON containers with escaped quotes/string bracket handling; nonfinite exponents are refused while previously supported noncanonical valid JSON object input remains accepted. This is read-only ingestion and does not alter the protected V3 training approvals/frozen evaluation contract.
- Latest exact source/test PR #5 HEAD `683cfa5f580dfff1fe8402f9859f875877e15a76`: #1685 / `41118243577` **six jobs GREEN** on Windows/Linux Python 3.11–3.13, independently checked. Earlier source-only CI #1684 / `41118195102` succeeded.
- No GPU, downloads, external service, model weights/Candidate, training, V2 opening, or promotion.

## Change/evidence accounting

Three coherent work packages, **55 new parameterized pytest cases** (17+15+23). Initial work basis PR #8 `2cd04830aa36cb4d678f6c7b8739d8d7f1c7690c`, PR #5 `40c77ec0edfd2f7d268454407a8eaac2b84275e2`. Latest source/test PR #8 `ebc0470db85ddca90dd0b38e58cf0bd5597be5c2` (PR #8 #1689 in progress as of the technical evidence preparation). Latest PR #5 source/test `683cfa5f580dfff1fe8402f9859f875877e15a76` (#1685 GREEN). Technical evidence and subsequent checkpoint are document-only revisions and have distinct CI status; do not confuse any previous source HEAD with a later checkpoint commit HEAD. All source/test writes used normal GitHub Contents API with immediate prewrite branch HEAD checks; no raw Git objects, force push, manual CI duplicate or protected merge.

Frozen Memory v1 SQLite Blob `0aba6392b39563df520aa8b378d0b313f0cc0a0d`; Memory contract `b6e93821ecd69270a7634aceb20775dc36e9953c`; Agency contract `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9` unchanged. `main` basis `7a843f17eb96ed13d66f23b58b06406b3002e405` unchanged, both PRs Draft/unmerged. V1/V2/Local UI/Launcher evidence, V3 frozen Contract 1, contamination/provenance/reproducibility gates remain protected. Independent local whole-project pytest/Ruff **NOT VERIFIED**: container GitHub DNS failed, so GitHub CI is the actual current validation source.

## Remaining limits / next steps

First confirm PR #8 #1689 across all six CI jobs; minimize and retest any failure. Then independently strengthen authentic clock/audit-before-action, durable Memory/Context/Scheduler privacy lifecycle and Planner UNKNOWN WRITE reconciliation with no retries. Add only reversible interfaces after exact-head GREEN, keep external action/consent/physical-PC, real Candidate, paid compute, V2 protected eval, promotion and approval-required merge blocked pending explicitly authorized evidence. Overall JARVIS = **NOT_PASSED**.
