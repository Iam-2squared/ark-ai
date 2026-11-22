# Run1123 — proactive state process recovery and class-seal rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD at branch creation: `125674bf1b09a5fe951926c5d39870d28468fe02`.
- Child branch: `research/run1123-proactive-state-recovery-rebase`.
- Source chain: Draft PR #304 (Run1120 process-exit recovery) followed by Draft PR #305 (Run1121 class-descriptor seal). This branch reapplies the tested chain to the latest observed PR #8 basis.

## Verified source evidence

- PR #304 exact child HEAD `c082c2dfd0004a7d3525dbfbda9556a7a9bc53e8`, CI run [45059948886](https://github.com/Iam-2squared/ark-ai/actions/runs/45059948886): GREEN, Windows/Linux × Python 3.11–3.13 (6/6).
- PR #305 exact child HEAD `0f9aef6ed47c2f019c64302561eb9cf1cf0e543d`, CI run [45060176698](https://github.com/Iam-2squared/ark-ai/actions/runs/45060176698): GREEN, Windows/Linux × Python 3.11–3.13 (6/6).
- The current PR #8 source file was unchanged from the PR #304 base through the current branch basis; the intervening PR #8 commits changed only `docs/PROJECT_STATUS.md`.

## Scope

- Retain the spawned-process cold-recovery test after a successful public API return, exact revision/digest/decision/window checks, content minimization, stale-CAS refusal and explicit recovered-revision CAS.
- Add the class-descriptor/slot-layout identity guard and regressions that reject substituted class entry points or rebound guard vectors before SQLite access.
- Preserve existing schema, path identity, CAS, digest, policy and denial-only authority semantics.

## Limits

These are local synthetic SQLite fixtures. A process exit after an API return is not a native-COMMIT crash proof; the class guard is not a secure Python sandbox against arbitrary same-process reflection. No trusted clock, consent, notification, dispatch, automatic replay, external service, paid compute, Candidate, protected V2 evaluation, credentials, hardware, UI or main merge is enabled. Fresh exact-head CI is required on this rebased branch. PR #8 remains Draft/unmerged; ARK/JARVIS remains NOT_PASSED.
