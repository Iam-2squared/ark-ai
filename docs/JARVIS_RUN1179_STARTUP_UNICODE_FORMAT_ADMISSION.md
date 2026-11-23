# Run1179 — Complete Unicode format-control admission for startup readiness

**Status:** implementation saved on an isolated Draft branch; exact-head CI pending. No PASS is claimed.

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `a27344061d5abc5304c44c03f7457005deb4c89d`.
- Child branch: `research/run1179-startup-readiness-complete-format-controls`.

## Finding and change

The disconnected startup graph and its freshness lease independently maintained hand-written Unicode formatting-control lists. Those lists rejected common bidi, zero-width and C1 characters but missed other Unicode General Category `Cf` values.

- Pin the import-time `unicodedata` module and exact `category` function in both validators.
- Reject all `Cf` characters in component IDs, dependencies, failure codes, schema revisions, and lease requirement IDs.
- Preserve the existing C0/C1, NUL, bidi, UTF-8, byte-budget, DAG, freshness, and denial-only semantics.
- Keep readiness diagnostic-only: no startup, dispatch, notification, clock, or hardware authority is added.
- Add synthetic coverage for U+0600, U+FFF9 and U+E0001, all component identity fields, lease fields, and classifier substitution.

## Validation and limits

- No local pytest/Ruff run is claimed.
- Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.
- Fixtures are synthetic. No physical readiness probe, file, SQLite store, credential, device, or backend is opened.
- Unicode category pinning is an in-process dependency-integrity guard, not a Python sandbox or independent runtime attestation.
- No paid/external compute, paid service, Candidate, protected V2 evaluation, credentials, physical hardware, destructive operation, frozen-contract change, UI work or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**
