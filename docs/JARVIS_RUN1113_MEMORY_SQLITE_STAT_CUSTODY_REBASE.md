# ARK Run1113 — rebase Memory SQLite stat-policy custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD: `4f9e44532cc25dfe57059021519717441399155b`.
- Rebased child branch: `research/run1113-memory-stat-reentrant-rebase`.
- Prior child PR #269 branch: `research/run1111-memory-stat-reentrant-rebase`, exact head `f0fdcd7b8b3809d30744f57ad0dd1d51361b1026`.
- Prior exact-head CI: [45019515216](https://github.com/Iam-2squared/ark-ai/actions/runs/45019515216), GREEN on the prior child head only; it does not transfer to this rebase.

## Change

Reapplies the Memory SQLite path-policy guard: import-original stat module and classifiers are pinned, and policy identity is rechecked after filesystem/metadata callbacks, including missing-leaf handling and reentrant `st_mode` / Windows `st_file_attributes` accessors. Classification uses captured predicates; the bounded one-time recheck for an already-unlinked regular SQLite sidecar remains unchanged.

## Preserved semantics and limits

Memory v1 DDL/API, row/event integrity, CAS semantics, expiry behavior and SQLite transaction semantics are unchanged. Tests use temporary paths and synthetic metadata only; no private Memory database is opened. This remains repeated pathname metadata admission, not atomic directory-handle custody, authenticated storage, independent provenance, a sandbox, or TOCTOU protection.

No local pytest/Ruff PASS is claimed. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No paid/external compute, Candidate, protected V2 evaluation, credentials, physical hardware, frozen-contract change, UI work, or main merge occurred. PR #5 and PR #8 remain Draft/unmerged. **ARK/JARVIS remains NOT_PASSED.**
