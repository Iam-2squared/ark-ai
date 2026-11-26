# ARK AI — Run825 non-UI generation CAS, Planner and proactive descriptor custody

**Scope:** `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), from exact work-basis HEAD `e91a72a56e04fe4d7149c9908b1317c37191967e`. This report is a source/test change receipt, **not** a JARVIS PASS or independent custody claim. No UI work, real external effect, training, protected evaluation, Candidate, paid compute, physical PC activity, or main merge.

## 1. Reproduce genuine independent-process Memory CAS rather than a create

- [Source `195e2dbd2317d5dbbef913f1a52ecdcdc3f94423`](https://github.com/Iam-2squared/ark-ai/commit/195e2dbd2317d5dbbef913f1a52ecdcdc3f94423): extends the **disposable, bounded** `scripts/diagnose_memory_sidecar_startup.py` with opt-in `--operation generation-cas`, default retaining historical `create`. Parent seeds a real Memory row for each unique synthetic scope/source and snapshots its **local** `MemoryGenerationCASToken` before starting two independent Python subprocesses. Children execute `generation_fenced_memory_update`; same-identity competition should produce `CONFLICT + UPDATED`, disjoint owners/namespaces/sources `UPDATED + UPDATED`. Sequential vs concurrent WAL bootstrap remain separately selectable. Never retry a sidecar refusal; child output remains path-free, limited to dispositions and sidecar file type/link metadata.
- [7 authored tests `1a6cc487d0d816a2fa3b69a935a017422ec82ffd`](https://github.com/Iam-2squared/ark-ai/commit/1a6cc487d0d816a2fa3b69a935a017422ec82ffd): four real independent-process generation CAS configurations verify **revision 2** and create/update event history, two strict aggregate CLI privacy assertions, one unknown-operation denial. No original user DB or real application actuation. This removes the previous **create-only reproduction gap**, but cannot establish external filesystem custody or independently explain every intermittent SQLite sidecar refusal.

## 2. Planner restart source slot/getter custody

- [Source `673e6d00409610ce867f4496fd0354de5f4edf6f`](https://github.com/Iam-2squared/ark-ai/commit/673e6d00409610ce867f4496fd0354de5f4edf6f): pins import-time class/slot/getter identity for seven recovered-plan, reservation, witness and dependency carrier types in `disconnected_planner_slot_restart_bridge.py`. Rejects a replaced class descriptor before touching step IDs, private journal/SQLite source or child reviewer callbacks. No new permission to execute or retry an UNKNOWN WRITE; existing bridge digest protocol and frozen contracts unchanged.
- [11 authored tests `eb09926a46c21c083a90053a8df36b9a45ba1f4f`](https://github.com/Iam-2squared/ark-ai/commit/eb09926a46c21c083a90053a8df36b9a45ba1f4f): eight field-slot traps, two class substitution traps, one intact positive synthetic quarantine path. Hostile getters must not execute.

## 3. Proactive startup cross-source descriptor custody

- [Source `22b986e991ed3306c5d13a9eed3d40696d979230`](https://github.com/Iam-2squared/ark-ai/commit/22b986e991ed3306c5d13a9eed3d40696d979230): pins six source type identities and dataclass field/getter descriptors before the dual synthetic trigger/readiness review. This is local callback custody, **not** a trusted clock, authenticated readiness, notification authority or real ToolBackend permission.
- [11 authored tests `da54c8782a767a3acafcb4e5f7dc9e6cf9c8a0db`](https://github.com/Iam-2squared/ark-ai/commit/da54c8782a767a3acafcb4e5f7dc9e6cf9c8a0db): eight source getter changes, two source type swaps, one unchanged protocol positive test.

**Total: 29 authored regression test cases** (7 + 11 + 11). This is **not** a claim that all 29 tests or the final six-job matrix have passed. No local full ARK checkout, local pytest/Ruff, model/PC benchmark, training, or authoritative human review was performed.

## CI and evidence at report time

- Prior Run824 exact checkpoint HEAD `e91a72a56e04fe4d7149c9908b1317c37191967e`: [CI #43274967459](https://github.com/Iam-2squared/ark-ai/actions/runs/43274967459) **GREEN 6/6** confirmed on Ubuntu/Windows × Python 3.11–3.13.
- [Memory source CI #43282564465](https://github.com/Iam-2squared/ark-ai/actions/runs/43282564465): Ubuntu 3/3 GREEN; Windows 3 **IN PROGRESS** on last check.
- [Memory 7-case test CI #43282709844](https://github.com/Iam-2squared/ark-ai/actions/runs/43282709844): Ubuntu 3/3 GREEN; Windows 3 **IN PROGRESS** on last check.
- [Planner source CI #43282971958](https://github.com/Iam-2squared/ark-ai/actions/runs/43282971958): Ubuntu 2/3 GREEN, rest **IN PROGRESS** on last check.
- [Planner 11-case test CI #43283078777](https://github.com/Iam-2squared/ark-ai/actions/runs/43283078777), [proactive source CI #43283330576](https://github.com/Iam-2squared/ark-ai/actions/runs/43283330576): QUEUED/IN PROGRESS on last check. Latest proactive test and this report's own CI IDs may not exist yet at this report write.
- **Do not label a newer source/test/report/checkpoint HEAD as GREEN based on earlier runs.** Confirm six jobs for the exact final HEAD later. Inspect actual failures; never suppress fail-closed guards or dispatch duplicate equivalent CI.

## Unchanged safety boundaries and next work

Frozen V1/V2/Local UI/Launcher evidence unchanged. Draft PR #5 remains gated; UI Draft PR #9 remains paused/unmerged/untouched; PR #8 stays Draft/unmerged. No paid/external compute or API, unauthorized credentials, live tool dispatch, untrusted-clock consent claim, Candidate/training/promotion, protected final evaluation, automatic UNKNOWN replay, destructive operation or main merge.

Prioritized next: (1) certify latest exact HEAD in all six jobs and minimal fix on real failure, (2) use the now-real generation-CAS disposable two-process diagnostic to isolate WAL-bootstrap vs update-time sidecar safety refusals without bypass, (3) Memory COMMIT-UNKNOWN and Planner durable quarantine integrity, (4) controlled Registry/PermissionGate/atomic audit/mock-only integration once lower-layer exact-HEAD GREEN, and (5) privacy-safe context, proactive, observation and V3 free-only guards. JARVIS: **NOT_PASSED**.
