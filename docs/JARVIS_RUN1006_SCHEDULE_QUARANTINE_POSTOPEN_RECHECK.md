# Run1006 — schedule quarantine SQLite post-open path recheck

**Work basis:** Draft PR #34 exact head `2ac894cfda27b3c92031d7aa97471f96282f6d84`. This isolated child keeps PR #34 and Draft PR #8 unchanged.

## Gap

The schedule-quarantine ledger already performed no-follow path checks before SQLite opens, including Windows reparse-point rejection. Its constructor and later read/write opens did not repeat path admission after SQLite returned a connection. A path could therefore be replaced during the open interval and the newly opened handle could reach the first transaction/query without a second pathname check.

## Change

- Add one shared checked-open helper for `rwc`, `ro` and `rw` URI modes.
- Re-run the existing exact local path admission immediately after `sqlite3.connect`, before any transaction, PRAGMA or application query.
- Close the newly opened connection before propagating a failed post-open admission.
- Use the helper for both constructor bootstrap/restart validation and later read-only/read-write ledger access.
- Recheck the pinned source/policy identity after later opens.

## Regression coverage

Four parameterized synthetic cases cover read-only and read/write access plus create-enabled and existing-ledger constructor opens. Each test opens a disposable SQLite file, changes only the subsequent `Path.lstat()` metadata to report a Windows reparse point, requires rejection, and verifies the just-opened connection is closed.

## Limits and safety

The second pathname check narrows the open race but is not descriptor identity verification, atomic dirfd custody, authenticated storage or TOCTOU protection. Tests use synthetic metadata and disposable SQLite only; no privileged junction, real schedule execution, timer, notification, consent, trusted clock, external effect, paid service, GPU, credential, Candidate, V2 opening, frozen-contract change, UI work or main merge is involved. Quarantine remains non-authorizing.

**Exact-head CI is pending for this child. No PASS is claimed. Overall ARK/JARVIS remains NOT_PASSED.**
