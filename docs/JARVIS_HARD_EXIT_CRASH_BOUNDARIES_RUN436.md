# ARK JARVIS — Real Process-Exit SQLite Fault Matrix (Run436)

## Scope and authority

This document records **new disposable local SQLite test fixtures**, not production
execution or demonstrated green test evidence. Every child Python interpreter
terminates via `os._exit` at a chosen durability boundary. Parent tests reopen the
exact fixture database and compare persisted rows to the only allowed outcome.
There is no hardware fault/power loss, filesystem replacement, authenticated
clock, consent issuer, real ToolBackend, notification, GPU or external compute.
Each tested SQLite store commits independently; no cross-file atomic transaction
or external exactly-once guarantee is asserted.

Work basis at invocation opening:
`6de366b0c4e53169c0ac927db6168f5e70d44189`.
All changes were made by normal GitHub Contents writes on Draft PR #8,
`research/jarvis-foundations`; existing frozen schemas and main are unchanged.

## Three independent packages — nine expanded test cases

| Package and commit | Hard stop and retained evidence | Expected restarted invariant |
| --- | --- | --- |
| Memory pre-event, `a9e7ba8662c0e4949ff74fd864ed89924c23c3c0` | Terminate immediately before a Memory audit event after row insertion | One uncommitted row/event transaction rolls back: 0 rows and 0 events; first CAS creation remains possible locally. |
| Memory post-COMMIT, same commit | Terminate when a MemoryRecord is constructed after committed row + event | Exactly one revision-1 row and matching content-free create event survive; retry with `expected_revision=0` conflicts. |
| Occurrence post-COMMIT, same commit | Terminate during synthetic receipt construction after one-shot reservation COMMIT | Reservation survives; the same token is rejected with either the previous or a fresh occurrence ID; no backend invoked. |
| Proactive post-COMMIT, same commit | Terminate during inert trigger receipt construction after marker COMMIT | One prepared trigger remains after re-open; repeat preparation hits the interval policy; no notification or execution. |
| ActionAudit pre-COMMIT, `a40852b985faddc009949bbe828c73e885537eea` | Terminate after SQL INSERT but before connection context commits | No audit event survives; a fresh local fixture audit append can be made (not authorization for any action). |
| ActionAudit post-COMMIT, same commit | Terminate at ActionAuditEvent construction after context-manager commit | Exactly one content-minimized audit event survives; no claimed external outcome. |
| Privacy revocation post-COMMIT, same commit | Terminate after SQLite commit and before `revoke()` returns | One scope-hashed veto persists after re-open; `assert_not_revoked` rejects and duplicate `revoke` cannot regrant. |
| Planner pre-COMMIT, `7ac700b7671cd628d89caaa071cd9c39c9fe6d66` | Terminate after Planner event/header SQL updates but before commit | Header and event count remain zero; PENDING state is preserved, without invented result. |
| Planner post-COMMIT, same commit | Terminate after local journal commit, before receipt is returned | Header/event counts both one; RUNNING is ambiguous and restart must refuse re-entering RUNNING from revision zero. |

Files:
- `tests/test_hard_exit_local_durability_run436.py` (4 expanded cases).
- `tests/test_hard_exit_audit_privacy_run436.py` (3 expanded cases).
- `tests/test_hard_exit_planner_journal_run436.py` (2 expanded cases).

All subprocess fixtures use `sys.executable`, bounded `subprocess.run(timeout=35)`,
unique disposable `tmp_path` databases, deterministic synthetic identifiers, and
assert the exact child exit status before checking SQLite. Parent reopens are real
separate-process recovery reads, not mock exceptions.

## Validation evidence and interpretation

Python AST parsing was performed locally on the three new test modules and
their embedded child scripts; no syntax errors were found. This is **not**
pytest, Ruff or a runtime cross-platform test. No complete local repository
clone was available and no full local suite was executed.

Normal PR Actions runs observed:
- Exact HEAD `a9e7ba8662c0e4949ff74fd864ed89924c23c3c0`:
  **#1245 / 40243820095 — QUEUED** at inspection.
- Exact HEAD `a40852b985faddc009949bbe828c73e885537eea`:
  **#1246 / 40244016815 — QUEUED**.
- Exact final executable/test HEAD
  `7ac700b7671cd628d89caaa071cd9c39c9fe6d66`:
  **#1247 / 40244183888 — QUEUED**.

These are different source HEADs. Neither an older GREEN nor a later
document-only run can be substituted for exact-head validation. No manual
rerun/duplicate dispatch was requested. New test cases are **ADDED, NOT
CONFIRMED PASSING**.

## Threat-model boundaries

A crash between *independent* SQLite stores can leave Planner RUNNING without
an Occurrence/Audit/Link row, or a reserved PENDING with no external outcome.
It must remain quarantined: never automatically replay UNKNOWN/RUNNING or
reserved PENDING WRITEs. Per-file row/event atomicity does not imply a
cross-file transaction or an authenticated proof of action completion.

Synthetic one-shot reservations, audit events, local clocks, and privacy vetoes
do not create trustworthy consent. An external attacker with write access
could alter an entire database; fixture row hashes do not stop coordinated
rewrites. Parent-read invariants are about local SQLite crash behavior, not
OS-level abrupt power failure, durable disk barriers, network partitions,
external service acknowledgement, or real-world exactly-once operation.

## Next dependency-aware work

1. Wait only for an actual Actions runner to execute #1247; inspect failing
   logs and correct only through normal Contents APIs if needed. Keep
   Windows, Python-version, Ruff and pytest assertions explicitly unverified
   until exact HEAD results exist. Do not flood a queued matrix with reruns.
2. After the older detached recovery-bundle source and new hard-exit tests
   have exact-head GREEN, test a separate restarted READ→WRITE→READ→WRITE
   chain with independently retained Planner/Occurrence/Audit/Link witnesses.
3. Preserve no-replay, immutable registry binding, exact-type PermissionGate,
   memory CAS/event integrity, and privacy revocation freshness while
   extending independent free-only fixtures.
4. Real hardware, credential/issuer integration, paid compute, protected V2
   final evaluation, real Candidate generation/promotion, frozen-contract
   edits, and any main merge remain strictly gated.
