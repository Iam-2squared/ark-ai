# Run1079 — SQLite Memory constructor path identity

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`
- Exact parent HEAD: `394f3573e18f0d1d6a8913dbb6e7e0f562012585`
- Child branch: `research/run1079-memory-store-path-identity`
- Source commit: `3e53e29b6b466bc1421fb8c61616e739b6d64861`
- Regression commit: `88a8693cb50f015054d4cf3f0048245b7ffd8f15`

## Finding

SQLiteMemoryStore checked its current path for symlink, hardlink, sidecar and in-operation source drift, but did not retain the constructor-selected path as a store identity. Reassigning the public `path` to a different, otherwise valid regular SQLite database before a method call could redirect that store's next read or write. Existing path-alias tests did not cover a second ordinary regular database.

## Change

- Capture the exact Path object selected during construction.
- Reject path-type changes and any equal-valued or different Path object before public Memory operations process inputs.
- Recheck the constructor path identity at both read-only and writable SQLite connection boundaries.
- Preserve existing in-operation source-epoch checks, no-follow path validation, sidecar checks, WAL bootstrap, CAS semantics, and schema v1.

## Synthetic regression coverage

The new tests create two disposable regular SQLite databases, attempt to retarget one store to the other's path, and verify read/search/write refusal without modifying the foreign store. Additional tests cover equal-value Path replacement and wrong-type path replacement before query validation.

## Evidence and limits

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. This is in-process store-path identity hardening, not OS-backed directory-handle custody, a sandbox, authenticated data provenance, consent, or privacy-use authorization. The existing Memory schema, row/event format, and public CAS contracts are unchanged.

No paid service, external compute, Candidate, training, protected V2 evaluation, frozen-contract change, live personal data, credentials, physical-PC action, UI/frontend work, PR #5, PR #9 or main merge is involved. PR #8 remains Draft/unmerged; ARK/JARVIS remains NOT_PASSED.
