# ARK AI — Run412: recovery recheck, Memory multiscope callback custody and disconnected clock genesis

**Mode:** Free-only, disconnected, reversible JARVIS foundations on Draft PR #8. All outputs are *diagnostic evidence only*. No new paid APIs, external GPU, model weights, real ToolBackend execution, authenticated approval, secrets, sensors, notifications, external disclosures, protected V2 evaluation or PR merges.

**Work-basis:** Run411 canonical checkpoint `02cb665a1b11496617974b2190ca914d812c9854`. Independently checked CI #990 / run `40163698641`: completed SUCCESS across Ubuntu/Windows Python 3.11–3.13. Earlier source #988 and engineering #989 also completed SUCCESS all six.

## Implementation and regression matrix (four independent packages; +23 parametrized pytest cases)

### 1. Detached recovery archive recheck custody (+7)

- Source `src/ark/agency/synthetic_recovery_archive_review.py` — `bbeafd72a262b4204973a49fc9c4384240b71fc8`.
- Tests `tests/test_recovery_archive_recheck_epoch_run412.py` — `c8eb6af3f6522a1b7ccc6b4cffc34123f47b6589`.
- Bind the exact caller-held archive JSON and digest **objects** through both offline `_restore()` calls and independent store review. A value-equal but separately allocated digest must not evade the restart review. Pin the returned synthetic recovery receipt and its nested Planner/Occurrence/Audit/Link witness carriers across the final parser boundary. A callback that rewrites a retained `step_state`, replaces a same-value nested plan witness or changes its event count must be rejected before any receipt is returned.
- Unchanged PENDING diagnostic receipts remain inert: no automatic replay, dispatch, verified external outcome or backend call.

### 2. Single-transaction cross-namespace Memory v1 custody (+8)

- Source `src/ark/memory/synthetic_multiscope_integrity_review.py` — initial `7ad42760111a3125fe7f3de31715e1cdd818455c`, narrow established-diagnostic preservation fix `d17e2e1f4a10f20d2b8023c36790cdcfcadbeb64`.
- Tests `tests/test_memory_multiscope_carrier_epochs_run412.py` — initial `e3f850457c01381dd2ba52c89aa400cba713eaaa`, specific diagnostic alignment `3d65b00e677f482934ba5ededca1aeb953d8dc3a`.
- Capture exact original MemoryScope fields, retained per-scope events, nested `require_same_snapshot` carriers, and SQLite source Path; inspect after connection creation, BEGIN, schema verification, bounded SELECT, event replay, record hydration/hash, commit and final owner/snapshot digest callbacks. This closes temporal gaps where an earlier source/scope/witness mutation could be restored by a later callback.
- Preserve existing *source/scope changed*, *invalid retained*, *malformed cached Memory scope* and *malformed cached Memory event* diagnostics so prior regression tests keep their rejection specificity; no Memory v1 SQL schema/API changes.
- This is a coherent view only inside one SQLite read transaction, not an independently authenticated cross-database snapshot, valid consent or private-context disclosure permission.

### 3. Disconnected clock replay genesis isolation (+4)

- Source `src/ark/agency/synthetic_clock_sequence_review.py` — `cd7b3ca92898eba457a23b10f923209c659284cc`.
- Tests `tests/test_synthetic_clock_genesis_custody_run412.py` — `65f69103a89ac1ff54d783beee8d35ad7907ca63`.
- Replace dependency on reflectively mutable exported `EMPTY_CLOCK_WITNESS` for replay initialization and zero-count retained-witness validation with a fixed genesis field vector. Caller-side monkeypatching or reflective poisoning of the exported singleton must not reseed replay or redefine empty witness validity.
- This is **not** an authenticated clock, signed timestamp, monotonic hardware receipt, human issuer, or grant for external action.

### 4. Archived reserved PENDING WRITE must not be locally terminalized (+4)

- Source `src/ark/agency/synthetic_recovery_archive_review.py` — `3bc9b4151f735253cc74a755392e4a2e4a4a0dcb`, following package 1.
- Tests `tests/test_recovery_reserved_pending_run412.py` — `2e0e1df302a5d009ead4ee8923a1e5377e1fa02a`.
- An independently retained archive with `step_state=PENDING` **and an already durable matching reservation** remains unresolved if a later local Planner journal says SUCCEEDED, FAILED, BLOCKED or CANCELLED. That journal-only transition is not a verified external outcome; the archive rechecker now rejects the attempted terminal reclassification.
- Unchanged reserved-PENDING witnesses and unreserved PENDING→RUNNING witnesses remain diagnostic, with `external_outcome_known=false`, no ToolBackend invocation and no automatic replay. This is a stricter local restart boundary, not global exactly-once semantics.

## Validation integrity and known CI history

- All ten source/test writes used the normal GitHub Contents API after fresh branch-HEAD reads. No force pushes, raw Git object/ref writes, duplicate workflow dispatches or main merges.
- Historical exact-head CI #990, #989 and #988: SUCCESS all six before this run.
- New archive source CI #991 and archive tests #992 launched automatically; check their six job conclusions independently.
- Multiscope source/test CI #993/#994 exposed **7 existing test expectation mismatches** in Ubuntu Python 3.12: the earlier guard used one new generic denial message rather than established semantic distinctions; the #994 job reported 2211 passed / 7 failed, Ruff PASS. This is retained as failure evidence, not relabeled GREEN. The narrow later source change preserves the same fail-closed rejection while restoring established diagnostic categories, and the new tests were aligned with those categories. Validation is pending on exact correction HEAD #997/#998; do not transfer earlier CI results to those commits.
- The clock source/test CI #995/#996 were initially running and inherited the pre-fix Memory mismatch. The reserved-PENDING source/test CI #1000/#1001 were queued at review; do not claim their success before the exact-head jobs complete. Do not claim all-six GREEN for them without explicit checks.
- Final green status, job counts and SHA must be independently checked. No synthetic hash by itself authorizes operation or establishes external truth.

## Invariants and next review

- `RUNNING`/`UNKNOWN` WRITE is never automatically replayed or reclassified from a local Planner terminal status. The archive recheck is not an external effect receipt, cross-store atomic journal or human approval.
- Personal data never leaves disposable offline fixtures. Frozen V1/V2/Local UI/Launcher evidence, Memory v1 and ActionAudit v1 SQL schemas, and frozen V3 Contract 1 remain unchanged.
- V3 PR #5 must remain Draft/unmerged/NOT_PASSED. PR #8 stays Draft/unmerged; main unchanged.
- Prioritize: (1) exact-head CI #997/#998 regression verification and smallest fixes if needed; (2) multiple WRITE restart + independently retained audit/link prefix and pending-but-reserved diagnostics; (3) Memory CAS/expiry and privacy revocation; (4) trusted issuer/audit-before-action interfaces without live dispatch; (5) isolated V3 identity/provenance free-only gates with explicit protected-evaluation and Candidate authorization boundaries.
