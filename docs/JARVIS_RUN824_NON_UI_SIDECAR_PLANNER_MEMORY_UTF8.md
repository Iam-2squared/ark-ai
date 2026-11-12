# ARK AI — Run824: disconnected SQLite race diagnosis, Planner ID ingress and Memory ABA review

**Work basis:** `e6e7072919cbd32ce75fdc1152c342ca72141988` (Run823 checkpoint). **Branch:** `research/jarvis-foundations`, Draft [PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), unmerged. **Report-write basis:** `36b5317823406b3e37fce28a5d353ca3a6768de9`. **Overall ARK/JARVIS: NOT_PASSED.**

## Package A — phase-aware, CI-equivalent disposable SQLite sidecar harness

[Source `08fc7b0b71e7cb9e65431963e1f03e46e0990660`](https://github.com/Iam-2squared/ark-ai/commit/08fc7b0b71e7cb9e65431963e1f03e46e0990660) extends `scripts/diagnose_memory_sidecar_startup.py` without touching the production Memory path fence. `--startup-mode sequential` (default) waits for child 1's readiness before starting child 2 and then releases their CAS writes together, matching the older failing test's sequencing. `concurrent` intentionally overlaps both fresh child bootstraps to isolate a different SQLite WAL lifecycle race. Four identity modes cover same-identity, separate-owner, separate-namespace and separate-source. The child catches failure phases (`BOOTSTRAP` vs `WRITE`) and emits only fixed status, optional sidecar suffix/type/link count and exception class, never a private database path, owner or row. The harness refuses unsafe sidecars without retry and runs only against automatically created temporary SQLite databases. Bounded iterations 1–30.

[New diagnostic regression `a9a7d806e064a3201db14024d5998130e5280f75`](https://github.com/Iam-2squared/ark-ai/commit/a9a7d806e064a3201db14024d5998130e5280f75) added **13 tests**: 8 argument-boundary cases, 4 actual sequential two-process disposable CAS scenarios, 1 aggregate-only/no-path CLI check. Initial CI found Ruff I001 in the new test's import formatting; subsequent normalization and one-blank import separator were made without weakening assertions. Final corrected test HEAD `13ffc07e072fa69f01d5723f24efd7f91d5bf542`, with [CI #43273579817](https://github.com/Iam-2squared/ark-ai/actions/runs/43273579817) **IN PROGRESS**, and a confirmed Ubuntu Python 3.11 Ruff step GREEN during inspection. Earlier `#43272797047`, `#43273243282`, `#43273477234`, `#43273524740` are historical CI FAIL due to this lint issue; later tests and multi-OS GREEN not yet established at report time.

## Package B — Planner restart step IDs validated before untrusted hashing

[Source `bc0c68f7e1e4376386616c3eeabf85a092a42bda`](https://github.com/Iam-2squared/ark-ai/commit/bc0c68f7e1e4376386616c3eeabf85a092a42bda) strengthens only the disconnected, no-dispatch `disconnected_planner_slot_restart_bridge.py`. Independently expected, Planner claim, offline step and observation step IDs now require **exact `str`**, nonempty, no NUL, strict UTF-8 and at most 256 encoded bytes **before** dict/set/sort, before the child SQLite slot reviewer. These are local review limits, not changed frozen Planner interfaces. The helper identity/budget are pinned by the module protocol.

[Test `b504a586a9d60ecd7342548882bf1b6be5b3c67e`](https://github.com/Iam-2squared/ark-ai/commit/b504a586a9d60ecd7342548882bf1b6be5b3c67e) adds **21 cases**: 20 carrier × hostile/reflected subtype, hash/equality trap, NUL, surrogate and multibyte budget denials; 1 exact UTF-8 budget boundary. All are fail-closed, with no WRITE recovery or replay. [Source CI #43272224575](https://github.com/Iam-2squared/ark-ai/actions/runs/43272224575), [test CI #43272569568](https://github.com/Iam-2squared/ark-ai/actions/runs/43272569568): Ubuntu 3/3 GREEN at last job inspection, Windows pending.

## Package C — Memory lifetime read-only review UTF-8 preaccess

[Source `e7895e62662797fee69f779f6779430cf7d603e9`](https://github.com/Iam-2squared/ark-ai/commit/e7895e62662797fee69f779f6779430cf7d603e9) hardens only optional `cas_generation_review.py`: `review_memory_revision_reuse` rejects inexact/unpaired-surrogate/overbudget owner, namespace and source labels *before* hashing the deterministic ID or reading private SQLite. Limits are strict UTF-8: 256 bytes owner/namespace, 512 bytes source. The read-only validator's identity is pinned; frozen Memory v1 constructors/schema remain unchanged.

[Regression `d57e11bbdcacc0868f2f6623513a8305c279605d`](https://github.com/Iam-2squared/ark-ai/commit/d57e11bbdcacc0868f2f6623513a8305c279605d), [surrogate fixture correction `36b5317823406b3e37fce28a5d353ca3a6768de9`](https://github.com/Iam-2squared/ark-ai/commit/36b5317823406b3e37fce28a5d353ca3a6768de9): **10 tests** with exact-class uninitialized store handles to prove validation precedes all DB path access, reflected fields, hostile string subclass, UTF-8 boundaries and substituted validator. This is no permission or durable provenance proof. [CI #43274097693](https://github.com/Iam-2squared/ark-ai/actions/runs/43274097693) last seen **QUEUED**.

## Evidence boundary and independent review

- [Run823 checkpoint CI #43264283714](https://github.com/Iam-2squared/ark-ai/actions/runs/43264283714): **GREEN 6/6** (verified Windows/Ubuntu × Python 3.11–3.13). This is the **preceding** exact-head baseline, not proof of Run824 source or tests.
- [Initial diagnostic source #43271996243](https://github.com/Iam-2squared/ark-ai/actions/runs/43271996243) last inspected **4/6 GREEN**, remaining Windows IN PROGRESS; source did not reproduce the race in an asserted runtime at that checkpoint.
- [Planner source #43272224575](https://github.com/Iam-2squared/ark-ai/actions/runs/43272224575) and [Planner regression #43272569568](https://github.com/Iam-2squared/ark-ai/actions/runs/43272569568) last inspected **Ubuntu 3/3 GREEN**, remaining Windows IN PROGRESS.
- [Memory source #43273944053](https://github.com/Iam-2squared/ark-ai/actions/runs/43273944053) and [Memory corrected tests #43274097693](https://github.com/Iam-2squared/ark-ai/actions/runs/43274097693) were **QUEUED** when last inspected. Exact-head six-job GREEN not established for this report.
- `compare(e6e7072...36b53178)` reported **ahead 11, behind 0**, with changed paths limited to the 3 backend/script files and 3 test files listed above. No frozen contract, V2 evaluation, Local UI/Launcher, Draft PR #5 or paused UI Draft PR #9 files changed.
- No local full checkout/pytest/Ruff, real GGUF, device acquisition, authenticated consent/clock/provenance, external execution, trusted multi-process file descriptor custody or independent human-review decision was claimed.
- Prior intermittent SQLite sidecar refusal remains **unresolved**. Metadata-only diagnostics and disposable fixture success cannot certify cross-process filesystem alias safety, and no automatic retry or weakening of sidecar/orphan/symlink/hardlink checks occurred.

## Next plan / 今後の方針

1. Verify exact latest HEAD's six CI jobs. Any failed job requires its actual logs and smallest semantics-preserving correction; no equivalent duplicate run.
2. Use bounded, disposable two-process probes with both sequential and concurrent bootstrap to classify any SQLite `-wal/-shm/-journal` refusal by **phase, suffix, file type and link count**, without paths, row data or side effects.
3. Continue Memory CAS/ABA/COMMIT-UNKNOWN coherent reconciliation, Planner durable RUNNING/UNKNOWN isolation, terminal propagation. Do not replay UNKNOWN writes.
4. After exact-head lower-layer GREEN, integrate registry-bound exact-type PermissionGate, restart-safe occurrence/audit-before-action and disconnected Mock Executor in isolated no-dispatch form; pursue privacy-safe Personal Context and proactive/observation backends independently.
5. Keep V3 preflight/Candidate/protected evaluation, paid compute and credentials gates closed until explicit authorization. Do not merge main or unpause UI without user direction.

**PR #5/#8/#9 Draft and unmerged; UI paused. No paid services, GPU, protected final evaluation, Candidate generation/promotion, real tool dispatch, new secrets, or destructive changes. Overall NOT_PASSED.**
