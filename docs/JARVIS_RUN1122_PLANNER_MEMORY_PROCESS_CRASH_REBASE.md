# Run1122 — Planner and Memory process-crash fixture repairs rebased

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD at branch creation: `125674bf1b09a5fe951926c5d39870d28468fe02`.
- Child branch: `research/run1123-planner-memory-crash-fixture-rebase`.
- Source evidence: Draft PR #306 (Planner fixture) and Draft PR #307 (Memory WAL marker fixture). Neither source PR is merged by this child.

## Planner fixture repair

- Source child HEAD: `c2cbb43968edc20f4f8816f31c68d74d4b92f135`.
- Exact-head CI run [45062498855](https://github.com/Iam-2squared/ark-ai/actions/runs/45062498855): GREEN, Windows/Linux × Python 3.11–3.13 (6/6).
- The spawned hard-exit fixture converts its argv path to an exact `pathlib.Path` before constructing `SyntheticPlanJournal`. The before/after native COMMIT cases, retained-tail checks, event sequence, SQLite quick_check and denial-only recovery flags remain unchanged.

## Memory fixture repair

- Source child HEAD: `faa9444461eb633ef309bc4296501d2fa98936a0`.
- Exact-head CI run [45062631067](https://github.com/Iam-2squared/ark-ai/actions/runs/45062631067): GREEN, Windows/Linux × Python 3.11–3.13 (6/6).
- The WAL reader marker check now waits within the existing bounded deadline for readable exact content, retrying only transient `FileNotFoundError` / `PermissionError`, and checking child liveness. Persistent failure remains a test failure.

## Scope and limits

This rebased package changes tests only. Planner production source, Memory production source, schemas, CAS/expiry behavior, event semantics, privacy policy and frozen contracts are unchanged. All databases, scopes, rows and plans are disposable synthetic local fixtures. No dispatch, automatic replay, permission grant, external effect, trusted-clock proof, erasure/retention authority, paid compute, Candidate, protected V2 evaluation, credentials, hardware, UI or main merge is included.

The source child runs validate their own exact child heads; they do not transfer as CI evidence to this rebased head. Fresh exact-head CI is required. PR #8 remains Draft/unmerged and ARK/JARVIS remains NOT_PASSED.
