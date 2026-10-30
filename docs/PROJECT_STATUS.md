# ARK AI — Canonical Project Status

**LATEST — 2026-10-31 / Run489: restart-safe due reservations, Memory witness carrier integrity, privacy diagnostic authority fence and V3 artifact lineage exact types**

**Saved at:** **2026-10-31T07:47:53+09:00 Asia/Tokyo/JST**, observed local wall-clock shortly before writing. **Not independently authenticated time, human review, consent or approval.**

**Overall ARK/JARVIS status: NOT_PASSED.** These are isolated, local-first/reversible foundations and V3 pre-paid-compute safeguards, **not** integrated JARVIS, trusted hardware, external Tool dispatch, proof of exactly-once real-world effects, legitimate consent, independent custody, protected V2 final evaluation, full Candidate training or authorization to merge.

## Canonical work basis, Draft PRs and checkpoint

- **JARVIS foundations:** [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), `research/jarvis-foundations`, OPEN/DRAFT/UNMERGED at the last verified read. **Initial work-basis HEAD** `480a7112742098df959a43c1fb3b36153ff24e6e` (Run488 checkpoint). **Run489 final source/test HEAD** `af8c5aef6bc6be1b338f2e6dff34e3575d135970`. Technical evidence commit `a0c93e57fb2756d9d135d0affdd96a89b975f4a0`; previous-checkpoint archive commit `e6444f8cf69d5e914ed3805f07376ff28ad88da3`.
- **Separate free-only V3:** [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5), `research/v3-learning-evaluation`, OPEN/DRAFT/UNMERGED. **Initial work-basis HEAD** `79376f3ce777dc877c63ce58785153e493b9b7fc`. **Final source/test HEAD** `b754608f41e9848ed7c8755aa46608d1af056910` (including one narrow test correction).
- **Checkpoint-write-basis HEAD** PR #8 `e6444f8cf69d5e914ed3805f07376ff28ad88da3`, containing the Run489 technical report and verbatim Run488 checkpoint archive. **Checkpoint-result HEAD:** the commit executing this file replacement is not knowable from the file's own pre-commit contents. Read the ordinary GitHub Contents update response and re-read the resulting branch HEAD after save; never present the basis SHA as the result SHA. A later checkpoint must use that actual result.
- **Main** last verified `7a843f17eb96ed13d66f23b58b06406b3002e405`; no merge performed.

## NEW in Run489 (four source/test work packages; 64 new parameterized pytest cases)

1. **Scheduler / existing-only durable restart — 17 cases.** `src/ark/agency/disconnected_due_reservation.py` blob `05874bee7a1fc34b0f0d75984d332e2f1fd3b43d`; `tests/test_due_restart_retained_existing_run489.py` blob `2d37f86c6533ecb1f8f003f1b4857d4b8c257c93`. Opt-in `require_existing=True` refuses absent storage and any uninitialized former store; `reopen_with_witness` checks exact independently retained caller tip before subsequent reservation. The default synthetic fixture-creation path remains compatible. This is **not independent provenance**. A write-intent SQLite bootstrap lock is still taken during existing-only construction; it must not be mislabeled as a pure read-only open.
2. **Memory / retained source identity — 6 cases.** `src/ark/memory/disconnected_witness_ledger.py` blob `38f1ca213f30cc9111bb7c6beaa9c8790d68c60c`; `tests/test_memory_witness_source_custody_run489.py` blob `7b9de3a086352decb8f6d02c0e990a39de0991ed`. Pin original ledger Path object and retained witness identity around SQLite open/inspect/commit and append CAS. Reject equal-valued path rebinding or reflective witness mutation in callbacks. OS-level path races and writer authenticity remain unproven.
3. **Personal Context / retention-review authority — 6 cases.** `src/ark/personal_context_retention_recheck_review.py` blob `c95e20784380127ec9838a054262a6c57a9335c0`; `tests/test_retention_recheck_authority_fence_run489.py` blob `27e0b2051b1e891b3fe516f35ad611b3771cdc22`. Pin exact diagnostic result type and deny spoofed deletion authorization, erasure completion, context use and disclosure flags. Does not erase private information or prove consent.
4. **V3 / exact lineage identity — 35 cases.** `src/ark/learning/lineage.py` blob `5cc1e3582f7c730c1f9526d8ee903f1b9f438c26`; `tests/v3/test_lineage_exact_carriers_run489.py` final blob `ad2031c9204d45cd8f9863df8b71175f12eebb55`. Validate exact built-in string, SHA, byte count, schema and quantization types, bounded control-free metadata and original artifact identity type. No model weights or external compute touched. An interim test encoded literal backslash+x00 instead of a NUL byte; corrected by `chr(0)`, with the source safety guard unchanged.

