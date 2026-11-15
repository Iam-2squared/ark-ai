# ARK AI Run896 — disconnected revocation alias, Planner fan-in, coherent Memory snapshot

This is a non-UI, no-spend, isolated foundation review. It does **not**
authorize dispatch, WRITE, privacy disclosure, human consent, Candidate,
protected evaluation, external compute, or merging any Draft PR.

## Exact starting evidence and work packages

- **Starting HEAD**: `95b83583e47d403bae6f759da55a491c1a1907bd` (Run895).
  [CI #43711489810](https://github.com/Iam-2squared/ark-ai/actions/runs/43711489810)
  completed GREEN for all six individual Windows/Ubuntu × Python 3.11–3.13 jobs,
  re-read this invocation. This baseline does not certify later commits.
- **Package A — Privacy diagnostic alias custody**:
  [`56ad48e1`](https://github.com/Iam-2squared/ark-ai/commit/56ad48e1bf7d9a8ae37e7b854dd48a10839e83e4)
  changes only `scripts/diagnose_revocation_wal_processes.py`.
  The disposable, independent, read-only synthetic-veto verifier now rejects
  symlinks, non-regular files, hardlinked databases, and a changed main-file
  device/inode or link count between opening and finishing the verification.
  This keeps a same-row aliased SQLite file from being reported as the same
  durable local veto. Existing exact v1 DDL, bounded readback and quick-check
  conditions remain required. No revocation ledger contract or production
  memory store was changed.
- **Package A regression**:
  [`8e6e63f1`](https://github.com/Iam-2squared/ark-ai/commit/8e6e63f12f62069f41afe8b8b80d7327d2b0652e)
  adds `tests/test_revocation_readback_alias_run896.py`, **five authored
  parametrized cases**: hardlink, symlink (filesystem-dependent skip),
  directory, absent file and unrelated SQLite schema. A single-link
  canonical synthetic row remains verifiable. The test harness uses a
  temporary directory and no user database.
- **Package B — disconnected Planner restart/fan-in**:
  [`31c11371`](https://github.com/Iam-2squared/ark-ai/commit/31c1137169925007f09b19c2c16a383c4afe2fe1)
  adds `tests/test_planner_journal_split_branch_recovery_run896.py`,
  **two authored cases**. A cold-restarted, unresolved RUNNING branch cannot
  activate downstream fan-in while an independent branch completes; both
  attempted replay and premature dependent start are rejected. A subsequent
  explicitly staged failure blocks fan-in once while another RUNNING branch
  remains UNKNOWN; its later completion cannot unblock the descendant.
  All calls are synthetic `ToolCall` identities without ToolBackend.
- **Package C — coherent multi-scope Memory WAL snapshot**:
  [`8983901c`](https://github.com/Iam-2squared/ark-ai/commit/8983901c58d0a4bdb2bbdbc82a06131c97a5e243)
  adds `tests/test_memory_snapshot_clock_writer_interleave_run896.py`,
  **two authored parametrized cases**. A controlled single clock callback
  commits revisions in two namespaces **after** the reader establishes its
  SQLite snapshot. The review must never show mixed old/new namespaces;
  expiry filtering at the same sampled time is examined in both
  include-expired modes; a cold subsequent review sees both new revisions.
  Only disposable SQLite, synthetic scopes and local WAL are used.

- **Package D — registry-bound inert WRITE identity**:
  [`c36b3574`](https://github.com/Iam-2squared/ark-ai/commit/c36b3574792dba5c124d837123c5e250f7b8b398)
  adds `tests/test_registered_atomic_revision_effect_fence_run896.py`,
  **three authored cases**. Distinct backend IDs produce distinct bound
  action claims with the same request digest; a READ-only registration cannot
  be converted into a WRITE intent; and reflective Effect.READ → WRITE drift
  fails closed. The test backend raises if invoked and no backend is executed.
- **Semantics-preserving Planner test correction**:
  [`a10b3d13`](https://github.com/Iam-2squared/ark-ai/commit/a10b3d13d29f22ee87dc2a2c5d724ebb72cdc1c3)
  fixes the test's initially incorrect expectation: after starting a
  second independent step `spare`, its RUNNING status is **also ambiguous**
  on cold restart, alongside `alpha`. The journal correctly preserves both;
  neither is an automatic replay grant. This is an assertion correction, not
  a production code change or safety-policy relaxation.

Total: **four coherent non-UI packages, twelve AUTHORED regression cases**.
New source changes are confined to the independent disposable revocation
diagnostic; the Planner, Registry and Memory schemas and frozen contracts are
unchanged.

## CI / integrity distinctions

The following runs were launched by normal PR pushes, **not** duplicate
manual workflows. Last observed while work was in progress:

| Exact HEAD | CI run | Evidence at report preparation |
| --- | --- | --- |
| `56ad48e1...` | [#43715274454](https://github.com/Iam-2squared/ark-ai/actions/runs/43715274454) | IN_PROGRESS |
| `8e6e63f1...` | [#43715358642](https://github.com/Iam-2squared/ark-ai/actions/runs/43715358642) | IN_PROGRESS |
| `31c11371...` | [#43715476426](https://github.com/Iam-2squared/ark-ai/actions/runs/43715476426) | IN_PROGRESS |
| `8983901c...` | [#43715589249](https://github.com/Iam-2squared/ark-ai/actions/runs/43715589249) | FAIL: inherited original Planner test expectation (not a Memory failure) |
| `c36b3574...` | [#43715969331](https://github.com/Iam-2squared/ark-ai/actions/runs/43715969331) | QUEUED at latest sampling |
| `a10b3d13...` | [#43716034217](https://github.com/Iam-2squared/ark-ai/actions/runs/43716034217) | QUEUED at latest sampling |

**The earlier Planner-test HEAD #43715476426 FAIL** (Ubuntu 3.11–3.13): it incorrectly expected only `alpha` to remain ambiguous after `spare` was explicitly transitioned to RUNNING. The `a10b3d13` normal-path assertion correction preserves the stricter correct behavior. **The latest exact source/test HEAD is NOT CERTIFIED GREEN in this document.**
The checkpoint may record subsequent independently verified job outcomes.
Do not count authored tests as green without their actual jobs.

## Safety, unresolved boundaries and next plan

A pathname `lstat()` comparison is not an atomic open-handle provenance
proof: a target can be replaced and restored between probes. Neither a
verified synthetic row, self-consistent journal hash nor caller-supplied
clock authenticates human consent, authorizes action or guarantees
cross-store exactly-once delivery. The diagnosed Windows SQLite WAL/SHM
last-close race remains unresolved; the losing revocation process must fail
closed even if another process committed a veto.

Preserved without modification: frozen V1/V2/Local UI/Launcher contracts
and evidence, direct Observation contract, frozen V3 Candidate/training
approval and protected evaluation gates, Draft PR #5, and paused Draft UI
PR #9. No frontend work, new service/account/credential, spending, GPU,
production tool, real personal data, irreversible action or main merge.

**Next plan / 今後の方針:** (1) certify current exact-head six-job CI,
fix failures without weakening denial rules; (2) isolate Windows WAL/SHM
last-close refusal with bounded no-private-data observations; (3) continue
Planner UNKNOWN journal and Memory CAS/expiry/coherent snapshot contracts;
(4) advance registry-bound PermissionGate, independent audit-before-action
and disconnected Mock READ only once lower-level exact-head evidence is
GREEN; (5) keep the free V3 guard lane read-only and UI paused.
