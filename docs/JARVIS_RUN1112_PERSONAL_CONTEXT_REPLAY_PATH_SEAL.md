# ARK Run1112 — Personal Context replay-ledger path seal

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD: `6bdbe12acadc2ffa5c7506c4e8d9b41b722f7e83`.
- Branch: `research/run1112-personal-context-replay-path-seal`.
- Exact pre-report work HEAD: `b9c6350a970b4a61f4da2f3bc64e93c7ca267995`.

## Finding

The disconnected Personal Context replay ledger already checked that its private `_path` object stayed stable across SQLite callbacks. Ordinary reassignment of that field before an operation could nevertheless redirect a ledger instance to a different valid local database.

## Change

- Store `_path` in a slot while retaining `__dict__` for the existing isolated instance-method fault-injection tests.
- Block ordinary reassignment and deletion of `_path` after initialization.
- Check exact ledger type before construction and before SQLite open/read/reservation operations.
- Keep the slot data descriptor authoritative even if a same-named `__dict__` key is inserted.
- Update the two path-retarget regressions to use explicit `object.__setattr__` reflective fault injection, preserving their original mid-operation rejection purpose.
- Add tests for ordinary assignment/deletion denial, dictionary shadow resistance, and subclass rejection before database creation.

The replay schema, chain digest, retained-prefix semantics, request binding, and reserve CAS are unchanged. No context payload is added to the replay ledger.

## Evidence boundary

This is an in-process object/path identity guard, not a sandbox. Reflective `object.__setattr__`, hostile class monkeypatching, and filesystem TOCTOU are not claimed to be prevented. The path checks remain lexical and do not establish atomic directory-handle custody. The ledger does not establish consent, revocation freshness, trusted time, context disclosure permission, tool dispatch, or automatic replay.

No local pytest/Ruff PASS is claimed. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. The parent PR #8 exact-head CI result does not transfer to this child. PR #5 and PR #8 remain Draft/unmerged; UI remains paused. No paid service, external compute, Candidate, protected V2 evaluation, credentials, physical hardware, frozen-contract change, or main merge.
