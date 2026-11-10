# Run761 — Independent OS crash and privacy checkpoint (NON-UI, FREE-ONLY)

## Scope, evidence standard, safety

Branch `research/jarvis-foundations` / [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8).
Work basis: Run760 checkpoint `488cd4bd0fd49a162c7f6f02bea7b8a30f5dfe00`.
Normal GitHub Contents API saved **four standalone regression packages** (12
parameterized cases). No production modules, frontend code, frozen v1/v2
contracts, paid services, model execution, protected evaluations, or real
ToolBackend calls were changed or invoked. The only OS subprocesses use Python
`multiprocessing.get_context("spawn")` against disposable local fixture files.

Do not treat a test-only source commit as proof of green execution until the
CI result for its **exact SHA** is checked on all six Windows/Ubuntu Python
3.11/3.12/3.13 jobs. Prior Run760 checkpoint CI #42787363660 was confirmed
**6/6 successful** on `488cd4bd0fd49a162c7f6f02bea7b8a30f5dfe00`.
That prior result does **not** certify the Run761 test additions.

## A — Memory COMMIT-UNKNOWN: unacknowledged genuine OS exit

Commit `440abe694cf1fe321072059172cf87f56a0be359`.
`tests/test_memory_os_exit_manual_triage_run761.py` adds three cases:
one matching COMMIT, one different-content COMMIT and two equal-content
COMMITs. The child process writes through
`generation_fenced_memory_update` and exits with `os._exit(0)` before
returning a receipt. A fresh interpreter reads retained evidence with
`review_uncertain_memory_commit` and must classify the visible history as
`ONE_MATCHING_UPDATE_VISIBLE` only for the first case and
`INDETERMINATE` otherwise. No disposition attributes the commit to the
original caller or authorizes an automatic retry. The old CAS token must
remain stale and the second diagnostic must not change the row/events.

**Non-claims:** a matching row is not evidence of a signed writer identity,
durable external effects, permission to dispatch, or cross-store atomicity.

## B — Plan-wide recovery across four independently committed mock stores

Commit `53c1d64f2c69a5e476e365513130c3660eeab31f`.
`tests/test_mock_os_exit_plan_wide_review_run761.py` adds five crash stages:
RUNNING, occurrence reservation, pre-action audit, link, and synthetic
terminal. A dependent WRITE is never initiated. After each spawned worker
commits and disappears, the parent reopens Planner, occurrence, audit and
link SQLite files and calls `review_synthetic_write_plan`. The test asserts
read-only diagnosis, an uncertain root WRITE, dependent hold for RUNNING
states, unchanged underlying local counts, and zero backend calls.

**Non-claims:** four local commits are not a distributed transaction;
SUCCEEDED in a local mock journal cannot establish the outcome of a real
external action or authorization to replay UNKNOWN work.

## C — Personal Context: independent privacy veto mid-projection

Commit `c29aa1334a80ff4b0705d1d05b71626525a3fbf1`.
`tests/test_context_cross_process_projection_veto_run761.py` adds two
cross-process cases. A separate Python interpreter inserts a scoped
privacy veto after `review_personal_context` has constructed the local
bundle but before `review_fresh_nonrevoked_context` performs its final
veto check. A newly vetoed *requested* owner must reject the result.
A newly vetoed unrelated owner must not be incorrectly merged into the
requested scope; its locally returned bundle is always deny-only. The
revocation SQLite bytes never contain either raw owner ID.

**Non-claims:** the final read cannot prevent revocation immediately after
it, and the fixture does not authenticate consent, guarantee physical
erasure, or authorize downstream model, tool, export or notification use.

## D — Memory DELETE/expiry COMMIT-UNKNOWN and scope isolation

Commit `2e5ebed25b0d05cbe59290a1faddd20800de458a`.
`tests/test_memory_delete_purge_os_exit_run761.py` adds two genuine
OS-process exit cases. A child commits either an exact-revision deletion or
one bounded expiry purge and exits before returning confirmation. A cold
SQLite reader checks that the target row remains absent, the matching
terminal event appears exactly once and a different namespace's retained
row is unaffected. The old generation CAS witness is rejected rather than
used to resurrect a deleted row. These disposable fixture operations are
not user-data deletion, physical erasure across backups, or permission to
repeat an ambiguous destructive operation.

## Outstanding architectural gates

1. No common atomic transaction across Planner, occurrence, audit,
   privacy, Memory and proactive SQLite stores. A lost response is **UNKNOWN**
   and cannot be re-dispatched automatically; any prospective outbox/inbox
   or single-transaction design must be isolated and reviewed first.
2. Local clock, token, registry digest and event prefix are not trusted
   hardware time, cryptographic human consent, independently authenticated
   custody, or an externally confirmed exactly-once side-effect receipt.
3. V3 immutable model/tokenizer bytes, review-approved rights/provenance,
   physically measured runtime identity and capped cost approval remain
   blocked. PR #5 must remain Draft. No Candidate training or protected V2
   final evaluation without its explicit gate.
4. Windows/GGUF real physical-PC readiness is unverified. Do not claim an
   actual offline JARVIS PASS based on mocked Python tests.
5. PR #9 remains Draft/unmerged and is paused: absolutely no UI/frontend
   source, tests, integration or design work in this run.

## Next plan

Check each exact Run761 SHA and final checkpoint-result CI against all six
job conclusions; diagnose actual failures rather than guessing. Continue
independent Memory WAL/ABA and high-water readback, Planner persisted
terminal/READ recovery, exact PermissionGate and registry identities, trusted
audit-before-action boundaries with disconnected executor only, and
privacy-safe proactive/observation fixtures. Admit cross-component wiring
only after lower-layer exact-head GREEN evidence and retain explicit
manual quarantine for ambiguous WRITEs.
