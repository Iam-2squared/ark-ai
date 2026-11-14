# Run515 — Detached READ-cycle receipt custody and coherent Memory denial epoch

**Status:** free-only experimental foundations; ARK/JARVIS NOT_PASSED. This is neither permission to execute tools nor authenticated history. PR #8 remains Draft and unmerged.

## Work basis and exact source

- Initial branch HEAD: `56cae9511d4997d0f635e993b321cb1b30a3da58` (Run514 checkpoint).
- First READ receipt module HEAD: `59754532aebccfdb83c76b8334bd1f90f75d44d0`.
- READ receipt tests HEAD: `f5d036463d0e055754489d34e8289f1d006ea1f4`. Import-only Ruff fix HEAD: `69bfa861d71cc132afcbf4b90f1b5c2196e9c846`.
- Memory last-denial source HEAD: `66472d13d859e66f7b67549838cac31d77ba58b2`.
- Final source/test HEAD for these packages: `32c3920992c3c666d825c647055dec90f45a7f64`. Later documentation/checkpoint commits are distinct heads and require separate CI evidence.

| Component | Path | Git blob SHA |
|---|---|---|
| READ-cycle retained recheck | `src/ark/agency/disconnected_read_cycle_receipt_recheck.py` | `4b289e3ec3a28e6af36dc588dafeaa1c6096fd60` |
| READ-cycle tests | `tests/test_disconnected_read_cycle_retained_recheck_run515.py` | `430bfa473e805d36aa8e2238b37db964232e11c3` |
| Memory coherent reviewer | `src/ark/memory/sqlite_retained_coherent_review.py` | `50bc78827538c11d73ff5c0df149fc992b32f70d` |
| Memory final-denial tests | `tests/test_memory_coherent_final_denial_run515.py` | `78463d183306362f88c155bf1f431a29f1d51fa2` |

## Scope and failure modes

**Planner mock READ receipt:** `verify_disconnected_read_cycle_receipt` independently re-simulates the original fresh pending DAG through the existing ToolRegistry, PermissionGate, and shadow PlanGraph. It compares all retained output fields, the synthetic-clock-bound fingerprint and READ waves, and requires exact-false non-authority flags. It retains exact original receipt, plan digest/status, registry revision and grant carriers around reentrant callbacks, including authority descriptors. It returns `None` and provides **no ToolBackend, external READ, WRITE, spend, trusted-clock verification, durable grant, auto-replay or execution token**. A matching receipt is a locally reproducible diagnostic, not authenticated source provenance.

**Coherent Memory:** the existing one-SQLite-transaction retained-prefix/row reviewer now rechecks every result data field **after the last false-valued authority getter**. A reflected, frozen-dataclass mutation in `cross_store_atomicity_proven` that changes a digest, count, status or the optional row-witness acknowledgment can no longer leave a forged returned report. The underlying frozen schema, memory CAS, previous witness validation and no-disclosure/no-action boundary remain unchanged.

**Tests authored:** 25 parametrized/individual mock READ receipt cases and 12 Memory denial-epoch cases (37 newly authored pytest cases total). Authored-case counts are **not** independent local pytest PASS evidence.

## CI custody (source-head-specific)

- [Initial READ HEAD 41253713874](https://github.com/Iam-2squared/ark-ai/actions/runs/41253713874): **6/6 FAIL** on Ruff I001 import ordering; no test-result claim. Corrected via normal GitHub Contents API, without relaxing runtime checks.
- [Corrected READ HEAD 41253814057](https://github.com/Iam-2squared/ark-ai/actions/runs/41253814057): **IN PROGRESS** when this document was prepared.
- [Latest Memory+READ source/test HEAD 41253895460](https://github.com/Iam-2squared/ark-ai/actions/runs/41253895460): **IN PROGRESS** when this document was prepared.
- Independent full local pytest/Ruff: **NOT PERFORMED** (this runtime cannot resolve GitHub for checkout). Do not promote older-head GREEN to a newer HEAD.

## Boundaries / next review

No network, OS backend, real READ/WRITE, memory disclosure, destructive operation, third-party API, physical PC, paid compute, external GPU, model training, Candidate, protected V2 evaluation, frozen-contract edit or main merge. Independent trusted clock, consent, provenance and cross-store atomicity are **not** established. Next: establish exact-HEAD GREEN; exercise detached READ verifier against restart/recovery fixtures, strengthen restart-safe Planner UNKNOWN WRITE manual-only triage and Memory witness custody, then integrate only the already-proven lower-level guards.
