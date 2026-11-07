# Run463 — Disconnected SQLite hardlink alias guard (unmerged)

**Work basis:** Run462 checkpoint `a67046751344f193c81239ca04e943496f267ef6`.
**Branch/PR:** `research/jarvis-foundations` / #8 Draft, not merged.
**Final source/test HEAD:** `80a81dd42eb8c5ada5d3dd6a37315cb1a3549514` (checked against PR and branch before this evidence commit).

## Security defect and remediation

A symlink or symbolic ancestor had already been rejected, but three synthetic
SQLite stores accepted an existing **hardlinked database main file** because
`stat.S_ISREG` alone cannot distinguish a normal file from an additional
link to another pathname. An unexpected hardlink can alias storage despite
a stable fixture path, so a malicious or misconfigured fixture could read or
write a file also reachable by another name.

Three existing *disconnected* path gates now require the regular file's
`st_nlink == 1` whenever the file exists. The check is made before initial
SQLite open and normal reopen. It does not grant read/write permission.

- Privacy veto: `src/ark/disconnected_privacy_veto.py` at blob `2bef2c311f5cbc942cee15b557da97e095ed9110`; commit `5394d56531da3b8966327eaf313f710f79b873ee`.
- Scheduler due reservations: `src/ark/agency/disconnected_due_reservation.py` at blob `4678e7f2ba70a7b564a8f1573ddb85e2db154cdd`; commit `d4775380625b856627407220360cce11eab49ad8`.
- Planner mock READ journal: `src/ark/agency/disconnected_read_journal.py` at blob `d20fbbe43a4931f12419510352b27da5c49b7256`; commit `828cd9337971debadd59832b953fa81675ccd88c`.
- Shared negative/normal fixture tests: `tests/test_disconnected_sqlite_hardlink_fence_run463.py` blob `ba9da95332c372a77bcd789c60165cef0129d79c`; commit `80a81dd42eb8c5ada5d3dd6a37315cb1a3549514`.

Each of three fixture ledgers is tested at the original and alias pathname:
six parametrized test cases expect fail-closed rejection with link count two;
after unlinking only the extra alias, the original fixture can be read again.

## Evidence and limits

- All four GitHub blobs were re-fetched from the new PR HEAD, with the
  expected guards/test names present and no lines exceeding 100 columns.
- An **isolated local** Python 3.13.5 SQLite + POSIX hardlink smoke case
  passed: one file -> two links -> one file and normal SQLite reopen.
  This is **not** the repository's six parametrized pytest cases.
- New repository pytest cases **NOT EXECUTED** in this runtime because there
  is no full checkout and github.com DNS resolution failed; Ruff, complete
  pytest and Windows/Linux six-matrix GREEN are **NOT VERIFIED**.
- Source/test CI #1423, run `40415539405`, exact HEAD
  `80a81dd42eb8c5ada5d3dd6a37315cb1a3549514`, was QUEUED
  at inspection. No manual workflow re-run, cancel or dispatch.
- Old #1251, run `40246006387`, had three Ubuntu failures on its
  old HEAD: one observation-carrier expectation and two privacy-check
  callback-count expectations. Their current tests were re-read and already
  corrected on later HEADs; newer matrix PASS is still missing. Historical
  Windows jobs remained IN PROGRESS and are not proof of a current-head result.

**Boundaries:** Link counts do not prove exclusive control of the bytes or
prevent directory/file/sidecar replacement after the check (TOCTOU).
Windows reparse points/junctions and SQLite -wal/-shm/-journal sidecars
require separate, exact-platform examination. These are synthetic fixture
stores only; no Memory v1/frozen schema or V2 contracts changed. No owner
authentication, human consent, trusted time, cross-store atomicity, real
Tool dispatch, actual notification, irreversible action, paid compute,
Candidate generation or main merge.

## Next plan

1. Get exact HEAD CI GREEN before considering dependent integration.
2. Design descriptor/handle custody for main file *and* SQLite sidecars,
   accounting for POSIX and Windows separately; no false atomicity claim.
3. Continue Memory event/row CAS/expiry and Planner UNKNOWN-WRITE quarantine
   in distinct lanes without external effects or protected evaluation.