[Run489 technical evidence](JARVIS_DUE_RESTART_MEMORY_CUSTODY_PRIVACY_LINEAGE_RUN489.md) records exact source and test blob identities, failure cause and non-authorizing limits.

## Tests / CI at the last actual observation

- **Pre-run Run488 latest PR #8 checkpoint** #1713 / `41134443768`: **GREEN** (completed/success; HEAD `480a7112742098df959a43c1fb3b36153ff24e6e`). PR #8 prior source #1710 and PR #5 prior source #1706 also completed success. These belong to **older HEADs**, not current code.
- **Run489 PR #5 source-only** #1716 / `41140102905`, `01f8ee1ffa194202753f57a77bd6ad545476b583`: **GREEN**. With new test file, #1717 / `41140128403`, `27f9b45d258c38d7e2ca3c2af4dcc8a8884f431e`: **FAIL** all six jobs (Ubuntu 3.12 log: **1 failed / 619 passed**; wrong test fixture literal). Test retained and corrected. **Exact final PR #5 HEAD** #1722 / `41140350170`: **QUEUED** at last query; **not GREEN** yet.
- **Run489 PR #8 final source/test** `af8c5aef6bc6be1b338f2e6dff34e3575d135970`: #1721 / `41140289600` **QUEUED** at last query, while earlier #1719 / `41140205826` was **IN PROGRESS**. **Latest PR #8 code is not verified six-job GREEN** yet.
- Technical evidence #1723 / `41140432978`, archived status #1724 / `41140460475`: **QUEUED** at last query. This checkpoint creates a later separate Actions run. No duplicate CI reruns were dispatched.
- Independent local full `pytest` / `ruff`: **NOT VERIFIED**; this runtime's local `git ls-remote` failed DNS lookup for `github.com`. GitHub connector source/commit reads and standard Actions jobs are distinct evidence.
- Public GitHub standard CI was permitted as zero-cost activity; no GPU job or paid compute started.

## Frozen evidence / boundaries and blockers

- Memory v1 contract `src/ark/memory/contracts.py` blob `b6e93821ecd69270a7634aceb20775dc36e9953c`, Agency contract `src/ark/agency/contracts.py` blob `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`: unchanged on current PR #8. No intended modification to frozen V1/V2/Local UI/Launcher evidence, protected V2 final suite/scorer, V3 Contract 1, contamination/provenance/regression/reproducibility gates. These have not all been exhaustively re-audited in this invocation.
- No paid API/service/subscription, external GPU, credential/connection creation, physical PC action, actual sensor/ToolBackend dispatch, potentially irreversible operation, real Candidate training/export, protected V2 evaluation opening, automatic promotion or main merge. No fabricated runtime identities, file hashes, outcomes or human decisions.
- Local hash chains and retained caller witnesses cannot authenticate an independent writer, detect all full-store rollback without an independently preserved tip, prove cross-SQLite atomicity, establish consent/erasure, trusted-clock origin or real-world effect completion. **UNKNOWN WRITE stays quarantined; never automatically retry.** PR #5 stays Draft under its separate authorization gate.

## Next plan / 今後の方針

1. Verify #1721 and #1722 against exact final source/test HEADs on all six standard CI jobs. If FAIL, inspect relevant logs and apply smallest semantics-preserving fix via normal GitHub Contents API; immediately work another independent lane while CI runs. No duplicate equivalent workflows.
2. Replace the due-ledger existing-only write-intent bootstrap with a true read-only SQLite transaction while keeping first-creation/migration explicitly separate; add concurrent restart/loss tests. Verify it on its exact HEAD.
3. Continue Memory independent CAS, durable rollback-custody, consistent SQLite snapshots; establish clear limits where independent writer/OS path guarantees do not exist.
4. Advance Planner manual UNKNOWN WRITE reconciliation, immutable ToolRegistry and exact PermissionGate, Trusted Clock audit-before-action and durable occurrence/replay barriers; disconnected/mock execution only.
5. Prioritize Personal Context revocation/retention lifecycle, Scheduler duplicate prevention, startup readiness, observation fixture contracts and free V3 reproducibility/approval/path/identity guards; all later milestones remain NOT_PASSED until integration gates are demonstrably fulfilled.

---

**Verbatim Run488 checkpoint:** [docs/history/PROJECT_STATUS_RUN488.md](history/PROJECT_STATUS_RUN488.md), blob `9c400ca05438b4dfc6609fb84dc44469f1c1c985`. **Run487 and earlier:** [docs/history/PROJECT_STATUS_THROUGH_RUN487.md](history/PROJECT_STATUS_THROUGH_RUN487.md), blob `21ea22807b38c1947edf252878b00d1dc2d20903`. These are preserved history, not the latest checkpoint. Run489 technical evidence blob `8ebdb114e88af9a5182510f05dba4d8c3dced942`.
