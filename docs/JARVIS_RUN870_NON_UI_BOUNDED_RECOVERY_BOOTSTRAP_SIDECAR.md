# Run870 — bounded disconnected recovery and native SQLite fixture ingress

Observed report authoring clock: 2026-11-14T12:01:35.923Z UTC / 2026-11-14 21:01:35 JST. This is an ordinary reporting clock, **not** trusted audit time, consent, provenance, an attested process identity, or an action execution clock.

Work-basis: Run869 checkpoint `12f233f009edf148028a2a1efee65f3308236beb`. Branch: `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). UI feature work remains suspended; PR #5 and #9 stay untouched and Draft/unmerged.

## Four reversible, disconnected work packages

1. **Scheduled UNKNOWN quarantine — bounded per-occurrence SQL read.** Source commit `c5d4f86b8e468f8bc3476c0438ea12fc45a6b0b9`. The single snapshot SELECT for the claimed `occurrence_id` now has `LIMIT 2`; rejecting more than one match retains exactly the existing denial semantics. Three synthetic tests in `tests/test_schedule_unknown_quarantine_bounded_sql_run870.py`, commit `9c128811b045cc667b0a272c7b853746827f0611`, trace the actual SQLite statement and verify UNCHANGED/LOCALLY_QUARANTINED/ADVANCED_OTHER stay denied for notification, execution and automatic replay. A two-row cap is not a proof of writer authenticity or external effects.

2. **READ journal recovery — bounded receipt hydration.** Source commit `38aa6094bf1a73b3f3c4342c5598a6c384f561af`. The second, post-`_scan` recovery receipt SELECT now uses SQLite `LIMIT ?`, with `_MAX_ROWS + 1`, and rejects overflow before constructing Python receipt carriers. Original retained-tip checks, fixed 128-row budget, atomic read transaction and deny-only snapshot claims remain. Four tests in `tests/test_read_journal_bounded_recovery_query_run870.py`, initial commit `29c5cd185a649d96e9b97fd2fabc147134232e32` and SELECT-specific trace refinement `00caaa5a6420731066247e9451b4689b3b833d13`, exercise 0/1/3 receipt snapshots and stale-tip denial. The test trace explicitly distinguishes the recovery SELECT from the already-bounded internal `_scan` query.

3. **SQLite new-ledger bootstrap — no unbounded `sqlite_master` Python list.** Personal Context source commit `1b90900f6ba1954307f34b3cdd8bb0cd0205358c`, Quarantine source commit `f6f73d17073cb693c1c5fcc593199b73baf67285`, formatting refinement `6dc3e293c9783974e4480b21b8c4daae2f46aff4`. The old `tuple(conn.execute("SELECT name FROM sqlite_master"))` becomes a one-row `SELECT 1 ... LIMIT 1` existence query during create-only bootstrap. Two tests in `tests/test_sqlite_bootstrap_nonempty_path_race_run870.py`, commit `79760089d696e089cac1afb0bcfd2113a9d2fe31`, synthesize a foreign schema planted **after** lexical path validation but before SQLite open; both stores fail closed and retain the foreign marker. This is a single-process controlled TOCTOU fixture, **not** a proof of race-free file opening. Neither store adopts or migrates the planted database.

4. **POSIX descriptor-relative sidecar path encoding — typed early rejection.** Source commit `27df2df686cfa49799f48f52eb7228053ff922f6`. `os.fsencode` is checked under a bounded `try` before any directory/file inspection; a native unencodable path now raises `SQLiteSidecarCustodyRejected`, not a raw exception containing the fixture pathname. Two POSIX-only synthetic tests in `tests/test_detached_sqlite_sidecar_unencodable_path_run870.py`, commit `3f1a880722e8c94a38cef67d45024298f8221dfd`, exercise both capture and review. No SQLite connection or payload read is introduced.

**Total: 11 new synthetic test cases authored**; not claimed all-environment GREEN merely by being committed.

## CI diagnosis and evidence boundaries

The initial work-basis checkpoint [CI #43588169206](https://github.com/Iam-2squared/ark-ai/actions/runs/43588169206) was independently verified **GREEN 6/6** (Ubuntu/Windows Python 3.11–3.13). The subsequent source/test updates automatically triggered separate CI runs, without manual duplicate dispatch.

On the intermediate quarantine/bootstrap source HEAD `6dc3e293c9783974e4480b21b8c4daae2f46aff4`, [CI #43592024064](https://github.com/Iam-2squared/ark-ai/actions/runs/43592024064) reported an actual **Ruff E501** at `personal_context_replay_ledger.py:412` (101 characters); this was repaired through the normal GitHub Contents API in `22b30dab985296313d04c3e082e7769d3a56917d`. This failure is historical, not evidence against a later fixed HEAD. New branch HEAD jobs require exact-SHA verification; no local full pytest/Ruff or physical-PC evidence is asserted in this report.

## Scope and remaining blockers

The following remain **NOT_PASSED**: independent sidecar custody and SQLite path-to-open races after the final check; last-close WAL/SHM unlink/coherence; Memory COMMIT-UNKNOWN and cross-store atomicity; Planner manual UNKNOWN disposition; authenticated one-shot permission, trusted audit-before-external-action and external effect exactly-once. None of these local fixtures authorize replay, consent, notification, camera/microphone, a real ToolBackend, or Candidate training.

V1/V2/Local UI/Launcher contracts and frozen evidence are unchanged; protected final evaluation closed; no UI/frontend modifications, paid services, GPU, Candidate/adapter generation, credentials, irreversible action, or main merge.

## Safe next work

1. Resolve latest exact-HEAD six-job CI and fix only real regressions without weakening guards.
2. Examine disposable SQLite WAL/SHM final-close race and Memory/ActionAudit COMMIT-UNKNOWN independently.
3. Strengthen Planner UNKNOWN lineage and Personal Context revocation/expiry coherent snapshot.
4. Integrate Registry/PermissionGate/atomic preaction with mock-only effects after exact prerequisite GREEN evidence.
