# ARK Run1322 — exact Personal Context revocation scope ingress rebased

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD after Run1317 Memory ingress integration: `77d3b2f50d258bb3694afc0d03830e0d44644961`.
- Child branch: `research/run1322-context-revocation-exact-scope-rebase-20261125`.
- Rebased the local revocation hardening from Draft PR #497 / Run1316. Its prior exact-head CI [45453428666](https://github.com/Iam-2squared/ark-ai/actions/runs/45453428666) was GREEN 6/6 on the old parent only; it does not transfer.

## Finding and change

The revocation digest boundary accepted an exact `MemoryScope` object but called its `__post_init__` validator before requiring exact built-in `str` owner and namespace fields. The frozen MemoryScope contract accepts `str` subclasses, so overridden subclass methods could run during privacy-veto digest validation.

The local `SyntheticContextRevocationLedger` now snapshots owner/namespace references and rejects non-exact built-in strings before calling the scope validator. It rechecks field references after validation and hashes only the captured exact strings.

## Regression coverage

- Exercise both owner and namespace subclasses through `revoke` and `assert_not_revoked`.
- Require the subclass's overridden `strip` callback not to run.
- Require SQLite not to open and no revocation row to be written on denial.

## Scope and evidence boundary

Production change is limited to the local synthetic revocation digest ingress. The frozen MemoryScope contract, Memory v1 schema, revocation schema, public API, retention semantics and downstream-use boundary are unchanged. This is not an atomic downstream-use lease, authenticated consent, independent erasure, trusted time, filesystem security or external dispatch authorization.

Synthetic local SQLite only. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. No paid compute, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, UI/frontend work, frozen-contract change or main merge.
