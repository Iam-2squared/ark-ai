# ARK AI — Run493 CI recovery, inert observation and retention review

**Status: NOT_PASSED.** All work is free-only, isolated and reversible. No live actions,
hardware acquisition, paid compute, real Candidate, V2 final suite opening,
frozen-contract changes, main merge, Tool dispatch, consent or erasure.

## Exact work basis and branches

- Started PR #8 from the Run492 checkpoint HEAD
  `2283b700b682ad710c648009d14f230d657ed899`.
- Started PR #5 from `d96ac89ac576483514bc6d715015a5f0736faaca`.
- PR #8 source/test head before this documentation write:
  `b3a9c941ee80c768ed8e9db0a69d4195c18dae7d`;
  OPEN / DRAFT / UNMERGED.
- PR #5 final source/test head:
  `7bd2ad6450c3a887351705f11054313de49c809c`;
  OPEN / DRAFT / UNMERGED.
- GitHub Contents updates used current file blob SHAs and fresh PR head reads.
  No raw Git-object bypass, force push, hidden route or manual duplicate CI run.

## Five coherent work packages

1. **Scheduler retained witness / Run492 CI regression.**
   `src/ark/agency/disconnected_due_reservation.py`, source fix commit
   `e80161e7c61ed703c1c9fb680e965a6e742b4566`.
   On a callback-modified retained count/hash carrier, classify custody drift
   *before* semantic validation. Both checks remain fail-closed and preserve
   pre-COMMIT rollback; this repairs the exact-message regression without
   deleting its existing test.
2. **Memory retained CAS / Run492 CI regression.**
   `src/ark/memory/disconnected_witness_ledger.py`, source fix commit
   `04520d17373d9cfe78ad2d6920bc6d68a80b7265`.
   Check retained input and denied execution authority immediately after the
   SQLite inspection callback, *before* validating the independently observed
   witness. Both checks still precede an INSERT and remain enforced after it.
   The existing authority-spoof regression remains intact.
3. **V3 Windows local file identity / Run492 CI recovery.**
   `src/ark/learning/identity.py`, source fix commit
   `7bd2ad6450c3a887351705f11054313de49c809c`.
   `Path.lstat()` and `os.fstat()` may disagree on Windows ctime semantics
   for an otherwise identical file. Compare nonzero file IDs using
   `os.path.samestat`, size and mtime across the sources; retain independent
   **full** epoch comparisons for descriptor-before/after and path-before/after,
   and POSIX cross-source ctime/mode checks. Nonregular/multilink and redirected
   descriptors remain rejected. No weight/model/network operations.
4. **Observation lineage non-authority.**
   `src/ark/observation_lineage_review.py`, source commit
   `4be98d3b836cf3a75c382750bece9d2bc08c7d50`;
   `tests/test_observation_lineage_result_authority_run493.py`, test commit
   `3865f053f94d56fcfbe43a1cc823e5f4af16a657`.
   A reflected class-property spoof on an exact result DTO must not turn
   a metadata lineage review into capture, disclosure or dispatch permission.
   Three parametrized rejection cases plus one positive local case.
5. **Personal Context retention non-authority.**
   `src/ark/personal_context_retention_review.py`, source commit
   `1adac559a7822371c22884ba9826ecf4c9a025e0`;
   `tests/test_retention_inventory_result_authority_run493.py`, test commit
   `b3a9c941ee80c768ed8e9db0a69d4195c18dae7d`.
   An exact retention inventory DTO must reject fabricated erasure-complete,
   delete-authorized or context-use-authorized properties. Three parametrized
   rejection cases plus one positive synthetic Memory inventory case. No
   deletion or export operation.

**New tests:** 4 pytest functions, **8 parametrized-expanded cases**, across
the two new test files. Two existing regression failures are fixed by source
ordering, not by relaxing/deleting tests. No claim of local independent pytest.

## CI results and exact source heads

- Run492 PR #8, source `ca92275b755d502a9e1ddfa69b04272d1667c7ae`,
  [Actions #1762 / 41157215683](https://github.com/Iam-2squared/ark-ai/actions/runs/41157215683):
  **FAIL** 6/6, including 2 exact error-message expectation mismatches.
- Run492 PR #5, source `d96ac89ac576483514bc6d715015a5f0736faaca`,
  [Actions #1761 / 41157173741](https://github.com/Iam-2squared/ark-ai/actions/runs/41157173741):
  Ubuntu **3/3 GREEN**, Windows 3.11 GREEN and Windows 3.12/3.13 FAIL.
  Descriptor-vs-path epoch comparison was the shared cause of 18/19
  Windows failures (job-dependent totals).
- Fixed PR #5 exact source `7bd2ad6450c3a887351705f11054313de49c809c`,
  [Actions #1767 / 41161362307](https://github.com/Iam-2squared/ark-ai/actions/runs/41161362307):
  **6/6 GREEN**, Ubuntu and Windows Python 3.11–3.13.
- PR #8 intermediate fixed-source `04520d17373d9cfe78ad2d6920bc6d68a80b7265`,
  [Actions #1766 / 41161305228](https://github.com/Iam-2squared/ark-ai/actions/runs/41161305228):
  **IN PROGRESS** when checked.
- PR #8 Observation source/test `3865f053f94d56fcfbe43a1cc823e5f4af16a657`,
  [#1769 / 41161452273](https://github.com/Iam-2squared/ark-ai/actions/runs/41161452273):
  **IN PROGRESS** when checked.
- PR #8 latest retention source/test `b3a9c941ee80c768ed8e9db0a69d4195c18dae7d`,
  [#1771 / 41161548147](https://github.com/Iam-2squared/ark-ai/actions/runs/41161548147):
  **QUEUED** when checked. No latest-head GREEN claim.
- Independent local full pytest/Ruff: **NOT VERIFIED** in this invocation.
  No duplicate/manual workflow dispatch was requested.

## Frozen evidence and safety boundary

- Memory v1 contract blob `b6e93821ecd69270a7634aceb20775dc36e9953c`;
  Agency contract blob `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`.
- V3 frozen Contract blob `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`;
  companion hash blob `176154514bd6be22685ca0555bc682c3bd8d45dc`.
  Read-only same-SHA checks; no frozen evidence changed.
- No independent writer authentication, attested monotonic clock,
  cross-database atomicity, provable actual external outcome, human consent,
  real Tool authority or reliable exactly-once physical side effect follows
  from any local fixture. UNKNOWN WRITE remains quarantined.
- V3 still blocked on model/tokenizer/tool/runtime bytes, real approvals,
  cost authorization and other controlling conditions. PR #5 stays Draft.

## Next plan / 今後の方針

1. Verify PR #8 latest-source six-job CI on exact SHA; on failure inspect
   logs and fix only the affected path via normal permitted file writes.
2. Further isolate Memory CAS/historical snapshots and Planner unknown-WRITE
   manual recovery with registry-bound Tool and trusted-clock audit barriers.
3. Extend privacy revocation/expiry review, Scheduler occurrence/replay
   fencing and disconnected Observation fixtures; integrate only after
   exact-head GREEN lower-level invariants.
4. Continue free-only V3 identity/reproducibility/approval guard audits. Stop
   at any paid compute, Candidate, frozen suite, human decision or main merge
   boundary until explicit authorization.
