# Run791 — non-UI provenance review, due-prefix and Memory/Permission bounds

**Report updated:** 2026-11-11T20:53:14+09:00 JST (local authoring time only,
NOT trusted clock, approval or execution authority).
**Work-basis HEAD:** `4be0d71782c1ac0629cf264065093dccdfd48878`
on `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8).
Basis CI [#43007372724](https://github.com/Iam-2squared/ark-ai/actions/runs/43007372724)
was verified **GREEN 6/6** with individually completed Windows/Ubuntu × Python 3.11–3.13 jobs.
**Run791 exact-head GREEN is NOT YET VERIFIED.**

## A. Proactive callback experiment and semantics-preserving CI repair

An initial proposal (commit `14e6c88e1c757b1bab3d8535053dde98f9efb1a9`)
statically pinned cross-review callback references to prevent unreviewed
synthetic readers from seeing private startup inputs. However these callback
seams are **deliberately used by existing regression fixtures to inject a
mid-read path, witness or descriptor mutation**. An initial long error message
also caused a Ruff `E501` check failure on all six jobs.

- After wrapping the long message at
  `36e01a7bc6bf759390e299bcd2a73481e67a485c`, real CI
  [#43014440234](https://github.com/Iam-2squared/ark-ai/actions/runs/43014440234)
  showed **21 Ubuntu test failures**; observed errors were a legacy regex
  mismatch and previously expected callback invocations no longer happening.
  This was a real fixture-contract regression, NOT passing validation.
- The proactive source was **fully restored byte-for-byte** to its previously
  GREEN blob `36793a89a3bd4f64c72c883d78a201b865056edb`, at repair
  commit `45cc06d5d57cfcf9c395a7cc70b05ecd61cf3072`.
  The full old race-detection behavior is preserved and the new callback
  pre-admission guard is **NOT being claimed as implemented**.
- New `tests/test_proactive_startup_reader_custody_run791.py` was revised
  at `46763f78a7196246e0a5852874238e2e68afa6d4`:
  two injected reviewer calls that retarget a value-equal source Path must
  be detected after the callback, plus one unchanged denial-only fixture.
  **3 submitted cases**; exact-head six-job CI pending.
- Initial failed runs also include
  [#43014122417](https://github.com/Iam-2squared/ark-ai/actions/runs/43014122417),
  [#43014177936](https://github.com/Iam-2squared/ark-ai/actions/runs/43014177936),
  [#43014239808](https://github.com/Iam-2squared/ark-ai/actions/runs/43014239808),
  and [#43014293308](https://github.com/Iam-2squared/ark-ai/actions/runs/43014293308).
  The former first-wave failure was Ruff `E501`; the later one was the
  verified legacy callback-fixture conflict. **No tests were weakened to
  force a pass; source behavior was restored instead**.

## B. Disconnected due-prefix digest/witness callback admission

- Source `src/ark/agency/disconnected_due_prefix_review.py` at
  `f004a6bdc9ed9a7496443854e098c92485274f7e` pins the imported
  `due._check_witness` / `due._digest`, outer `hashlib.sha256` and
  `json.dumps`, and hash domain before retained SQLite row inspection.
- `tests/test_due_prefix_callback_custody_run791.py` at
  `b4c4debb45e6f9aaf76587818826190527f1392f`: five synthetic malicious
  swaps denied pre-access plus one normal genesis-prefix denial-only check
  (**6 new cases**).
- The lower-level `due._inspect` remains fault injectable by old tests.
  SHA-256 and local SQLite cannot independently authenticate a retained
  witness, a historical writer or permission to replay/notify.

## C. Memory retained-generation budget protocol

- Source `src/ark/memory/retained_generation_fence.py` at
  `f18d1d55c8bfbf525eabf9f9829b84d4642d7b9a`: exact
  `int` type and import-time carrier **identity** for both
  event-budget and SQLite range baselines before private generation review.
  Former inequality could run a hostile comparator or accept float `40000.0`.
- `tests/test_memory_generation_budget_carriers_run791.py` at
  `b3fedda337d6a0492c6d57ee13cc7e4e269afa97`: five malformed/poisoned
  budget cases + one real local SQLite restart positive (**6 cases**).
  No CAS write or unknown-COMMIT automatic retry.

## D. PermissionGate grant-budget baseline protocol

- Source `src/ark/agency/policy.py` at
  `05d8753e8d72f74e4e93d8162aee57e1f04b8f3d` replaces
  an equality comparison with exact `int` type and object identity checks
  of the current vs original `1024` grant limit. This rejects a swapped
  original baseline before hostile grant iteration or in-memory token spend.
- `tests/test_permission_grant_original_budget_custody_run791.py` at
  `ce341ddf64f169d7dc1cf26a81e6f7a5784b2dcd`: equal-valued float
  and poisoned comparison replacements in both registered and ordinary
  PermissionGate paths (**4 parametrized cases**). Valid restored gates
  still inspect only local synthetic grants and never call a backend.

**New submitted regression cases:** 3 + 6 + 6 + 4 = **19**.
At document revision the source/test/reconciliation CI for the newest HEAD
was still running; earlier Run791 HEADs are explicitly **FAIL**, not GREEN.
No local pytest or Ruff result is claimed; use GitHub Action jobs and failure
logs with exact matching SHA for a final result. No equivalently duplicative
workflow was rerun.

## Safety, unresolved gates, next priorities

This run touched neither frozen V1/V2/Local UI/Launcher contracts/evidence nor
V3 Contract 1. PR #5 remains Draft/unmerged under paid-compute review gate;
PR #9 stays Draft/unmerged and UI/frontend development is PAUSED.
PR #8 remains Draft/unmerged. No billable service, external GPU, training,
Candidate weight/adapter generation, protected V2 evaluation, promotion,
real backend/Tool dispatch, destructive change, secrets/account connections,
physical-PC work, human approval or main merge was performed.

Interpreter-local descriptor/callback guards are NOT a security sandbox.
Neither SQLite digests nor repeated read-only sweeps prove actual writer
identity, authenticated consent, trusted time, globally atomic reads,
external effects or race-free post-return freshness. ARK/JARVIS/V3
**NOT_PASSED**.

**Next:** confirm exact-head full six-job CI; correct only observed failures.
Then prioritize Memory generation CAS/ABA and manual COMMIT-UNKNOWN,
Planner restart/terminal recovery, and ultimately only a disconnected mock
Registry + exact-type PermissionGate + restart-safe one-shot ledger +
audit-before-action integration after prerequisite GREEN. Independent
privacy-safe context/observation/proactive fixtures and free V3 guards follow,
with UI and all paid/protected gates still paused.
