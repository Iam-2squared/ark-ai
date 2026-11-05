# ARK AI — Run641: concurrent local Memory, coherent WAL snapshots and Planner restart

Status: **non-UI, disconnected, reversible, unmerged Draft PR #8 evidence**.
Work basis: `ff16031827114213c5c40746904ba26c2acafb05`, whose GitHub Actions run [#42089536764](https://github.com/Iam-2squared/ark-ai/actions/runs/42089536764) finished **GREEN (6/6)** before this work. This report makes no claim about full JARVIS or authenticated execution.

## New packages and reproducible scopes

1. **Generation CAS concurrent writers** — `tests/test_memory_generation_concurrent_cas_run641.py`, initial commit `68c93d99b33452ae99d6bb49044319554c34a77c`. Three synthetic owner labels share two independently opened SQLite handles. Both observe one generation; two threads race a synchronized update using the same retained token. Exactly one success and one conflict are required, with one new row/event and denied stale replay. No remote database or real personal data. Initial CI [#42097096523](https://github.com/Iam-2squared/ark-ai/actions/runs/42097096523) failed **Ruff E731**, because the test originally assigned a lambda to a local variable. Source/test semantics were preserved by replacing it with a def at `2e1881c55b12a21357a5a85bbf45de7e1e30ee8f`; do not count the initial run as PASS.
2. **Parallel independent Planner roots** — `tests/test_planner_independent_root_concurrency_run641.py`, commit `3c9eb6338b961478f01a5d93da1e6c22e764c87b`. Two journal objects concurrently commit independent RUNNING roots with equal synthetic timestamps. Restarted replay requires both ambiguous roots, then FAILED or CANCELLED must block only its dependent branch. The unrelated branch may finish and start its child; the final RUNNING child is **UNKNOWN** on restart, not automatically replayable. No backend is called.
3. **Coherent multi-namespace WAL read** — `tests/test_memory_coherent_wal_clock_race_run641.py`, commit `d44e1a140e0da8e60c3e2e909456704638d07704`. For both namespace orders, a separate local SQLite writer commits two updates from the reader's synthetic clock callback *after the reader's first SQLite snapshot read*. The first result must show both older revisions; a new transaction must show both updated revisions. This verifies a single coherent SQLite snapshot under WAL, not trusted clock or content provenance.
4. **Finite expiry and generation lifecycle** — `tests/test_memory_cas_retention_expiry_lifecycle_run641.py`, commit `f0eef073116e6dd2b54d7db42542864c46665194`. CAS refuses to extend or clear a finite deadline, permits shortening, refuses update at expiry, then requires purge + fresh-create lifetime and rejects the old generation token. Rejected writes must leave alignment evidence unchanged. This is only a local retention constraint; it cannot authorize irreversible erasure.

## Validation and epistemic limits

All added cases are **authored** regression tests, not local pytest PASS claims. Local GitHub clone could not resolve `github.com` DNS; the canonical validation surface is existing GitHub Actions CI on the exact branch HEAD. The first source/test run failed due to a test-only Ruff issue, corrected without touching frozen contracts or application source. Runs with later package coverage must be checked on their exact commit SHA and *all six* Ubuntu/Windows × Python 3.11–3.13 jobs before any GREEN claim. A successful test does not imply OS-backed provenance, consent, trusted-clock audit, actual external exactly-once execution, physical-memory erasure, or user-approved operation.

No source DDL/migrations, UI/frontend, external tool dispatch, real microphone/camera, paid service/GPU, Candidate generation/promotion, V2 final evaluation, PR #5 or #9 changes, or main merge occurred in these packages. Existing PR #5 must remain Draft and protected; PR #9 UI development remains paused.

## Next plan / 今後の方針

1. Review exact-head CI for the test-only lint repair and the newest four-package commit. If FAIL, use actual job logs and a narrow correction; do not trigger duplicate workflow runs.
2. If GREEN, extend **independent** fault injection for Memory CAS on expiry and unknown outcomes, and Planner terminal/restart recovery. Keep runtime execution disabled until ToolRegistry, PermissionGate, durable occurrence, and audit-first safety gate dependencies have matched HEAD evidence.
3. Continue read-only/free-only Personal Context and observation backend contract review; preserve all frozen evidence. Do not merge, promote, spend or activate external execution without the specified user authorization.
