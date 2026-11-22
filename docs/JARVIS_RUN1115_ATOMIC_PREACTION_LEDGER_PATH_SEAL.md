# ARK Run1115 — atomic pre-action ledger path identity seal

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD: `246083bb46be2deb18b905a59953247baa290af8` (includes the separately green Personal Context replay path-seal child package).
- Work branch: `research/run1115-atomic-preaction-path-seal`.
- Source commit: `8b7b7998d5c7d91568620cef256dd90eb933cfa2`.
- Focused regression commit: `b28917ec5d28e48c0aff1fc435d11b755bfd3ec5`.

## Change

The disconnected atomic pre-action ledger stores its normalized SQLite path in a slot-backed data descriptor and keeps a separate path-identity witness. Ordinary assignment and deletion of either identity field are rejected. Exact ledger type and original class-method/slot descriptors are checked before path use. A same-named instance-dictionary key, reflective single-field retarget, or callback-time path change is rejected before the alternate database can be opened. The exact-type check also rejects subclass creation before filesystem inspection or database creation.

The existing instance dictionary is intentionally retained because the commit-ambiguity fixture wraps the instance `_open` method. The path fields remain slot-backed and are checked around connection creation, snapshot scanning, reservation mutation and commit boundaries.

## Preserved semantics / limits

- Atomic intent and audit DDL, schema version, row digest, chain digest, paired-row insertion, retained witness CAS, and COMMIT-UNKNOWN recovery behavior are unchanged.
- The ledger remains digest-only and has no execute method. A retained local witness is not consent, trusted time, independent custody, dispatch authority, automatic replay authority or proof of an external effect.
- This is an in-process path-identity guard, not a sandbox. Deliberate coordinated reflective mutation, hostile native code, filesystem TOCTOU and cross-store atomicity are not claimed to be prevented.
- Tests use disposable temporary SQLite files and synthetic claims only. No private database, live tool, external action, paid service, GPU, Candidate or physical hardware is accessed.

## Validation

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required on the resulting PR head. No local pytest/Ruff PASS is claimed. Existing exact-head CI for another branch or commit does not transfer.

PR #5 and PR #8 remain Draft/unmerged; PR #9 and all Local UI freezes remain untouched. V1/V2, Memory, Planner, ActionAudit, Observation, Personal Context and V3 frozen contracts/evidence remain unchanged. **ARK/JARVIS remains NOT_PASSED.**
