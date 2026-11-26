# ARK Run1113 — rebase Planner journal stat-policy custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD: `4f9e44532cc25dfe57059021519717441399155b`.
- Rebased child branch: `research/run1113-planner-journal-stat-reentrant-rebase`.
- Prior child PR #270 branch: `research/run1111-planner-journal-stat-reentrant-rebase`, exact head `8d76eecf944aa053863cb2de19af9ed087119016`.
- Prior exact-head CI: [45019519474](https://github.com/Iam-2squared/ark-ai/actions/runs/45019519474), GREEN on the prior child head only; it does not transfer to this rebase.

## Change

Reapplies replay-only Planner journal stat module/classifier custody and reentrant path/metadata checks. The import-original stat module and `S_ISDIR` / `S_ISLNK` / `S_ISREG` classifiers are pinned and rechecked after ancestor/leaf `lstat`, missing-leaf handling, path existence checks, metadata accessors and sidecar re-observation. Classification uses captured original predicates.

## Preserved semantics and limits

Planner journal schema, hash chain, transition policy and UNKNOWN handling for recovered RUNNING remain unchanged. No automatic retry, dispatch or external execution authority is added. Tests use temporary paths and monkeypatched callbacks only; no private journal or external action is opened.

This is local dependency-identity and lexical pathname preflight hardening, not atomic directory-handle custody, a sandbox, independent provenance, trusted time, consent, power-loss durability or exactly-once external effects. No local pytest/Ruff PASS is claimed. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.

No paid/external compute, Candidate, protected V2 evaluation, frozen-contract change, credentials, physical hardware, UI/frontend work, destructive operation or main merge occurred. PR #5 and PR #8 remain Draft/unmerged. **ARK/JARVIS remains NOT_PASSED.**
