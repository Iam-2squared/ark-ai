# Run1192 — Personal Context and Observation Unicode custody rebase

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD at branch creation: `2df6b261554428cd01871f2723ce87c4dd05e4b4`.
- Reconciled source: Draft PR #362, exact child HEAD `ff3eed56d9cf3a366c8244edd1525bd65f252ada`.
- New isolated child branch: `research/run1192-personal-context-observation-unicode-rebase`.

## Change

This rebase retains the two independent privacy-boundary improvements from PR #362 while deliberately excluding its proactive-state hunk, which is being handled separately by PR #372.

- Personal Context policy revisions now pin the import-time `unicodedata` module and exact category classifier, reject every Unicode General Category `Cf` scalar, and recheck classifier identity after scanning. Existing control, UTF-8 and byte-budget checks remain.
- The disconnected Observation fixture adapter pins the same classifier in its existing fixture-budget integrity guard, rejects all `Cf` scalars in source/privacy labels before private fixture hashing, and rechecks the guard after admission.
- Observation Envelope v1, Memory v1, public constructors, and frozen evaluation contracts are unchanged.

## Regression coverage

Synthetic-only tests cover U+0600, U+FFF9 and U+E0001 in Personal Context policy revisions and both Observation metadata fields; classifier substitution is denied before the replacement callback receives caller text or private fixture bytes. Positive Japanese metadata remains accepted.

## Validation and limits

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff result is claimed. This is an in-process dependency-integrity guard, not a Python sandbox, authenticated observation provenance, consent, disclosure, notification, Tool authorization or dispatch.

No paid/external compute, paid APIs/services, Candidate generation/promotion, protected V2 evaluation, credentials, physical hardware, destructive operation, frozen-contract change, UI/frontend work or main merge is involved. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
