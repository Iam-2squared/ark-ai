# JARVIS Run564 — Memory ambiguous COMMIT dual-observer manual reconciliation

This free-only, reversible local fixture module closes a **diagnostic coherence** gap between the two existing opt-in SQLite Memory generation-CAS outcome reviewers. It is NOT a transaction coordinator, retry engine, caller authentication system, final PASS gate, or main integration.

## Implementation

New `src/ark/memory/ambiguous_commit_pair_review.py` uses the already existing:

- `postcommit_uncertainty_review.review_uncertain_memory_commit`
- `generation_cas_outcome_review.review_memory_generation_cas_outcome`

Both reviewers receive the same exact `SQLiteMemoryStore`, `MemoryWrite` and pre-write `MemoryGenerationCASToken`. The bridge pins the original no-authority result properties and child function identities and rechecks the caller input epoch across callbacks. It accepts only exact child result classes, verifies all denial properties remain **False**, requires that the retained and observed event-prefix SHA-256 claims agree between reviewers, and maps compatible classifications into one manual-only result:

| Local Memory triage | CAS observation | Bridge disposition |
|---|---|---|
| `LOCAL_UNCHANGED` | `UNCHANGED_OBSERVED` | `LOCAL_UNCHANGED_REVIEW` |
| `ONE_MATCHING_UPDATE_VISIBLE` | `ONE_MATCHING_UPDATE_OBSERVED` | `MATCHING_ROW_MANUAL_REVIEW` |
| `INDETERMINATE` | `DIVERGED_OBSERVED` | `DIVERGED_MANUAL_REVIEW` |

The complete read-only pair runs **twice**, rejecting a changed classification, row digest or observed prefix across passes. The report includes only dispositions and bounded SHA-256 evidence, never Memory content, metadata or actor identity. It denies automatic retry, WRITE, trusted-clock proof and caller attribution by original immutable descriptors.

## Tests and limitations

`tests/test_memory_ambiguous_commit_pair_run564.py` covers retained unchanged, one matching update, divergent update, forged prefix, four false-only authority substitution cases, callback mutation, result disagreement and second-pass drift: **11 authored parameter-expanded test cases**. Tests use temporary local SQLite fixtures. The new read-only code does not retry an uncertain COMMIT, delete data, dispatch tools or change a frozen Memory contract.

A matching row can have been written by another actor with identical bytes. Two successive SQLite reads do **not** prove a coherent global transaction or exclude a writer changing state immediately after the last read. A caller-retained token and original Python callables are not trusted custody of independent history. Missing/deleted/recreated generations or conflicting classifications remain a **manual investigation blocker**. There is no user or hardware identity, durable cross-store atomicity, consent authentication, trusted time, or exactly-once external action guarantee.

CI must be evaluated on the exact code+test head and subsequent documentation/checkpoint heads. No tests are claimed GREEN until corresponding completed GitHub CI evidence is observed. Draft PR #8 remains unmerged. PR #5 remains Draft/unmerged; Candidate creation, protected V2 evaluation and spending are not authorized. **ARK/JARVIS/V3 NOT_PASSED.**
