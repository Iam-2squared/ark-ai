# Run1070 — Personal Context replay reparse admission rebase

## Exact work basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `5d9e1dfb37d7ff0769545e790da9d5dfbfeb8c50` (Run1067 checkpoint; parent CI run `44912347493` GREEN, 6/6).
- Original package: Draft PR #191, exact child HEAD `087b87d550d0fdcb981a6e29a5526ca8555efc78`; exact-head CI run `44909097904` GREEN, 6/6 on older parent `87ee86a333fb851ef21b64ce91e9b15d15e231f6`.
- Rebased child branch: `research/run1070-personal-context-replay-hardening-rebase`.
- Fresh exact-head CI is required; the older green run is not transferred.

## Change

- Pin the import-time Windows `FILE_ATTRIBUTE_REPARSE_POINT` mask as part of replay-ledger protocol authority.
- Reject policy rebinding and malformed present `st_file_attributes` metadata.
- Reject reparse-point ancestors, database leaves and SQLite sidecars before SQLite access.
- Preserve the hash-only replay schema, row format and denial-only authority.

## Regression coverage

Synthetic stat metadata and disposable local paths cover policy rebinding, malformed metadata, absent platform metadata, reparse ancestors, database leaves and SQLite sidecars.

## Limits

This is local path-admission hardening, not atomic directory-handle custody, independent storage custody, power-loss durability, trusted time, consent, disclosure authorization, revocation freshness, cross-store atomicity or external-effect proof. No live context, connector, model, ToolBackend, notification, paid service, external compute, Candidate, protected V2 evaluation, frozen-contract change, UI work, credentials, physical hardware or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**
