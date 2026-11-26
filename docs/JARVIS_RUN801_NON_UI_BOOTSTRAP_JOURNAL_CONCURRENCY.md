# ARK Run801 — NON-UI Memory/Audit bootstrap & proactive journal concurrency review

**Scope:** Local-only, free-only, reversible safeguards on [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). No UI work, actual ToolBackend, notification, external compute, paid service, trusted approval, training, Candidate or protected V2 evaluation.

## Exact basis and source packages

Initial inspected branch/PR #8 HEAD: `a58a268b7eae0dd1146aac23276afc60331a6736` (Run800 checkpoint); initial status blob `136bfaf4e65eb94e00048735aada1ee18801d2ed`. PR #5 and #9 were confirmed Draft/open/unmerged; PR #9 untouched.

1. **Memory same-process initial-open integrity.** `src/ark/memory/sqlite_store.py` source commit `b454667a5a3e8a6c0868d36e1c4cff1ad25d3aae`: move existing first-open parent/main/sidecar preflights, parent creation and v1 WAL setup into one process-local `RLock` epoch. The existing `_initialize` lock remains in place, now safely reentrant; no v1 schema, storage semantics, CAS authority or frozen evidence changed. New `tests/test_memory_bootstrap_path_fence_race_run801.py` commit `3b8869dfa6db3dbf91363634ed5a422fe6f87b71`, **one** deterministic concurrent-constructor test observing preflight overlap and exact WAL/v1 schema. Ruff import-only fix `9e686d76c7f5e0f19ba60062a29d66b9ed137836` combines two imports; all assertions unchanged.
2. **Proactive SQLite transient unlink handling.** `src/ark/proactive_synthetic_review.py` source commit `fe29a5379263cde0a6f71c0b221361405ba0b186`: if a regular SQLite sidecar's `lstat` snapshot reports **zero hard links**, re-sample the same pathname exactly once; accept only disappearance or a single-link regular file. Always reject an absent main with sidecars, symlinks, special files, hardlinked files and persistent invalid metadata. No journal deletion, permission, new replay, notification or Tool execution. New `tests/test_proactive_transient_journal_preflight_run801.py` commit `c3a997adca87adbe41a0d7a881352463bf24d1fa`, **four** deterministic tests (one simulated unlink + three unsafe sidecar variants). This mitigates one plausible observed SQLite race; it is not evidence that the CI failure's precise `st_nlink` was zero.
3. **Audit first-open custody.** `src/ark/agency/audit.py` source commit `2d24e2bcb8cea0021c8e3dc2b9198cbebccbcfd8`: serialize existing path checks, parent creation and WAL setup under one same-process `RLock`, preserving the independent `_initialize` guard. New `tests/test_audit_bootstrap_path_fence_race_run801.py` commit `01e2c1369d699891a770fe27f9b40c3ed3f952dd`, **one** deterministic concurrent-constructor test observing serialized path fences and unchanged audit schema.

**Total new cases: six submitted; not a claim that they have passed all six CI environments.** No local integrated test run or actual PC/GGUF evaluation is asserted. The tests do not weaken or edit existing fault-injection oracles.

## Concrete pre-existing CI failure forensics

- Run799 checkpoint [CI #43093515609](https://github.com/Iam-2squared/ark-ai/actions/runs/43093515609), Ubuntu Python 3.12 job `130776371290`: pytest failed `test_repeated_two_initializer_races_leave_one_valid_v1_schema` with `MemorySchemaError: orphaned memory SQLite sidecar refused`. Ubuntu 3.11/3.13 were GREEN. Windows Python 3.12 job `130776371264` passed **13,490 pytest cases** with 74 skipped, then the GitHub `actions/upload-artifact@v4` service returned an HTML document where JSON was expected, after five retries, causing that job failure. Do not mislabel this as a code regression. Other Windows failures remain independently unclassified here.
- Run800 checkpoint [CI #43098848007](https://github.com/Iam-2squared/ark-ai/actions/runs/43098848007), Ubuntu Python 3.13 job `130784465992`: pytest failed `test_process_race_preserves_scope_budget_and_durable_dedup[distinct-policy-expected2]`; one concurrent subprocess raised `SyntheticTriggerRejected: unsafe proactive SQLite sidecar`. The other **five of six** jobs were GREEN. The log does not include the transient sidecar inode metadata, so the specific cause is unresolved.
- Early Run801 CI [#43106123571](https://github.com/Iam-2squared/ark-ai/actions/runs/43106123571), [#43106348736](https://github.com/Iam-2squared/ark-ai/actions/runs/43106348736), [#43106589837](https://github.com/Iam-2squared/ark-ai/actions/runs/43106589837) hit the same newly introduced **Ruff I001** in the Memory test import block, confirmed from actual Ubuntu logs. No pytest was run on those failing jobs. The test-only import fix above was saved via the normal Contents API; use its subsequent exact-head CI, never these earlier failures, to decide correctness.
- No duplicate equivalent workflow was launched and no broad retry or safety gate relaxation occurred.

## Remaining invariants and blockers

The SQLite path `lstat` checks are *not* atomic OS handle custody; an adversary racing filesystem mutations or SQLite commits may invalidate a preflight. Process-local `RLock` does not serialize separate processes. Zero-link recheck is limited to an already-unlinked regular inode and must never be extended to symlink or hardlink acceptance. Snapshot/hash/clock checks do not authenticate human approval or external provenance. No automated COMMIT-UNKNOWN retry or actual notification/action was authorized.

Frozen V1/V2/Local UI/Launcher evidence and V3 Contract 1, contamination/provenance/regression/reproducibility protections remain untouched. PR #5 stays Draft/unmerged under its protected gate, PR #9 Draft/unmerged **untouched**, UI development PAUSED. No external GPU, paid/potentially billable actions, new credentials, Candidate generation/promotion, protected evaluation or main merge.

## Next plan / 今後の方針

1. Verify post-Ruff-fix exact-head CI across Windows and Ubuntu × Python 3.11–3.13; if FAIL, inspect the actual first failure and preserve every old fault test. For the proactive race, distinguish zero-link transient from other alias metadata before claiming a complete repair.
2. Continue Memory retained-CAS/ABA, coherent expiry, and COMMIT-UNKNOWN read-only investigation, with no blind retry or frozen schema change.
3. Improve Planner durable recovery and terminal propagation, registry-bound exact PermissionGate, and audit-before-action connected only to disconnected mock execution after independent GREEN.
4. Continue privacy-safe Personal Context, proactive and observation backend contracts and free V3 guard audits. Preserve all user authorization boundaries.
