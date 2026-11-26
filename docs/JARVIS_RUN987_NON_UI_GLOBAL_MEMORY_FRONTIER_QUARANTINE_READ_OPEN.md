# ARK AI Run987 — non-UI Memory frontier / synthetic quarantine / disconnected READ opening

**Scope:** Draft PR #8, `research/jarvis-foundations` only. This is non-normative,
free-only disconnected/local-first hardening, not a V1/V2/Launcher/UI contract or
a trusted action authorization. **JARVIS overall NOT_PASSED.**

## Basis and source packages

Work-basis/prior checkpoint HEAD: `801eeab1a56317294fcc50bce97c874de4715fe8`
(Run986). Source/test and repair commits in order:

1. **Memory global event mutation fence** — production
   [`5a9aa297`](https://github.com/Iam-2squared/ark-ai/commit/5a9aa297d5ad96f0d75bd02c609b169433543914);
   [10 authored regression cases `5d0e4c59`](https://github.com/Iam-2squared/ark-ai/commit/5d0e4c59dab62f242f1d7f9626e7f11e58aab144).
   Run original bounded/dense AUTOINCREMENT frontier validation within each
   Memory `put`/`delete`/`purge_expired` writer transaction before private
   target hydration or row/event mutation. Detect missing global events,
   rewound `sqlite_sequence` and duplicate marker rows, including when
   target owner/scope is otherwise unaffected. Test verifies unchanged durable
   memory rows, event rows and sequence rows after denial; valid lifecycle still
   appends `create/update/delete/expire` records.

2. **Synthetic overdue-quarantine policy before filesystem** — production
   [`082b3535`](https://github.com/Iam-2squared/ark-ai/commit/082b3535778bf082dcc1de03e76a409968977181);
   [5 authored regression cases `8d4ba817`](https://github.com/Iam-2squared/ark-ai/commit/8d4ba81789860c589200aae00ea0c054d34ff0f9).
   Validate bounded recurrence and synthetic policy class descriptors before
   `lstat`/sidecar or SQLite access. Four hostile policy variants must not
   reach either filesystem or DB I/O; one valid cold restart preserves an
   unauthenticated genesis witness. No real scheduler notification or dispatch.

3. **Disconnected READ cold-open no-create race** — production
   [`a0dee4bd`](https://github.com/Iam-2squared/ark-ai/commit/a0dee4bdfa3b879edda994bcfa45f9ea852910cd);
   [2 authored regression cases `c51fd0d1`](https://github.com/Iam-2squared/ark-ai/commit/c51fd0d1d209e60b868462d7ca4d65a0acaaead2).
   Cold `DisconnectedReadJournal.open` uses an SQLite URI `mode=rw` rather
   than a potentially file-creating bare pathname. A file unlinked between
   lexical path admission and the native connect now fails instead of creating
   an unmarked replacement. Exact digest-only legitimate restart remains
   available. Lexical validation still does **not** prove atomic path/handle
   custody against a malicious concurrent replacement.

## CI regression discovered and narrow repair

The first Memory test-head workflow
[CI #44481606612](https://github.com/Iam-2squared/ark-ai/actions/runs/44481606612)
failed on Ubuntu Python 3.11/3.12/3.13 during this invocation.
Ubuntu 3.11 completed **19,045 PASS / 2 FAIL / 1 SKIP**. Existing
`test_memory_scoped_event_wal_race_run705.py` instruments the
`_require_dense_committed_memory_events` **read hook**, then opens a
second WAL writer from that callback. Reusing that instrumentable hook
inside writer transactions made the nested writer reenter while a SQLite
`BEGIN IMMEDIATE` already held the writer slot, causing
`sqlite3.OperationalError: database is locked`.

The narrow source repair is
[`a43563ce`](https://github.com/Iam-2squared/ark-ai/commit/a43563cef06fd396c0491aa177e33bc2abb3f42b):
pin the original dense event checker as
`_ORIGINAL_MUTATION_EVENT_FRONTIER` immediately after its definition;
writer mutation paths use that original checker, and
`events()` keeps the instrumentable read hook. **The original
global high-water denial is preserved, not bypassed or weakened.**
This is a local instrumentation/reentrancy repair, not independent
tamper-proof provenance. Its exact-head CI is pending, not yet GREEN.

**17 new authored cases total across the three packages.** New tests
are not certified PASS until matching exact-head all-six CI succeeds.
No local full pytest, external GPU, physical-PC GGUF, or live tool
execution is claimed. All commits used the normal GitHub Contents
API with live PR HEAD re-read before every write; no duplicate workflow
dispatch, force-push, merge, or protected-contract change.

## Boundaries and next work

All work stays on Draft/unmerged PR #8. Main and gated Draft PR #5,
paused Draft PR #9, frozen V1/V2/Local UI/Launcher evidence and contracts
must remain untouched. No paid potentially billable action, new
credentials, external compute, protected V2 evaluation, real Candidate
generation/promotion, filesystem/network tool effects, automatic
COMMIT-UNKNOWN retry, or irreversible privacy deletion.

Next: verify exact-head CI for the repaired Memory/READ/Quarantine
packages; fix any real failures narrowly. Then prioritize Memory
WAL/SHM path custody and CAS/ABA; Planner crash/terminal recovery;
registry-bound PermissionGate, durable one-shot authorization,
trusted-clock audit-before-action with disconnected/mock only;
privacy-safe Personal Context, proactive replay review, Observation
fixtures and V3 free-only controls. **UI development remains paused.**
