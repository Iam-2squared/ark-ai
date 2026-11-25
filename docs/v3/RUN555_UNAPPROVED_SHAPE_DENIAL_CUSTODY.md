# Run555 — Passive unapproved shape review denial custody

## Scope and safety

This work is confined to `research/v3-learning-evaluation` (PR #5 Draft, unmerged).
It never invokes model loading, GPU, external services, training, Candidate
generation, protected V2 evaluation, promotion or billable operations. The
input remains a synthetic, **unapproved** execution-snapshot template; even
a clean shape report cannot authenticate model bytes, provenance, a reviewer,
a time source, an allowed budget or runtime identity.

## New source and adversarial regression

`src/ark/learning/offline_snapshot_shape_review.py` now retains
`UnapprovedSnapshotShapeReview` and `OfflineReadinessInventory` denied-property
descriptors **at module import**, rather than accepting whatever matching
False-valued descriptor happens to be present at the beginning of a review.
The nested inventory's denial descriptors and the final shape report's
descriptors remain checked across independent placeholder and digest
classification and after each denial callback. This does not manufacture
trusted authority, nor make Python monkeypatch checks a process isolation
boundary.

`tests/v3/test_shape_import_denial_custody_run555.py` adds **12 authored
parameter-expanded tests**: six original shape denial substitutions, four
nested inventory denial substitutions, a late shape descriptor replacement,
and an unaffected unapproved-template path. Tests assert that preinstalled
malicious False getters are not invoked and that the clean template remains
entirely non-authorizing.

The first source+test CI run exposed four **inherited tests expecting the
older `authority` diagnostic word** after a substituted inventory property.
The follow-up source change preserves the original fail-closed behavior and
includes `authority descriptor` in the error while retaining the existing
`inventory source changed` prefix. This is a diagnostic-only correction, not
a permission or validation relaxation.

## Invariants and next gates

- Readiness/shape are observations of literal JSON syntax, not proof of
  materialized artifact identity, approval, file hash provenance or consent.
- The frozen V3 Contract, Experiment 001 hyperparameters, contamination
  review, split counts, and approval boundaries are unchanged.
- Validate the final source/test/note HEAD in six CI jobs. A green matrix
  establishes repository test evidence only, not protected evaluation PASS.
- The unresolved immutable HF revision/byte hashes, human-approved dataset,
  provider billing cap, environment/device identity and explicit user consent
  remain **blocked**. Work on independent free JARVIS foundations continues.
