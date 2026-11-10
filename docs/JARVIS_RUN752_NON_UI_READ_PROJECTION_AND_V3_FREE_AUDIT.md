# ARK non-UI evidence — disconnected READ recovery cross-review (2026-11-10 JST)

> Status: **source and regression fixtures saved on Draft PR #8; final six-platform CI verdict pending**. This is an opt-in, offline synthetic reviewer, not an execution path, human approval, authenticated clock, trustworthy journal, or proof of external effects. It does not alter frozen V1/V2/Local UI/Launcher boundaries or the paused PR #9.

## Work basis and packages

- Independent initial PR #8 HEAD: `948832922467969c36a91eb6c73171ec2802c681` (Run751 checkpoint). Its [CI #42724158888](https://github.com/Iam-2squared/ark-ai/actions/runs/42724158888) was independently read and confirmed **6/6 GREEN** on that **older exact HEAD**. This verdict is not transferable to any new source/test commit.
- **Package A — new, reversible READ-only join:** `src/ark/agency/disconnected_read_projection_review.py` first saved at [`e772553`](https://github.com/Iam-2squared/ark-ai/commit/e772553fc693a18d3fa56625365f6de9f0dae6af); follow-up [`bc19213`](https://github.com/Iam-2squared/ark-ai/commit/bc192137283b9c69d8f4824f80a9e01e0f22555a) corrected the isolated projection's hash domain to a NUL-terminated v1 domain, pins immutable disposition/state mappings and original READ/mixed-classifier guards **before** the first private step-slot read. A dual-classifier comparison maps `NOT_STARTED` to `PENDING` and explicitly reconciles seven disposition classes. Unknown or inconsistent histories fail closed. Returned `ready_step_ids` are mock-only hints, never permission.
- **Package B — independent mixed-DAG oracle:** [`6e8fe15`](https://github.com/Iam-2squared/ark-ai/commit/6e8fe1502c5080100a0bf2564441f0883168eaaf) adds 56 parametrized synthetic cases across two independently chosen root states, a five-step fan-in, terminal-versus-uncertain precedence, disconnected READ independence, and WRITE non-dispatch.
- **Package C — dual-review regressions:** [`825e6ba`](https://github.com/Iam-2squared/ark-ai/commit/825e6bacaf724fa73b4041a265553d487ef1f3ed) adds normal/rejected topology, deterministic result and inertness tests; [`54f0846`](https://github.com/Iam-2squared/ark-ai/commit/54f08466b752fc453301a62c36617afe5662604f) adds preaccess descriptor-sabotage and mapping-replacement cases with the carrier constructed before temporary sabotage. This prevents the test setup itself from triggering the malicious property. **21** parametrized cases in that file; **77 new cases total** across packages B/C. All remain CI-pending until exact-head results are read.

## What is and is not established

The two existing standalone reviewers intentionally have distinct synthetic digest domains and different status vocabularies. One classifies READ-only recovery; the other classifies mixed READ/WRITE recovery but this new join passes **READ-only projected claims**. A disagreement fails closed; equal digests do not establish independent historical custody, actor identity, consent, actual execution, durable one-shot authorization, audit-before-action, WAL file-handle integrity, trusted time, or a restart-safe write result. No backend is invoked, and none of the returned permission flags can become true.

The first new source version exposed an avoidable pre-validation slot-access surface while copying input for the second reviewer. The corrected source calls the original underlying no-authority/descriptor checks before reading any caller-retained `ReadRecoveryStep` fields. The regression suite explicitly poisons a class slot with a would-be exfiltrating property and verifies **zero getter calls**. The new source remains isolated; nothing in the existing Planner/PermissionGate/Registry dispatch pathway imports or depends on it.

## Independent V3 zero-spend review (unchanged PR #5)

Read-only source basis: Draft PR #5 `805b377697472268db02650a89c7a94b1c5337c8`.

- `learning/authorization_packet_verify.py` (blob `d6137a9e37faaa6580389306b133ea1e11615e25`) compares canonical detached packet bytes with a separately retained file digest and the packet's internal payload digest. Its result correctly denies external compute, Candidate creation and protected evaluation. A local matching digest **is not a signed human approval or billing-cap receipt**.
- `learning/runtime_guard.py` (blob `f3ecdbdcc0cc44ac87ad3121ae27a547199181f7`) reads `ARK_V3_OS_IMAGE_DIGEST` from the process environment, checks CUDA/device/package identities, and implements a soft monotonic timeout guard. The environment variable is a caller-supplied claim, not external OS/image attestation or provider bill protection.
- `learning/training_cli.py` (at the inspected PR #5 head) checks frozen scope and local evidence before heavy runtime use, but the preflight evidence is currently published with an `open("xb")` write of its final path. The CLI snippet does not prove a durable fsync/atomic publish-and-commit protocol or single-attempt crash recovery, so a partial/unknown outcome must remain blocked pending independent evidence. No preflight, GPU import, Candidate creation, paid provider check or weight download was executed in this review.
- The current `learning/execution.py` explicitly contains strict duplicate-key rejection when loading the execution snapshot; earlier generic checklist language about all snapshot JSON parsing being permissive must **not** be promoted to a verified current defect. Separate loaders and post-authorization paths require their own exact-source review.

### Next integration order

1. Confirm exact-head green CI for new reviewer/fixtures; repair only observed failures on the ordinary permitted GitHub write path and recheck downstream integration.
2. Keep mixed WRITE startup *quarantined*. Any future planner/recovery integration must bind actual immutable Registry identities, durable occurrence IDs, exactly-once authorization, audit-before-action, and an independently trusted clock. Distinguish database commit uncertainty from external effect certainty.
3. Maintain separate V3 human dataset/legal review, immutable local model/tool byte identities, runtime/time/billing ceiling and distinct preflight/full-training approvals. Do **not** run paid/external compute, open V2 evaluation, auto-promote a Candidate or merge main.

No files or branches from PR #5 or paused UI PR #9 were modified. This evidence is not a release or roadmap PASS.
