# Rebase — Personal Context replay carrier absent-hook custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `db7f12a406ef668b2f6bf1cdbf46715d8a406ce8`.
- Parent source `src/ark/personal_context_replay_ledger.py` was verified unchanged from prior basis `7178d91c4ae332908dd8bd34fd9f8ab939385bd3` (blob `595d5a8215f59f44c66916605dbde421020779ef`).
- Rebased source package: prior Draft PR #598, child HEAD `7258c534399d184067f70418f463801acbff98db`.
- Prior exact-head CI run [45668069987](https://github.com/Iam-2squared/ark-ai/actions/runs/45668069987) was GREEN on that prior child HEAD only; it does not transfer to this rebase.
- New child branch: `research/rebase-personal-context-replay-hook-custody-20261126`.

## Finding and correction

The disconnected Personal Context replay witness and post-COMMIT receipt captured absent `__new__`, `__getattribute__` and `__getattr__` hooks with `vars(type).get(name)`. This represented both true absence and an explicit `None` class member as the same value. The guards also did not retain all carrier/type/vector aliases in one import-time epoch.

Each carrier now has its own unique absence sentinel and retained epoch for its exact type alias, fields, denial descriptors, hook-name vector, original hook descriptors and sentinel. Validators check epoch/alias identity before reading the class namespace, then require namespace non-membership for absent hooks and exact identity for present members. Receipt validation remains before construction after the durable reservation; rejection remains post-COMMIT and does not imply rollback or safe retry.

## Regression coverage

- Explicit `None` and the exact sentinel installed as each absent witness/receipt hook.
- Sentinel rebinding, equal-valued hook-vector replacement and epoch replacement.
- Joint public/private type-alias replacement for both carriers.
- Witness hook substitution is denied before the digest callback.
- Special class-slot probes run in an isolated subprocess.

## Privacy and evidence boundaries

The replay ledger continues to store only request/owner/context/binding digests and a local hash chain. No context text is added to persistence. The work does not prove consent, revocation freshness, context disclosure permission, trusted time, independent storage custody, physical deletion, process isolation, exactly-once external effects or permission to dispatch. DDL, row/hash domains, CAS reservation semantics, recovery, retention and public APIs are unchanged.

No live personal data, external context connector, ToolBackend dispatch, notification, credential/account connection, hardware action, paid/external compute/service, Candidate generation/promotion, protected V2 evaluation, destructive operation, frozen-contract change, main write/merge or UI/frontend work occurred. PR #5 remains gated Draft/unmerged; PR #8 remains Draft/unmerged; PR #9 remains untouched.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff result or PASS is claimed.
