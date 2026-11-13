# ARK AI Run842 — non-UI privacy race / proactive bounds / Memory high-water

This report is for synthetic, disconnected, free-only code on Draft PR #8.
It is **not** an integration PASS, real physical-PC run, trusted-clock evidence,
consent, model capability, external action, or authorization to replay writes.

## Work basis and boundaries

- Initial observed `research/jarvis-foundations` / Draft PR #8 HEAD:
  `606d4905378fc81f8972c9f1c09f311077e6f6dc` (Run841 checkpoint).
- Previous exact checkpoint CI [#43397692655](https://github.com/Iam-2squared/ark-ai/actions/runs/43397692655)
  completed **GREEN 6/6** Windows/Ubuntu Python 3.11–3.13.
- Earlier source/test [#43397176437](https://github.com/Iam-2squared/ark-ai/actions/runs/43397176437)
  was **FAIL 1/6**, Ubuntu Python 3.12, with
  `test_disconnected_revocation_competing_processes_preserve_veto[False]`:
  child exits `[0, 4]` instead of assumed `[0, 0]`. The same final Run841
  checkpoint later passed 6/6, indicating a timing-dependent observation,
  **not** an independently proven production root cause.
- No PR #5 or PR #9 edits; no UI/frontend, protected evaluation, Candidate,
  new account/secret, physical hardware, paid service, tool dispatch or main merge.

## Package A — explicit fail-closed process evidence

[Commit b0ccc173](https://github.com/Iam-2squared/ark-ai/commit/b0ccc1730a50bec2ae3bb997bccc756c0753a3ed)
revises the existing disposable SQLite two-process privacy-revocation test.
Same-scope races still require one success/one denied exit; separate scopes can
produce two successes or a success plus a **fail-closed** denial when local path,
sidecar, or transaction checks race. No production safety check was relaxed.

A synthetic denied child could have committed immediately before the post-COMMIT
path recheck failed; therefore exit 4 is **not evidence of no durable write**.
The test now reads the actual persisted veto witness, checks that every confirmed
successful child has its expected digest, permits **only** the two synthetic owner
digests, requires at least one successful independent child and every persisted
owner's veto to reject reuse. It does not replay failed operations, equate absent
veto with consent, or claim a reliable success outcome from an ambiguous exit.
This is a test-contract correction, not proof that SQLite conflicts are solved.

## Package B — fixed-width proactive SHA ingress

[Source 1c06f05a](https://github.com/Iam-2squared/ark-ai/commit/1c06f05aaba8405a6804375a9d0a1f736b86e51c)
requires exact 64-character SHA-256 hex label width **before** regex matching.
[Tests 32030144](https://github.com/Iam-2squared/ark-ai/commit/32030144b6a0f71195b029b53c5f3619328855cc)
add **17 authored parameterized cases** covering short/overlong candidate,
policy and history digests plus an unchanged denial-only valid fixture.
No scheduler is activated and no notification is sent.

## Package C — global append-log integrity in manual uncertain-COMMIT review

[Source 60adfb67](https://github.com/Iam-2squared/ark-ai/commit/60adfb67bb1884e4b79ac6bba2ac70ccce5b55a4)
reuses the Memory CAS outcome reader's global `memory_events` high-water
validation from the **same** `BEGIN` read snapshot used for manual triage.
It pins the validator's original callable identity before private SQLite access.
A coherent target-row prefix can otherwise conceal removed unrelated events.

[Tests ad2cbcc7](https://github.com/Iam-2squared/ark-ai/commit/ad2cbcc77b75557cd8ebe730e2d07ec5b69b3037)
add **6 authored cases**: unrelated event deletion, missing/duplicate/regressed
`sqlite_sequence` high-water, substituted validator preaccess rejection,
and intact manual-only observation. Every SQLite mutation is limited to
temporary synthetic test databases; **none** authorizes automatic retry, write,
erasure, external action or caller attribution. Independent retained witnesses
are still required against valid-file replacement or rollback.

## Evidence precision and next priorities

- 23 new authored test parameterizations + one existing test assertion update
  are **NOT 23 CI-confirmed passes**.
- First test-repair [CI #43403857677](https://github.com/Iam-2squared/ark-ai/actions/runs/43403857677)
  and proactive source/test [#43403968137](https://github.com/Iam-2squared/ark-ai/actions/runs/43403968137)
  were **IN PROGRESS** on latest early inspection; latest Memory
  source/test [#43404237793](https://github.com/Iam-2squared/ark-ai/actions/runs/43404237793)
  was **QUEUED**. These statuses can evolve; check exact run/head before claiming GREEN.
- No local full 14k+ pytest matrix, Windows-hosted test, model, hardware or
  source/contract freeze was directly executed during this invocation.
- Next: inspect exact latest-head six-job CI, repair genuine failures without
  weakening revocation/continuity gates; continue disposable WAL/SHM held-FD
  correlation without treating normal SQLite last-close unlink as proven
  ARK-specific cause; then proceed with coherent Memory CAS, Planner UNKNOWN
  and Registry/Permission/Audit/Mock integration only after exact-head evidence.

**Overall ARK/JARVIS: NOT_PASSED.** Frozen V1/V2/Local UI/Launcher contracts
and protected evaluation remain untouched. PR #5/#8/#9 remain Draft and
unmerged; paused PR #9 is not a development lane.
