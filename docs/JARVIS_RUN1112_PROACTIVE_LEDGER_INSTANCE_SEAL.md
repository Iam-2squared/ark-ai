# ARK Run1112 — seal proactive state ledger instance identity

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD: `6bdbe12acadc2ffa5c7506c4e8d9b41b722f7e83`.
- Child branch: `research/run1112-proactive-ledger-instance-seal`.
- Source commit: `857418f0f76b0e40aeeca7fffb87b675f94834be`.
- Test commit: `ab74691a1accd128e9e690c6180ceae935127463`.

## Finding

`SyntheticProactiveStateLedger` previously stored its database path in an ordinarily assignable public `path` attribute. Its operation-time identity checks detect path changes during an operation, but do not prevent a caller from replacing the path before the next operation and redirecting that ledger object to another valid local database.

## Change

- Use a slot-only `_path` field; instances no longer expose an instance `__dict__`.
- Expose the path through a read-only property.
- Reject ordinary instance attribute assignment and deletion.
- Require the exact ledger class before construction and before connect/read/evaluate/count operations, rejecting subclasses before database creation.
- Preserve the existing path checks around open, callbacks, and commit.

The focused tests cover absent instance dictionaries, ordinary path/private-slot/extra-attribute assignment and deletion, unchanged path identity, and subclass rejection before a database file is created.

## Evidence boundary

This is a local object-identity hardening, not a security boundary against reflective `object.__setattr__`, class monkeypatching, hostile in-process code, or filesystem TOCTOU. The existing lexical SQLite path preflight remains non-atomic; this does not add dirfd custody, trusted time, consent, notification, or dispatch authority. `ELIGIBLE_PREVIEW` remains a non-authoritative preview.

The proactive state schema, row digest, policy identity, revision CAS, cooldown/window calculations, and public evaluation semantics are unchanged. No timer, notification, ToolBackend, external effect, UI, frozen contract, V3 evaluation, Candidate, paid service, or main branch is involved.

No local pytest/Ruff PASS is claimed. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. The parent PR #8 exact-head run `45020401780` is GREEN 6/6 only for the parent HEAD, not this child.
