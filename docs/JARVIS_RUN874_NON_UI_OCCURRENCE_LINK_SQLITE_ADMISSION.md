# ARK AI Run874 — disconnected occurrence/audit-link SQLite pre-hydration

**Scope:** non-UI, free-only, synthetic local SQLite and fail-closed evidence.
**Work-basis HEAD:** `cb45d20d883efa9128901cc7d090278c3db8b775` (Run873 checkpoint).
**Latest complete code/test/diagnostic HEAD:** `609ed54392daf28fec194203b33766dcbfd7120f` (before this report).
**Branch:** `research/jarvis-foundations`, Draft PR #8 only. PR #5 and UI PR #9 untouched.

## Packages saved

1. **Durable occurrence reservation admission.** `src/ark/agency/durable_occurrence_review.py`
   now preflights exactly three schema catalog objects and a bounded DDL byte budget
   using SQLite aggregate checks before Python DDL hydration; caps catalog SELECT to 3,
   quick_check to 2 diagnostic rows, and validates the <=10,000 row/type/UTF-8-width/
   timestamp budget inside SQLite before Python materializes stored identifiers.
   Create-only unversioned bootstrap now probes one SQLite-only catalog row. Existing
   row regex and ordering replay remain intact. Source commits: `595ad853...`,
   `2c0569ee...`, `609ed543...`. The last repair preserves the exact legacy
   `row integrity failed` diagnostic substring while distinguishing SQL preflight.
2. **Occurrence-to-audit synthetic link admission.**
   `src/ark/agency/synthetic_occurrence_audit_link_review.py` bounds schema DDL
   hydration and quick_check, preflights 10,000-row and exact storage/UTF-8 byte
   widths in SQLite, bounds replay to 10,001 SQLite rows, and replaces unversioned
   bootstrap enumeration with an existence probe. Existing hash-chain, time order,
   audit identity and no-dispatch receipts remain mandatory. Source commit:
   `52ab5d4556fa923e7115ce4cefe18c637869c0a1`.
3. **Regression and race diagnostics.** New
   `tests/test_occurrence_audit_link_sqlite_prehydration_run874.py`, commit
   `5803cede72470ec6348abed8b3212097ba406fbd`, authors **10** cases
   across both modules: bounded normal diagnostics, two bogus diagnostics denied,
   planted foreign TABLE/VIEW denied without adoption, and a 131,072-byte BLOB
   rejected before Python row hydration with durable malformed fixture retained.
   Existing `tests/test_privacy_revocation_cross_process_run425.py` modified
   in `fb0fa75434dc79ae5bfcd9e2c53909d835561f24` to print bounded
   *non-private* loser rejection and coherent durable COUNT/MIN/MAX timestamp
   on a test failure; strict two-process success/one-winner assertions unchanged.
   No test was skipped, loosened or reclassified.

## Verification and CI limitations

- GitHub comparison of Run873 HEAD to `609ed543...`:
  six ordinary Contents API commits, exactly two non-UI Python modules and two
  test files changed; all PR gates preserved. No raw Git-object bypass, force
  update, source overwrites of concurrent work or UI edits.
- Independent local SQLite smoke: both table DDLs create exactly three
  `sqlite_master` objects; correctly sized sample rows yield aggregate
  `(1, 0)`; malformed BLOB identifiers yield `(1, 1)`. This is *not*
  full ARK pytest or Ruff and not a trustworthy action/consent authority.
- Prior Run873 checkpoint `cb45d20d...`: [Actions #43602764426](https://github.com/Iam-2squared/ark-ai/actions/runs/43602764426)
  **GREEN 6/6** (Ubuntu/Windows Python 3.11–3.13), prior HEAD only.
- Initial occurrence-source [#43606765822](https://github.com/Iam-2squared/ark-ai/actions/runs/43606765822)
  had Ubuntu 3.11/3.13 FAIL on seven legacy `row integrity failed` regex checks.
  [#43607060931](https://github.com/Iam-2squared/ark-ai/actions/runs/43607060931)
  also showed this known old-message mismatch; [#43607258316](https://github.com/Iam-2squared/ark-ai/actions/runs/43607258316)
  includes the intermediate incomplete message repair.
  Final source commit `609ed543...` restores the contiguous legacy substring;
  **its [CI #43607435427](https://github.com/Iam-2squared/ark-ai/actions/runs/43607435427)
  was QUEUED at last observation; six-job result not proven.** Additional
  automatic runs for later documentation/checkpoint commits do not prove this
  final source until they complete. No duplicate manual CI was requested.
- Historical intermittent [#43596487033](https://github.com/Iam-2squared/ark-ai/actions/runs/43596487033)
  showed Ubuntu Python 3.13 privacy revocation loser rejection and Windows
  Python 3.11 `memory SQLite sidecar ... link_count=0` on an active -wal
  during competing startup. These remain unresolved; no weakening of symlink,
  hardlink, last-client-close or COMMIT-UNKNOWN denials.

## Non-authority and next steps

Synthetic SQLite validation cannot authenticate human consent, source custody,
trusted clocks, independent retained witnesses, cross-store atomicity, or
external exactly-once effects. No real tool execution, GPU, model training,
Candidate generation/promotion, protected V2 final evaluation, paid API/service,
new credentials, main merge or UI work occurred. PR #5/#8/#9 remain Draft.

Next: conclude exact latest HEAD all-six CI, repair only real failures; isolate
WAL/SHM last-close and privacy loser races using bounded non-sensitive evidence;
advance Memory CAS/expiry and Planner UNKNOWN manual recovery; couple immutable
Registry, exact PermissionGate, durable audit-before-action and mock-only executor
only after their prerequisite exact-head GREEN contracts.
