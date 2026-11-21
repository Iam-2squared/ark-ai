# Run822 — Non-UI Planner quarantine and Memory scope preaccess

**Scope:** Draft PR #8, `research/jarvis-foundations`. Initial live work basis: `3181224e37eeec1bf77503c0ad4e8778254a4972` (Run821 checkpoint). This report is non-normative evidence for isolated, reversible, free-only changes, **not** a JARVIS, V2, V3, protected evaluation, trusted-clock or dispatch PASS.

## Package 1 — bounded, non-executable Planner ID verification

- Source commit `b20cba6cc69c7a24de686bf4e23b27639a3d06f6`, test commit `14a019f3def96df28f051e810bd6a7544f5c3f55`.
- `src/ark/agency/disconnected_recovery_quarantine_inventory.py` now admits **both** held and unknown Planner step IDs only as exact, nonempty, non-NUL, strict UTF-8 strings of at most 256 **bytes**. The unknown-step inventory is bounded to 24 entries; this is a local diagnostic budget, not a change to any frozen Planner schema.
- Input fields are validated before hashing, set membership, or sorting. This prevents executing caller-supplied `__hash__` / `__lt__` methods on objects reflectively inserted into an otherwise frozen local receipt. The helper and local bound are pinned by the reviewer protocol.
- `tests/test_recovery_quarantine_step_id_preaccess_run822.py`: 17 authored regression cases: four hostile-object cases, ten malformed/oversized/invalid-UTF-8 cases, bounded valid ID, 25-item unknown inventory, protocol-bound mutation. The inert result remains `MANUAL_REVIEW_REQUIRED` or `QUARANTINED`, never approval, replay or dispatch.
- Caveat: source receipt hashes here are caller-local. Neither integrity nor consent is independently authenticated.

## Package 2 — bounded Memory coherent expiry scope ingress

- Source commit `66ed0359df622207c8f0f87ab924bdbe236edddc`, initial test commit `3333ab6b4145f6180991fc26c8834dbd8f813e92`, corrected test commit `bd480473548001810160d5e6cbff5d1a812612b8`.
- `src/ark/memory/coherent_expiry_snapshot_review.py` validates exact owner/namespace strings as strict UTF-8 with at most 256 bytes each, **before** SQLite is opened or private row/event history scanned. The new local limit is pinned in `_protocol()`; it does not change `SQLiteMemoryStore`, the public Memory schema, TTL policy, owner consent or any actual expiry action.
- `tests/test_memory_coherent_expiry_scope_budget_run822.py`: ten authored cases: six oversized/invalid Unicode scopes, two reflected wrong-type scopes, an exact 256-byte empty-cohort review, and a protocol-bound mutation. Test inputs exceeding the frozen `MemoryScope` constructor's 256-*character* limit are reflectively mutated **after** a valid construction, to exercise a real threat: frozen instances can be mutated after validation.
- CI for the **pre-correction** test commit `3333ab6...` ([run #43251503896](https://github.com/Iam-2squared/ark-ai/actions/runs/43251503896)) recorded two test failures on Ubuntu 3.12: the test incorrectly constructed an oversized `MemoryScope` before entering the expected reviewer rejection. The test-only fix `bd48047...` preserves the reviewer safety check and no production denial is weakened. **The corrected exact HEAD must have its own GREEN validation**; the earlier failure is not evidence of a broken final path.
- No memory content is intentionally returned, erased, exported or granted retention authority.

## Independent forensic lane — pre-existing SQLite sidecar race

Read the failure log of [CI #43231449304](https://github.com/Iam-2squared/ark-ai/actions/runs/43231449304), Ubuntu Python 3.12 job `131227650555`. The concrete failure in `tests/test_memory_independent_owner_process_cas_run772.py::test_independent_owners_can_both_commit_across_os_processes` is one child `SQLiteMemoryStore` initialization raising `MemorySchemaError("memory SQLite sidecar path is not a single regular file")`; the other independent child returned normally. The run had 1 failure / 14,282 passed / 1 skipped on that job; its other five OS/Python jobs were successful. The prior Run821 checkpoint [#43243836738](https://github.com/Iam-2squared/ark-ai/actions/runs/43243836738) was GREEN 6/6.

The current `sqlite_store.py` `_require_safe_memory_path()` uses `lstat` and requires sidecar files `-wal`, `-shm` and `-journal` to be singly-linked regular files, rejecting symlinks, hardlinks, FIFOs and orphaned sidecars; `_BOOTSTRAP_LOCK` is **process-local**, not cross-process. The failing log does **not** record the exact suffix, stat mode, link count, or timing, so SQLite sidecar turnover under concurrent processes is a hypothesis, **not** an established root cause. No change to this safety path, no test suppression, retry loop, loosened checks or fabricated proof is included.

Safe next forensic step: use disposable local fixtures with two competing independent processes; report only content-free sidecar suffix, `st_mode` file type, link count and observation phase. Preserve all rejection semantics while distinguishing legitimate SQLite lifecycle turnover from unsafe aliases. Then design a minimally invasive, independently reviewed fix if reproduced. No user private DBs or files are needed.

## CI / authorization receipt

- Baseline: Run821 checkpoint `3181224e37eeec1bf77503c0ad4e8778254a4972`, #43243836738 **GREEN 6/6** on Windows/Ubuntu, Python 3.11/3.12/3.13.
- Run822 source / test workflows: [#43251194025](https://github.com/Iam-2squared/ark-ai/actions/runs/43251194025), [#43251311657](https://github.com/Iam-2squared/ark-ai/actions/runs/43251311657), [#43251415177](https://github.com/Iam-2squared/ark-ai/actions/runs/43251415177), [#43251503896](https://github.com/Iam-2squared/ark-ai/actions/runs/43251503896), [#43251602443](https://github.com/Iam-2squared/ark-ai/actions/runs/43251602443). As checked during report preparation, newer exact-head jobs were **IN PROGRESS**; the pre-fix test run had the two known test setup FAILs. Other Ubuntu source/test jobs have partial GREEN; **full final-head GREEN 6/6 is not established**. No manual duplicate workflow dispatched.
- 27 authored regression cases total (17 + 10), **not** a claim of 27 independently run local PASS results. No local pytest/Ruff/full checkout, physical PC/GGUF, model training or external execution was performed this invocation.
- Frozen V1/V2/Local UI/Launcher evidence and contracts were not modified; Draft PR #5 and paused Draft PR #9 remain untouched and unmerged. PR #8 remains Draft/unmerged. No paid/external GPU, paid API or service, Candidate generation/promotion, protected evaluation, new accounts/secrets, destructive data operations, owner notifications, real tool dispatch, or main merge.

## Next plan / 今後の方針

1. Confirm corrected source/test exact-head Windows+Ubuntu CI outcomes. Inspect any actual FAIL from job logs and apply the narrowest non-weakening fix, working independent lanes while CI runs.
2. Reproduce the independent-process Memory SQLite sidecar failure with metadata-only disposable fixtures; do not loosen filesystem-identity checks.
3. Extend Memory CAS/ABA, durable COMMIT-UNKNOWN row/event integrity and Planner persistent UNKNOWN quarantine; integrate with Registry/PermissionGate/audit-before-action/mock executor only after their lower-level exact-head GREEN gates.
4. Keep privacy-safe Personal Context, proactive/observation mock contracts and free-only V3 guards independent and non-authorizing. User approval remains mandatory at protected boundaries.

**Overall ARK/JARVIS: NOT_PASSED.**
