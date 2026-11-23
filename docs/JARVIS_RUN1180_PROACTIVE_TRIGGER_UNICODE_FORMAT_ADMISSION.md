# Run1180 — Complete Unicode format-control admission for proactive trigger policy

**Status:** implementation saved on an isolated Draft branch; exact-head CI pending. No PASS is claimed.

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `a27344061d5abc5304c44c03f7457005deb4c89d`.
- Child branch: `research/run1180-proactive-trigger-unicode-format-controls`.

## Finding and change

The durable synthetic proactive trigger policy validates owner, namespace, definition and policy revision before deriving policy digests and preparing local deduplication markers. Its hand-maintained formatting-control list missed valid Unicode General Category `Cf` values.

- Pin the import-time `unicodedata` module and exact `category` function.
- Reject all `Cf` characters at initial construction and retained-policy revalidation.
- Preserve existing C0/C1, NUL, bidi, UTF-8 and 512-byte limits.
- Keep the ledger disconnected and deny-only; no notification, dispatch, automatic replay, trusted clock or consent authority is added.
- Add synthetic tests for U+0600, U+FFF9 and U+E0001 across all four policy identity fields, reflected mutation, and classifier substitution.

## Validation and limits

- No local pytest/Ruff result is claimed.
- Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.
- Tests use synthetic policy values only. No real scheduler, notification, Tool, external action, or private user data is used.
- Unicode classifier pinning is an in-process dependency-integrity check, not a Python sandbox or independent runtime attestation.
- No paid/external compute, paid service, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, frozen-contract change, UI work or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**
