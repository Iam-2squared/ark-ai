# ARK Run1113 — rebase proactive state ledger instance seal

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD: `4f9e44532cc25dfe57059021519717441399155b`.
- Rebased child branch: `research/run1113-proactive-ledger-instance-seal`.
- Prior child PR #280 branch: `research/run1112-proactive-ledger-instance-seal`, exact head `6293e93189885b9bffc0c746cfe2a65f76adb5c5`.
- Prior exact-head CI: [45027156939](https://github.com/Iam-2squared/ark-ai/actions/runs/45027156939), GREEN on the prior child head only; it does not transfer to this rebase.

## Change

The proactive state ledger now uses slot-only `_path` storage, a read-only path property, and rejects ordinary instance assignment/deletion. Exact-class checks run before construction and before connect/read/evaluate/count operations. The tests cover absent instance dictionaries, ordinary path/private-slot/extra-attribute mutation and deletion, stable path identity, and subclass rejection before database creation.

## Preserved semantics and limits

The SQLite schema, row digest, policy identity, revision CAS, cooldown/window calculations, and denial-only preview behavior are unchanged. This is local object-identity hardening only. It does not prevent reflective `object.__setattr__`, class monkeypatching, hostile in-process code, or filesystem TOCTOU; it adds no dirfd custody, trusted time, consent, notification, dispatch, or automatic replay authority. `ELIGIBLE_PREVIEW` remains non-authoritative.

No local pytest/Ruff PASS is claimed. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No paid/external compute, Candidate, protected V2 evaluation, credentials, physical hardware, frozen-contract change, UI work, or main merge occurred. PR #5 and PR #8 remain Draft/unmerged. **ARK/JARVIS remains NOT_PASSED.**
