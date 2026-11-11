# LATEST — Run788 / 2026-11-11 JST

**LATEST:** Three coherent **FREE-ONLY / NON-UI** development packages saved in
[Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8):
(1) fix the precise Run787 CI Memory retained-global-prefix hash/JSON
preflight ordering bug; (2) pin detached Planner WRITE recovery bundle
decode/capture codecs and add **25 new regression cases**, then align four
legacy regression assertions to the new earlier denial; (3) reject value-equal,
wrong-type cached Personal Context retention items before private SQLite access
and add **5 new regression cases**. The concrete earlier failure logs were
inspected, not inferred. The V3 paid-compute gate was separately reviewed
read-only; it remains blocked. **30 new cases were submitted, NOT claimed
as all-six PASS. ARK/JARVIS/V3 NOT_PASSED.**

**Saved at:** Asia/Tokyo/JST **2026-11-11T17:59:39.733+09:00** (connector administrative
checkpoint-writing time, NOT a trusted ARK clock, independent provenance,
human approval or permission to dispatch).

## Exact branch, PR, work basis and checkpoint result semantics

- **Initial work-basis HEAD:** `28321c1d75e90e493e2c08efd06d644d36392847`;
  branch `research/jarvis-foundations`, PR #8 **OPEN/DRAFT/UNMERGED**.
  Its Run787 exact-head
  [CI #42982703663](https://github.com/Iam-2squared/ark-ai/actions/runs/42982703663)
  is **COMPLETED/FAIL in all six Windows/Ubuntu × Python 3.11–3.13 jobs**.
- **Memory pre-access gate source fix:** `8044b01a11981b075486cd5c8fdd0eeab0a50e83`,
  `src/ark/memory/synthetic_multiscope_integrity_review.py`. The retained
  foreign-owner event prefix codec is checked BEFORE `_scope_digest` can
  call a substituted SHA-256 or JSON function. Source change retains the
  existing later codec checks and does not modify the optional-prefix-free path.
  No Memory schema, write API or frozen evidence changed.
- **Planner detached WRITE archive source:** `ea2f95c1e34e419683443afea2d3dfc404c05f4a`,
  `src/ark/agency/synthetic_plan_recovery_bundle_review.py`. Frozen
  import-time digest/JSON/base64/archive/restore callbacks and limits are
  checked before byte decode and at reentrant boundaries. No approval,
  signed history, external effect, dispatch or exactly-once guarantee.
- **Planner new tests:** `22a08e9b071b60e3441806aec08a2905dc78c3e1`,
  `tests/test_plan_bundle_private_codec_preaccess_run788.py`: 24 parametrized
  hostile-callback cases plus one valid-codec malformed-shape denial (25).
- **Planner older expectation realignment:** `85587442a5092d7af985fe4082f18a9664cae431`
  (`test_recovery_bundle_carrier_preaccess_run648.py`) and
  `127e1ce54d40850392f1a7672bb1da7d2c298b17`
  (`test_synthetic_plan_bundle_cross_process_run434.py`). Before this
  alignment, [CI #42990211232](https://github.com/Iam-2squared/ark-ai/actions/runs/42990211232)
  confirmed **four FAIL in the Ubuntu jobs**: the new safer *pre-callback*
  rejection superseded expectations of later patched-slot/decoder rejection.
  No backend action or authorization was unblocked and the original False-only
  result authority remains intact. Re-alignment only updates the assertions
  to require refusal BEFORE the malicious callback executes.
- **Personal Context source:** `410d7cfe04a80db2321850e4d162b39cb924955f`,
  `src/ark/personal_context_retention_recheck_review.py`. Cached nested
  `RetentionState` must be the exact enum, `revision` exact positive int,
  `memory_id` exact str; `StrEnum == str` and `bool == int` no longer
  pass shape admission. **Tests:** `e45a92f7c572128b50a64e85ef8fb8fcf9e82113`,
  `tests/test_context_retention_exact_nested_fields_run788.py`, four
  wrong-type value-equal cases and one unchanged denial-only case (5).
- **Source-grounded report and read-only V3 gate review:**
  [Run788](./JARVIS_RUN788_NON_UI_PREFIX_EARLY_GATE_PLANNER_ARCHIVE_CODEC.md),
  commit `4abdd6852d8d2077785e7b0987f7ea26e544e4b6`.
- **Checkpoint-write work-basis HEAD immediately re-read:** `e45a92f7c572128b50a64e85ef8fb8fcf9e82113`,
  previous PROJECT_STATUS.md blob `93167e80da5c4dcc2dc8d8f2209d8dae0290a820`.
  **Checkpoint-result HEAD:** the normal GitHub Contents API will create a
  later commit; its exact SHA is intentionally **not predeclared inside this
  file**. Read the returned SHA and live branch/PR HEAD after writing. This
  checkpoint does not assert future CI GREEN for that later SHA.

## CI / exact evidence without borrowed PASS

- Inspected Run787 Ubuntu 3.11 job `130396601697` and Windows 3.12 job
  `130396601715` logs: **two** failing parametrizations of
  `test_memory_global_prefix_callback_custody_run787.py`
  (`sha256`, `json_dumps`) invoked a poison callback before the originally
  late retained prefix codec gate.
- **Memory repaired source**
  [CI #42989856403](https://github.com/Iam-2squared/ark-ai/actions/runs/42989856403):
  at inspection Ubuntu **3/3 GREEN**, Windows **3/3 IN PROGRESS**.
- **Planner source**
  [CI #42990130588](https://github.com/Iam-2squared/ark-ai/actions/runs/42990130588)
  and **original new-test**
  [CI #42990211232](https://github.com/Iam-2squared/ark-ai/actions/runs/42990211232)
  were in progress/failed as noted; the four observed old-test expectation
  mismatches were explicitly repaired in later commits.
- **Planner expectations re-aligned**
  [CI #42990884185](https://github.com/Iam-2squared/ark-ai/actions/runs/42990884185)
  was **QUEUED** when inspected.
- **Privacy source and new tests**, latest test HEAD
  [CI #42991154621](https://github.com/Iam-2squared/ark-ai/actions/runs/42991154621),
  was **QUEUED** when inspected.
- Updated source/new-test lines were statically checked for >100-char lines,
  but this is **not** Ruff, pytest, local matrix or actual Windows verification.
  No duplicate equivalent Actions workflow was manually launched. Source/test
  CI on the latest work and on this final checkpoint SHA remains
  **ALL-SIX GREEN NOT VERIFIED** until each exact-head job is read.

## Frozen contracts, authorization and current blockers

- PR #5 V3 head `805b377697472268db02650a89c7a94b1c5337c8`
  remains **OPEN/DRAFT/UNMERGED**; PR #9 Next Generation UI head
  `3b49048dd70eebcb6268299b9ecef4e301bbc0fd` remains
  **OPEN/DRAFT/UNMERGED / PAUSED**. Neither branch touched.
- Frozen V1/V2/Local UI/Launcher evidence, V3 Contract 1, protected V2 final
  evaluation and training authorization boundaries unchanged. No UI/frontend
  implementation, main merge, Candidate adapter/weights, data provenance or
  human-review fabrication, external/paid GPU/API, new credentials, hardware
  actions, real ToolBackend dispatch, automatic WRITE retry, sensitive erasure
  or irreversible operations.
- V3 blockers still include immutable HF revision/materialized model and
  tokenizer hashes, human-reviewed 120/30 dataset/provenance/contamination
  decisions, exact runtime/llama.cpp identities and user-approved cost,
  device and time ceilings. No billing or preflight authorized.
- A local hash/digest/witness is not independently authenticated custody.
  In-process callback pins are not a sandbox; multi-SQLite sweeps are not
  atomic, caller-provided times are not trusted, and local synthetic
  permissions/claims do not prove real-world exactly-once effects.
  **ARK/JARVIS/V3 NOT_PASSED.**

## Next plan / 今後の方針

1. Check exact-head **all six individual CI jobs** for Memory fix, Planner
   expectation realignment, Personal Context and checkpoint; repair any
   evidenced failure via the normal GitHub Contents path only, then develop a
   separate non-UI lane while the replacement CI runs.
2. Memory CAS/ABA and COMMIT-UNKNOWN manual reconciliation, cross-owner
   event/row append and retained historical evidence, with no automatic replay.
3. Planner terminal/crash recovery; extend positive detached archive fixtures
   and integrate proven immutable ToolRegistry + exact PermissionGate +
   trusted-clock audit-before-action **only using a disconnected mock** after
   prior exact-head GREEN.
4. Personal Context revocation/expiry and privacy-safe cleanup *reviews*,
   proactive occurrence/replay guards, observation offline fixtures, and
   free-only V3 approval/path/identity guards. UI, paid compute, Candidate,
   V2 protected suite and main merge remain separately gated.

## Historical checkpoint archive

Full Run786-and-earlier status text is preserved byte-for-byte at
[PROJECT_STATUS_THROUGH_RUN786.md](./status_archive/PROJECT_STATUS_THROUGH_RUN786.md),
verified prior blob `d822957c16172ea47f4dbca80d219c0da9433c65`,
with pre-existing Run639 archive parts untouched. Run787 status is preserved
in Git history at HEAD `28321c1d75e90e493e2c08efd06d644d36392847`.
Historical timestamps and CI states are not current proof.
