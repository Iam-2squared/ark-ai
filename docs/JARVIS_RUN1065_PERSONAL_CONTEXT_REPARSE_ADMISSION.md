# Run1065 — Personal Context replay-ledger reparse admission

- Target: Draft PR #8, `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `87ee86a333fb851ef21b64ce91e9b15d15e231f6` (Run1062 foundation; exact-head CI run `44905799382` was GREEN).
- Child branch: `research/run1065-personal-context-reparse-admission`.
- Rebased from the prior isolated Personal Context replay reparse package; source and synthetic test are applied to this exact current parent.

## Change

- Pin the import-time Windows `FILE_ATTRIBUTE_REPARSE_POINT` mask as part of the replay-ledger protocol authority.
- Reject policy rebinding and malformed present `st_file_attributes` metadata.
- Reject reparse-point ancestors, the database leaf and SQLite sidecars before SQLite access.
- Preserve the hash-only replay schema, row format and denial-only authority.

## Evidence and limits

The regression suite uses synthetic stat metadata and disposable local paths only. It does not create privileged junctions or inspect live personal data. Fresh exact-head CI is required on this rebased child; no local pytest/Ruff PASS is claimed. The prior branch's green run on a diverged parent does not transfer.

This is local path-admission hardening, not atomic directory-handle custody, independent storage custody, power-loss durability, trusted time, consent, disclosure authorization, revocation freshness, cross-store atomicity or external-effect proof. No live context, connector, model, ToolBackend, notification, paid service, external compute, Candidate, protected V2 evaluation, frozen-contract change, UI work or main merge is involved. PR #8 remains Draft/unmerged.
