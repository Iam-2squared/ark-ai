# Run1158 — Memory cross-process pinned-WAL CAS rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `9b1dbc439ec338e2840d9dc493e724c651617e60`.
- Rebased from Draft PR #113 exact child HEAD: `87dbeab4a9c13252f81c03c28195098e4687b452`.
- Source exact-head CI: [44806223097](https://github.com/Iam-2squared/ark-ai/actions/runs/44806223097) GREEN, 6/6 on the source head only; it does not transfer to this rebase.
- New child branch: `research/run1158-memory-wal-cas-rebase-latest`.
- Test: `tests/test_memory_cross_process_pinned_wal_cas_run993.py`.

## Scenario and assertions

A spawned read-only process pins a SQLite WAL snapshot containing one synthetic Memory row and its create event. Two other spawned processes start together and attempt a generation-fenced update using the same retained pre-write token.

The regression requires:

- The WAL reader does not prevent the independent writer processes from completing.
- Exactly one writer commits revision 2; the competing writer receives a CAS conflict.
- The pinned reader continues to see the original revision and event prefix until it rolls back.
- A fresh read after rollback sees the single committed update and matching event.
- Reusing the retained pre-write token after restart is denied.
- SQLite quick_check remains `ok`.

## Safety and limits

All paths, owners, namespaces and content are synthetic temporary fixtures. The test dispatches no tool and performs no external effect. The generation token is a local CAS witness, not consent, trusted time, writer attribution or external-action authorization. This is a cross-process storage regression, not proof of independent custody or protection against offline database rollback.

Test-only. No Memory production source, v1 DDL/public API, or frozen contract changes. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed before that run completes. No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, UI/frontend work, or main merge is included. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched; ARK/JARVIS remains NOT_PASSED.
