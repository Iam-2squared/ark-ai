# ARK/JARVIS Run788 — Memory early gate, detached Planner bundle codec

**FREE-ONLY / NON-UI / DISCONNECTED / NOT_PASSED.** Work basis: PR #8
`research/jarvis-foundations` HEAD
`28321c1d75e90e493e2c08efd06d644d36392847`.
No real ToolBackend dispatch, Candidate creation, protected V2 evaluation, paid compute,
external effects, credentials, UI modification or main merge.

## 1. CI incident: previously queued Run787 actually FAILED

The exact Run787 checkpoint CI
[#42982703663](https://github.com/Iam-2squared/ark-ai/actions/runs/42982703663)
finished **FAIL in all six** Ubuntu/Windows × Python 3.11/3.12/3.13 jobs.
Downloaded Ubuntu 3.11 job `130396601697` and Windows 3.12 job
`130396601715` logs. Both report these two precise regressions:

- `test_memory_global_prefix_callback_custody_run787.py::test_rebound_hash_or_prefix_helper_is_denied_before_sqlite[sha256]`
- `test_memory_global_prefix_callback_custody_run787.py::test_rebound_hash_or_prefix_helper_is_denied_before_sqlite[json_dumps]`

The retained cross-owner Memory prefix codec was pinned **after** the scoped
`_scope_digest` callbacks. When a synthetic test replaced the shared hashlib/json
functions, the substituted functions were invoked too early. The tests correctly
expected refusal before any hostile callback or private-history SQLite open.
The Ubuntu log reports **2 failed, 12931 passed, 1 skipped**; Windows 3.12
reports **2 failed, 12858 passed, 74 skipped**. These counts pertain to those
failed checkpoint runs, not the new fix.

**Normal-path fix:** commit
`8044b01a11981b075486cd5c8fdd0eeab0a50e83` in
`src/ark/memory/synthetic_multiscope_integrity_review.py` moves the existing
`_require_original_global_prefix_codec()` gate directly after input-type
admission and **before first scope construction/digest** whenever the optional
`retained_global_prefix` is present. The later repeated gates are retained.
Without an optional global prefix, behavior remains unchanged. No schema,
authorization, retained witness grammar or frozen contract changed.
The existing Run787 parameterized regressions are the focused test oracle.

## 2. Independent Planner WRITE-recovery archive hardening

**Source:** commit `ea2f95c1e34e419683443afea2d3dfc404c05f4a`,
`src/ark/agency/synthetic_plan_recovery_bundle_review.py`.
The bundle contains per-WRITE retained recovery metadata. Its existing carrier
checks did not pin the local SHA-256, JSON, base64, digest/canonicalization,
archive and restore callback identities before decoding or capturing a bundle.
Added `_require_original_bundle_codec()` with original import-time witnesses
and exact budget/label constraints. It is checked before the first sensitive
input read, on decode/capture entry, and at the reentrant epoch checks.
This is only **in-process callback drift rejection**, not hostile-interpreter
resistance, cryptographic custody, human approval or exactly-once execution.

**Tests:** commit `22a08e9b071b60e3441806aec08a2905dc78c3e1`,
`tests/test_plan_bundle_private_codec_preaccess_run788.py`.
Twenty-four parametrized hostile-callback cases cover both detached entrypoints
against a dozen mutated codec/budget bindings; one intact-codec malformed-bundle
case verifies the established canonical-shape refusal and all three False-valued
authority flags. **25 submitted cases are not all-platform PASS claims**.
No real database, provider connection, tool backend or paid compute is involved.

## 3. Independent free-only V3 gate inspection (read-only)

Read PR #5 metadata and the unchanged
`docs/v3/PRE_PAID_COMPUTE_GATE.md` and `docs/v3/HF_IDENTITY_REVIEW.md`.
PR #5 remains **OPEN/DRAFT/unmerged** at
`805b377697472268db02650a89c7a94b1c5337c8`.
Explicit blockers remain immutable HF revision and local file hashes,
traceable human-reviewed 120/30 dataset/provenance/contamination decisions,
exact runtime/llama.cpp identities, and user-approved cost/device/time ceilings.
No immutable model identity, permission, reviewer decision, Candidate metrics or
preflight evidence was inferred from metadata. PR #5, its gates and its frozen
Contract 1 remain untouched.

## CI and safety boundaries

- Memory-fix SHA:
  [#42989856403](https://github.com/Iam-2squared/ark-ai/actions/runs/42989856403).
- Planner source SHA:
  [#42990130588](https://github.com/Iam-2squared/ark-ai/actions/runs/42990130588).
- Planner regression SHA:
  [#42990211232](https://github.com/Iam-2squared/ark-ai/actions/runs/42990211232).

These runs were queued/in progress during the work session. Their **exact-HEAD
individual six-job results must be inspected**; do not borrow GREEN from Run786.
No duplicate manual workflow runs were requested. The new source/tests were
statically checked to have no lines exceeding 100 characters, not locally
executed; public GitHub DNS access from the isolated local container was
unavailable and no alternate write path was attempted. PR #9 remains untouched,
Draft/unmerged and UI paused. All frozen V1/V2/Local UI/Launcher evidence
remains unchanged; ARK and V3 are **NOT_PASSED**.

## Next plan / 今後の方針

1. Resolve exact-HEAD Windows/Ubuntu CI from the three new SHAs; if a concrete
   failure remains, apply only the smallest normal Contents fix and work a
   different non-UI path during the new CI.
2. Memory: historical retained-prefix cross-owner integrity, generation
   CAS/ABA and COMMIT-UNKNOWN manual-only reconciliation without retries.
3. Planner: terminal/restart recovery and detached archive positive roundtrip
   fixtures before promoting any registry-bound simulated integration.
4. ToolRegistry/PermissionGate/audit-before-action with only a disconnected
   mock executor; Personal Context privacy lifecycle, proactive occurrence
   replay, offline observation fixtures, and free-only V3 source/identity
   guards stay isolated until exact-HEAD evidence supports integration.
