# ARK AI Run836 — non-UI SQLite WAL lifecycle forensics

**Scope:** local-only, disposable privacy revocation and Memory WAL diagnostics.
**Overall ARK/JARVIS:** NOT_PASSED. Nothing here authorizes real tools,
consent, user-data access, Candidate training, protected evaluation or UI work.

## Work basis and preserved gates

Work-basis HEAD: 9c170825b03de66440549ebd2b1d0a5625c6096a (Run835).
Branch: research/jarvis-foundations, Draft PR #8, no main merge.
Frozen V1/V2/Local UI/Launcher evidence unchanged; PR #5 remains protected,
Draft and unmerged; PR #9 remains paused, Draft, unmerged and untouched.
No paid service or GPU, external compute, credentials, real user SQLite files,
real tool backend, training, protected evaluation, private disclosure or deletion.

## NEW: two independent source/test packages

1. **Privacy revocation controlled two-process WAL diagnostic.**
   [Source fbbe9a43](https://github.com/Iam-2squared/ark-ai/commit/fbbe9a431497bb89ddba445788bdc4460cb1eb1f)
   creates scripts/diagnose_revocation_wal_processes.py. Each iteration uses
   TemporaryDirectory and a fixed synthetic scope. WAL mode is explicit;
   two separate Python interpreters synchronize at a release gate. An optional
   --wal-keeper holds a disposable SQLite handle through both child exits.
   Child reports are size-capped, deny duplicate JSON keys and nonfinite
   numbers, allowlist status/phase, and never echo private path/error text.
   Independent read-only schema, version, row, and quick-check review
   rejects child-only success. Any refusal is an anomaly, never auto-retried.
   A synthetic revocation is not authenticated human consent or deletion.
2. **Privacy tests.**
   [Commit c1a9d400](https://github.com/Iam-2squared/ark-ai/commit/c1a9d40026b355791bd1e3553d4f7d8ebf0aae28)
   adds 25 parameterized cases: input/parser budgets, independent process
   winner/loser, durable corruption/absent-source rejection and path-free
   no-replay reporting. Initial CI found Ruff B017 in the test's broad
   exception assertion. The exact argparse.ArgumentTypeError assertion was
   saved by [repair ceddc308](https://github.com/Iam-2squared/ark-ai/commit/ceddc308cdf4085e05839cb8507830d39aa05e58).
   No source safety predicate or failing behavior was weakened.
3. **Memory disposable sidecar lifecycle observation.**
   [Source b52db211](https://github.com/Iam-2squared/ark-ai/commit/b52db211a9749ddcf62787eea812bf1e9c439ed2)
   adds opt-in --lifecycle-snapshots to the existing Memory process diagnostic.
   Passive lstat samples only -wal/-shm/-journal at prepared, ready, child-exit
   and closed process epochs. Output reports bounded aggregate categories:
   absent, single, unlinked, multilink, nonregular, unavailable. It never
   dereferences, adopts, rewrites or retries a rejected sidecar; the default
   diagnostic behavior is unchanged.
4. **Memory tests.**
   [Commit 8894ee19](https://github.com/Iam-2squared/ark-ai/commit/8894ee19ddca187b4e4b2b905faa95d8239a0e69)
   adds five cases for lstat categories, no symlink traversal, keeper-mode
   real two-process fixture, opt-in aggregate and default opt-out.

**35 test cases AUTHORED (25 revocation + 5 Memory + 5 ActionAudit), NOT independently confirmed PASS.**
No frozen Memory schema or production permission, action, or Memory write
API was changed. Fixture success is not a real external side-effect witness.

## NEW — independent ActionAudit WAL lifecycle lane

5. **ActionAudit sidecar lifecycle.** [Source 09b17f20](https://github.com/Iam-2squared/ark-ai/commit/09b17f20f621215139f2671224c27abbe2d81e11) updates the opt-in disposable ActionAudit two-interpreter test utility with passive, path-free lstat categories for -wal/-shm/-journal at prepared, ready, each child exit, and closed phases. It does not invoke any real tool/backend or relax sidecar admission.
6. **ActionAudit regression tests.** [Commit 19676209](https://github.com/Iam-2squared/ark-ai/commit/1967620960fc8405bf64799ed1fbbb65f6006e2e) adds five cases including a real keeper-mode two-process synthetic audit/readback, symlink non-dereference, opt-in bounded counts and opt-out behavior. No synthetic audit record proves an external effect. Automated [CI #43368166047](https://github.com/Iam-2squared/ark-ai/actions/runs/43368166047) was IN_PROGRESS for source and [CI #43368200814](https://github.com/Iam-2squared/ark-ai/actions/runs/43368200814) QUEUED for test HEAD at the 2026-11-13T13:52:26 JST inspection; both are **NOT YET GREEN**. No duplicate workflow run dispatched.

## SQLite source facts vs hypothesis

SQLite documentation explains that WAL mode has transient shared-memory
-shm indexes and that clean closure of the last connection usually performs
checkpoint and unlinks the -wal/-shm files. A keeper can alter this lifecycle,
making keeper/no-keeper comparisons a useful diagnostic control. It does
not prove a historically observed zero-link -shm path was benign nor rule out
an alias. References:
https://www.sqlite.org/wal.html
https://www.sqlite.org/walformat.html

Earlier Run835 intermediary
[CI #43361855339](https://github.com/Iam-2squared/ark-ai/actions/runs/43361855339)
had two Ubuntu failures: one Memory separate-source create returned a
fail-closed SIDECAR_REJECTED; another revocation two-process test expected
the losing contender to report already revoked but observed a different
fail-closed rejection. The later exact Run835 checkpoint
[CI #43362813338](https://github.com/Iam-2squared/ark-ai/actions/runs/43362813338)
was GREEN 6/6. The WAL/SHM race root cause remains **UNRESOLVED**.

## CI snapshot — 2026-11-13T13:47:48 JST

- Baseline 9c170825 [#43362813338](https://github.com/Iam-2squared/ark-ai/actions/runs/43362813338): GREEN 6/6, Windows/Ubuntu Python3.11–3.13.
- Revocation source fbbe9a43 [#43367359478](https://github.com/Iam-2squared/ark-ai/actions/runs/43367359478): IN_PROGRESS.
- Revocation first tests c1a9d400 [#43367443738](https://github.com/Iam-2squared/ark-ai/actions/runs/43367443738): FAIL 6/6, exact Ruff B017 in new test.
- Memory source b52db211 [#43367629380](https://github.com/Iam-2squared/ark-ai/actions/runs/43367629380): FAIL 6/6, inherited same Ruff B017.
- Memory tests 8894ee19 [#43367679551](https://github.com/Iam-2squared/ark-ai/actions/runs/43367679551): FAIL 6/6, same inherited Ruff B017.
- Test correction ceddc308 [#43367737614](https://github.com/Iam-2squared/ark-ai/actions/runs/43367737614): IN_PROGRESS. New exact-head GREEN not yet known.
- Automatic CI only; no duplicate manual workflow runs.

## Reproduction and next plan / 今後の方針

Explicit opt-in fixture commands on an existing local development checkout:

- python scripts/diagnose_revocation_wal_processes.py --iterations 4
- python scripts/diagnose_revocation_wal_processes.py --iterations 4 --wal-keeper
- python scripts/diagnose_memory_sidecar_startup.py --iterations 4 --lifecycle-snapshots
- python scripts/diagnose_memory_sidecar_startup.py --iterations 4 --wal-keeper --lifecycle-snapshots

Only fresh owned temp directories are used; never supply a user database.
First confirm latest exact HEAD six-job CI and repair any genuine failure
without weakening alias/sidecar refusal. Compare keeper/no-keeper and
bootstrap/WRITE/close epochs; do not automatically retry ambiguous commits.
Next: Memory COMMIT-UNKNOWN manual triage, Planner persistent UNKNOWN,
registry-bound permission, audit-before-action Mock Executor, privacy-safe
Personal Context and free-only V3 gates. No JARVIS PASS or user approval
has been established.
