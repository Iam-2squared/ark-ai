# Run566 — Offline coverage shape, privacy authority custody, Memory auditability

Status: isolated, reversible, local-fixture-first work on Draft PR #8. These
changes are **NOT** completion evidence for JARVIS, V3, real sensors, real
actions, privacy consent, a trusted clock, an authenticated writer, or a
protected evaluation. No paid/external compute or Candidate was used.

## Package 1 — transcript timeline uncovered-run metrics

Source: `src/ark/offline_transcript_coverage.py`; tests:
`tests/test_offline_transcript_coverage_run565.py`.

In addition to covered frames, leading/interior/trailing uncovered totals and
integer coverage ppm, the bounded detached PNG/WAV/transcript review returns:

- `uncovered_run_count`: number of **nonzero** contiguous uncovered spans
  across the beginning, each interval between claims, and the end.
- `longest_uncovered_run_frames`: maximum uncovered span length, or zero
  when all WAV fixture frames are claimed.

Intervals are already checked for exact integer, bounded, monotonic,
nonoverlapping frame positions. The sum of the covered and three uncovered
totals must still equal the validated local WAV frame count. The original
result remains metadata-only, with no transcript text, image pixels or PCM.
Both new values enter the deterministic receipt payload; its domain changes
to `ARK-disconnected-transcript-coverage-v2` so a v1 receipt cannot silently
masquerade as the expanded shape. Three new parameter-expanded cases cover
full coverage, two interior gaps, and leading/interior/trailing gaps;
existing fixture tests also check the new metrics.

These metrics are **not** confidence, speech detection, acoustic timing
authentication, provenance, consent or actionable task results. The inputs
are local caller-supplied fixtures.

## Package 2 — Personal Context retention denial definitions

Source: `src/ark/personal_context_retention_recheck_review.py`; tests:
`tests/test_retention_recheck_preinstalled_denials_run566.py`.

Previously, the final recheck captured its four safety-denial property
definitions **after** several retention inventory reads. A preinstalled
False-only substitute could therefore become the expected descriptor.
The original denial definitions are now pinned at module import and checked
before the first SQLite review, at source-epoch checks after callbacks, and
at final result integrity checks. An exact result class substitution is
also rejected before review. Six new cases cover four preinstalled False-only
substitutes, a reentrant False-only substitution during the first inventory
read, and unchanged passive behavior.

Existing tests intentionally inject a replacement read-only inventory
function to simulate concurrent mutations. That read callback remains
replaceable for those tests; this change specifically binds the output's
four denial property definitions. A local False-only property check does
not prove legal consent or successful erasure and grants no deletion.

## Package 3 — independently reconstructible Memory ambiguity receipts

Source: `src/ark/memory/ambiguous_commit_pair_review.py`; tests:
`tests/test_memory_manual_reconciliation_receipts_run566.py`.

A dual-pass read-only post-COMMIT ambiguity review already hashed both
independent reviewer receipts internally but exposed only the overall digest.
The passive result now also exposes `triage_receipt_sha256` and
`outcome_receipt_sha256`. Together with disposition, retained event-prefix
hash, observed prefix hash and observed row hash, an investigator can
reconstruct `reconciliation_sha256` under its **unchanged** v1 domain.
Three new cases exercise unchanged, one matching local update and divergent
local row states; they recompute the final digest and assert all authority
denials. No data content or memory plaintext is returned.

Both receipts are *local unauthenticated observations*, not independent
proof of who performed a COMMIT. Matching data must never be treated as
authorization for an automatic retry or as exactly-once external execution
proof.

## Package 4 — Planner partial SUCCESS/FAILED/BLOCKED result custody

Source: `src/ark/agency/disconnected_partial_registered_failure_join.py`;
tests: `tests/test_partial_failure_archive_epoch_run566.py`.

The partial registered READ/failure archive join now retains the exact
archive/fixture result carriers after initial plan and failure-mask
validation. It rechecks them after each registered READ reviewer callback,
after every denied-authority getter and before the final output. Three new
cases cover two False-only denial-getter mutations (archive file hash or
hypothetical terminal states) plus the stable, no-dispatch baseline.
The local failure mask remains a caller assertion; archive/SQLite are not
one atomic transaction. There is no proof that a tool ran or that a later
automatic retry is safe.

## Validation and pending gates

These are **15 newly authored parameter-expanded pytest cases** in four
independent source+test packages, not a claim that 12 tests were run locally.
The repository's Python 3.11–3.13 Ubuntu/Windows CI matrix must establish
the exact final-head result. Earlier GREEN evidence belongs only to its
own SHA. No tool dispatch, external API, webcam, microphone, ASR, live
scheduling, model training, protected V2 evaluation, promotion, contract
change or main merge follows from these changes.

## Next plan / 今後の方針

1. Finish exact-head six-environment CI and correct any actual source/test
   regression through the ordinary guarded GitHub path.
2. Continue Planner FAILED/BLOCKED durable propagation and registered READ
   partial-success receipts, retaining UNKNOWN-WRITE quarantine.
3. Extend Memory expiry/generation-CAS and manual uncertain-COMMIT review;
   advance local consent-withdrawal/retention consistency and restart-safe
   Scheduler occurrence checks without real actions.
4. Keep PR #5's V3 paid compute/Candidate/approval gates closed, PR #8 Draft,
   V1/V2/Local UI/Launcher frozen, and ARK/JARVIS/V3 NOT_PASSED.
