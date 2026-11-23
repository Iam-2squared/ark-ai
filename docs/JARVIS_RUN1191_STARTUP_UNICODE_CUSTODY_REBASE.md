# Run1191 — Rebased startup readiness Unicode dependency custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `c1b7b3d2dfe38242fcbe3d6d4930c3bbf53e9390`.
- Rebased from Draft PR #363 exact child HEAD `6c695a9be4e25e7c04050d148f6157a740f0a4f7`.
- Original child exact-head CI [45159355292](https://github.com/Iam-2squared/ark-ai/actions/runs/45159355292) was GREEN on the prior child head only; it does not transfer.
- New child branch: `research/run1191-startup-readiness-unicode-custody-rebase`.

## Change

The disconnected startup graph and freshness-lease validators pin the import-time `unicodedata` module and exact `category` function, reject every Unicode General Category `Cf` scalar across component IDs, dependency IDs, failure codes, schema revisions and lease requirement identifiers, and recheck the dependency around admission. Existing C0/C1, NUL, bidi, byte-budget, DAG, freshness and denial-only semantics remain.

## Regression coverage

Synthetic identities cover U+0600, U+FFF9 and U+E0001 across the applicable fields, ordinary Japanese labels, and Unicode classifier/module substitution. The fixtures deny before unreviewed category callbacks can receive caller identifiers.

## Limits

Diagnostic-only local fixtures. No physical readiness probe, file, SQLite store, credential, device, backend, startup, notification or dispatch authority is exercised. Unicode category pinning is an in-process dependency-integrity guard, not a Python sandbox or independent runtime attestation.

No paid/external compute, paid API/service, Candidate generation/promotion, protected V2 evaluation, credentials, physical hardware, destructive operation, frozen-contract change, UI/frontend work or main merge. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
