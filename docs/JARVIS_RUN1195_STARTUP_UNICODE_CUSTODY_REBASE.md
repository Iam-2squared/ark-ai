# Run1195 — Startup readiness Unicode dependency custody rebase

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD at branch creation: `2df6b261554428cd01871f2723ce87c4dd05e4b4`.
- Reconciled source: Draft PR #375 exact child HEAD `113b04a271833a5764a5593c1c4bdc6730760178`.
- Original source PR #363 exact child HEAD: `6c695a9be4e25e7c04050d148f6157a740f0a4f7`.
- New child branch: `research/run1195-startup-readiness-unicode-custody-rebase`.

## Change

Both disconnected startup graph and freshness-lease validators pin the import-time `unicodedata` module and exact category function, reject every Unicode General Category `Cf` scalar in component IDs, dependency IDs, failure codes, schema revisions and lease requirement identifiers, and recheck dependency identity around admission. Existing C0/C1, NUL, bidi, UTF-8 byte-budget, DAG, freshness and denial-only semantics remain.

## Regression coverage

Synthetic identities cover U+0600/U+FFF9/U+E0001 across applicable fields, ordinary Japanese labels, and Unicode classifier/module substitution denial before unreviewed category callbacks receive caller identifiers.

## Limits

Diagnostic-only fixtures; no physical readiness probe, credential, device, backend, startup, notification or dispatch authority. Unicode category pinning is an in-process dependency-integrity guard, not a Python sandbox or independent runtime attestation.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No paid/external compute, paid APIs/services, Candidate generation/promotion, protected V2 evaluation, credentials, physical hardware, destructive operation, frozen-contract change, UI/frontend work or main merge. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
