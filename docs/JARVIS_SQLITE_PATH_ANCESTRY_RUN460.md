# Run460 — disconnected SQLite ancestry boundary (2026-10-27 JST)

Status: **SOURCE AND TESTS SAVED; EXACT-HEAD CI QUEUED; NOT PASSED**.
Branch: `research/jarvis-foundations` / PR #8 Draft, not merged.
Entry HEAD: `93a906b17256a84b73c87f3ba7c1e858d1b6eddc`.
Final source/test HEAD: `0805459319f99d0d8a74ea545654a08c5f7f9525`.

## Threat model and three independent packages

A fixture SQLite store which checks only the final file and its immediate
parent can traverse a symlink in an earlier ancestor (grandparent, etc.).
During CREATE this can redirect filesystem writes outside the intended
fixture tree; during reopen it can redirect a read/write journal handle.
A lexical `..` component also defeats the principle of refusing ambiguous
source paths. This is relevant to disconnected privacy denials, scheduler
due-slot reservations and read-result receipts.

Each of the following existing ordinary GitHub Contents paths now rejects
lexical `..` and verifies EVERY `Path.parents` item with `lstat` as a real
non-symlink directory, on initialization and every existing path-check call.

| Independent package | Modified source blob | New regression test blob |
| --- | --- | --- |
| Privacy veto | `src/ark/disconnected_privacy_veto.py` `754604e05f5aeec7a0b94dbfbea7e83cc4702bbf` | `tests/test_disconnected_privacy_veto_ancestry_run460.py` `d45f3df950b169b4d25394580baf9a8a4b87e21e` |
| Due-slot reservation | `src/ark/agency/disconnected_due_reservation.py` `26368f35f41cceb93448bd643ed1b23058fc42bf` | `tests/test_disconnected_due_reservation_ancestry_run460.py` `00642d66a0a768a9460078a9f1391bc312307d8d` |
| READ receipt journal | `src/ark/agency/disconnected_read_journal.py` `34dd72753fa373d900973194fdd131892287e416` | `tests/test_disconnected_read_journal_ancestry_run460.py` `cb3e2b98daa65049539e8411f5f47d1ef8daf0ab` |

Each regression file defines four cases: normal nested operation, nested
symbolic ancestor rejected before creation, symbolic ancestor rejected
on reopen, and lexical parent escape rejected. A symlink-creation restriction
in Windows/Linux fixtures causes the corresponding symlink test to SKIP,
rather than pretending it was exercised.

## Verification without fabricated PASS

- GitHub readback confirmed all **six** exact saved blob IDs above.
- All changed source and test files passed a deterministic <=100-column
  line-length inspection via readback.
- A separate local Python 3.13.5 four-case **path-guard logic smoke** passed:
  nested real parent admitted, lexical parent traversal rejected, missing
  ancestor rejected, and symbolic grandparent rejected. The smoke mirrors
  the new local guard logic; it is **not** execution of the repository tests
  or a source-level/runtime integration test.
- **12 new pytest cases are SAVED but not executed**. The running environment
  cannot clone github.com because DNS resolution fails. Do not report
  12 PASSED, entire-repo pytest, Ruff, Windows/Linux, or all-six CI GREEN.
- GitHub Actions spawned automatically by normal PR file commits:
  `#1396`/`40389594467`,
  `#1397`/`40389658443`,
  `#1398`/`40389706509`,
  `#1399`/`40389756551`,
  `#1400`/`40389836731`,
  and **final source/test** `#1401`/`40389879282`;
  all **QUEUED** at the exact-head audit. No manual dispatch,
  rerun, cancellation or external paid runner.
- Historical `#1244`/`40237313817` still has three Windows
  `Run pytest` steps IN PROGRESS and three historical Ubuntu failures.
  The later 45-minute watchdog cannot retroactively change that old run.
  The queue contained 152 QUEUED and 6 IN PROGRESS at inspection.

## Residual boundaries

`lstat` ancestry inspection is NOT an atomic secure open. An adversary able
to rename or swap directories between the check and the subsequent SQLite
open can still create a TOCTOU race; Windows-specific junction/reparse-point
coverage has not been established on real hardware. Neither matching
hashes nor SQLite quick_check prove authentic sources, independently
retained witness custody, coherent multiple-database WAL snapshots,
consent, a trusted clock, irreversible erasure, authorized Tool dispatch,
or external exactly-once effects.

No frozen V1/V2/Local UI/Launcher, Memory v1 schema, ActionAudit v1, V3
Contract 1, official protected evaluation, Candidate approval or
real-world execution contract was edited. PR #5 stays Draft/unmerged;
PR #8 remains detached and reversible. No billable action undertaken.

## Next plan / 今後の方針

1. Check the naturally queued **exact source/test HEAD** `#1401`
   and follow-up document/checkpoint runs; if it fails, inspect the first
   factual failure and fix with unchanged safety semantics.
2. Evaluate handle-pinned parent/open identity and Windows junction
   fixture coverage independently, without claiming those are solved
   by this path-only patch.
3. Prioritize Memory CAS/event/expiry coherent snapshots and Planner
   UNKNOWN/WRITE quarantine in independent workstreams; integrate
   privacy or scheduler ledgers only after their exact dependencies
   become GREEN. Preserve free-only, protected-evaluation and approval gates.
