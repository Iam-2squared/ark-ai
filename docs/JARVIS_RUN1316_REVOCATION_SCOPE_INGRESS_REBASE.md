# ARK Run1316 — exact Personal Context revocation scope ingress

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `824bb987f0addf4e961c9f4949f6075ca42a1caa`.
- Child branch: `research/run1316-context-revocation-exact-scope-rebase-20261125`.
- Previous child exact-head CI [45443628554](https://github.com/Iam-2squared/ark-ai/actions/runs/45443628554) was GREEN on its old base only; it does not transfer to this rebase.

## Finding

The revocation ledger accepted an exact `MemoryScope` object but called its `__post_init__` before requiring exact built-in `str` owner and namespace fields. The frozen `MemoryScope` constructor uses the broader `isinstance(str)` contract, so a string subclass could execute overridden methods during privacy-veto digest validation.

## Change and regression coverage

- The local revocation digest boundary snapshots owner/namespace references and rejects non-exact built-in strings before calling `MemoryScope.__post_init__`.
- It rechecks the field carriers after validation and hashes only the captured exact strings.
- Synthetic tests cover both owner and namespace subclasses through both `revoke` and `assert_not_revoked`.
- The subclass's overridden `strip` method must not run during the veto operation; SQLite must not be opened and no revocation row may be written.

## Scope and evidence boundary

Production change is limited to `SyntheticContextRevocationLedger`'s local digest ingress. The frozen MemoryScope contract, Memory v1 schema, revocation schema, public API, retention semantics and downstream-use boundary are unchanged. This is not an atomic downstream-use lease, authenticated consent, independent erasure, trusted time, filesystem security or external dispatch authorization.

Synthetic local SQLite only. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed. No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, UI/frontend work, frozen-contract change or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched.
