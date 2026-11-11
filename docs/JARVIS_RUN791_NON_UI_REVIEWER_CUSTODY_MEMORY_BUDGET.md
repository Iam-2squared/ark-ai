# Run791 — disconnected callback custody and exact Memory limit epochs

**Report prepared:** 2026-11-11T20:46:09+09:00 JST. This wall-clock stamp
is not an ARK trusted-clock receipt or a human approval.

**Initial work-basis:** `4be0d71782c1ac0629cf264065093dccdfd48878`
on `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8).
The basis [workflow #43007372724](https://github.com/Iam-2squared/ark-ai/actions/runs/43007372724)
was independently checked: six individual Windows/Ubuntu × Python 3.11–3.13
jobs **COMPLETED/SUCCESS 6/6**. Do not transfer this GREEN to Run791.

## Package A — proactive readiness / trigger reviewer identities

- Implementation `src/ark/proactive_startup_fence_review.py` at
  `14e6c88e1c757b1bab3d8535053dde98f9efb1a9`, with corrected
  legacy refusal wording at `88ad4b5c479c206525b847c405da399c12d02f75`.
  Two imported cross-boundary reviewers are now pinned at module import and
  rejected before either executes or can inspect private synthetic startup
  and trigger state. Every existing source-epoch sweep checks them again.
- `tests/test_proactive_startup_reader_custody_run791.py` at
  `6c0a07cc1adda915ff443a8f73d2db498f30eb89`: two malicious pre-access
  callback substitutions and one local denial-only positive fixture.
- **CI correction:** Several intermediate runs failed `ruff E501` for a
  109-character refusal message, not a measured semantic flaw. The only
  verified correction is a two-literal line wrap at
  `36e01a7bc6bf759390e299bcd2a73481e67a485c`.
  Earlier failed runs:
  [#43014122417](https://github.com/Iam-2squared/ark-ai/actions/runs/43014122417),
  [#43014177936](https://github.com/Iam-2squared/ark-ai/actions/runs/43014177936),
  [#43014239808](https://github.com/Iam-2squared/ark-ai/actions/runs/43014239808),
  and [#43014293308](https://github.com/Iam-2squared/ark-ai/actions/runs/43014293308)
  (initially IN PROGRESS at last combined read; verify its final result).
  Corrected HEAD [#43014440234](https://github.com/Iam-2squared/ark-ai/actions/runs/43014440234)
  was IN PROGRESS at report preparation. **Do not assert GREEN yet.**

## Package B — disconnected due-slot historical-prefix callback custody

- `src/ark/agency/disconnected_due_prefix_review.py` at
  `f004a6bdc9ed9a7496443854e098c92485274f7e` now pins the
  imported retained witness checker and row-digest callback, outer SHA-256
  serializer, and reconciliation hash domain before opening SQLite.
  This rejects value-looking forged digest implementations before private
  historical rows are read; it does not authenticate the retained witness.
- `tests/test_due_prefix_callback_custody_run791.py` at
  `b4c4debb45e6f9aaf76587818826190527f1392f`:
  five substituted-callback/domain pre-access negatives and one legitimate
  genesis-prefix denial-only positive. The independent `due._inspect` fixture
  callback remains explicitly substitutable in legacy drift tests; this
  package **does not claim to pin every Python callback**.
- Due-source and due-test HEAD CI were FAIL due to the unrelated earlier
  proactive `E501`; package-local six-environment validation must be
  taken from a later exact HEAD including the corrective line wrap.

## Package C — Memory retained-generation integer budget continuity

- `src/ark/memory/retained_generation_fence.py` at
  `f18d1d55c8bfbf525eabf9f9829b84d4642d7b9a`:
  the event-budget and SQLite maximum must retain import-time **exact int
  type and identity**, including the baseline slots. Former value inequality
  could accept an equal-valued float or execute a hostile comparison method
  before private Memory input admission.
- `tests/test_memory_generation_budget_carriers_run791.py` at
  `b3fedda337d6a0492c6d57ee13cc7e4e269afa97`:
  five equal-valued/poison-comparison substitutions rejected before private
  reads and one real disposable SQLite restart positive. The review is
  read-only and grants neither CAS nor automatic COMMIT-UNKNOWN replay.
- Memory-source run [#43014575626](https://github.com/Iam-2squared/ark-ai/actions/runs/43014575626)
  was IN PROGRESS; test HEAD [#43014631815](https://github.com/Iam-2squared/ark-ai/actions/runs/43014631815)
  was QUEUED at preparation. **Six-job GREEN not yet verified**.

**Combined newly submitted cases:** 3 + 6 + 6 = **15**.
No local pytest/Ruff execution, real ToolBackend, paid service, or human
approval is claimed. Reverify six independent matrix jobs on the exact
source/test/checkpoint HEAD before treating this work as GREEN.

## Safety, limits and integration order

These are interpreter-local identity checks only. They are neither
cryptographic attestation nor a Python sandbox. SHA-256 and local SQLite
cannot prove independent retained custody, consent, trustworthy time, real
effects, cross-store atomicity, or absence of races after the last read.
No notification, execution, WRITE replay, erasure, Candidate generation,
protected V2 evaluation, model promotion, paid compute, new credentials,
physical-PC action or main merge is permitted or performed.

**Next:** verify the corrected proactive code and Memory test exact-head
matrix; fix only observed failure logs using ordinary GitHub Contents API.
Then move to Memory CAS/ABA/COMMIT-UNKNOWN manual provenance, Planner durable
terminal recovery, disconnected ToolRegistry + PermissionGate + audit-before-
action mock integration only after lower-layer exact-head GREEN. Audit free
V3 guards on isolated paths. Freeze V1/V2/Local UI/Launcher contracts and
evidence. Keep PR #5 and PR #9 Draft/unmerged, #9 untouched and UI paused.
**ARK / JARVIS / V3: NOT_PASSED.**
