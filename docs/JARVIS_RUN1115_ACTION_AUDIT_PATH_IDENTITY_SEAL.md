# ARK Run1115 — ActionAudit source-path identity seal

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD: `246083bb46be2deb18b905a59953247baa290af8`.
- Work branch: `research/run1115-action-audit-path-seal`.
- Production source commit: `98009a2e16d647a9aa31c836169b6861d5fce8bf`.
- New focused regression commit: `c15903aa4f6b88401a28c7e9c4cd40430f47bd0d`.
- Existing path-change fault-injection tests were migrated to explicit `object.__setattr__` reflective mutations so their callback/transaction boundaries remain tested under the new ordinary-assignment guard.

## Change

`SQLiteActionAudit.path` is now a slot-backed data descriptor paired with a private path-identity witness. Ordinary assignment/deletion is rejected; an instance-dictionary key cannot shadow the slot. The exact audit class and its path-sensitive method descriptors are checked before path use. Constructor subclassing is rejected before parent-directory creation. The path identity is checked around constructor admission, safe-path inspection, SQLite connection creation, append and read entrypoints.

The instance dictionary is intentionally retained for existing test-only callback injection of `_clock_ms`, `_connect`, `_connect_readonly` and other fault boundaries. The path itself is not stored in that dictionary. Existing callback tests now use explicit reflective mutation to prove that same-value/new-object retargeting is detected at the same transaction boundaries.

## Preserved semantics / limits

- ActionAudit v1 DDL/API, event identity, sequence, schema validation, full-history validation, WAL/bootstrap, chronological clock checks, append transaction and post-COMMIT ambiguity handling are unchanged.
- The injected clock remains caller-supplied and is not authenticated or trusted merely by this path seal.
- This is an in-process path-identity guard, not a sandbox, atomic directory-handle custody, TOCTOU defense, trusted clock, consent proof, independent provenance or proof of an external effect.
- Tests use disposable local SQLite files and synthetic ToolCalls only. No real backend dispatch, private database, external action, paid service, GPU, Candidate or physical hardware is accessed.

## Validation

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required on the resulting PR head. No local pytest/Ruff PASS is claimed. Earlier CI on another HEAD does not transfer.

PR #5 and PR #8 remain Draft/unmerged; PR #9 and all Local UI freezes remain untouched. Frozen V1/V2, Memory, Planner, ActionAudit, Observation, Personal Context and V3 contracts/evidence remain unchanged. **ARK/JARVIS remains NOT_PASSED.**
