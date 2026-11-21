# Run898 — non-UI reentrant Planner, SQLite sidecar and Memory source epochs

**Work-basis HEAD:** `9eafb3f988a9ce9e9f1d95f98741827dbaef93ca` (Run897 checkpoint). **Working branch:** `research/jarvis-foundations` / Draft PR #8, never main. **Complete authored code/test head before this report:** `05c32504878978ec70da41c2a69b2c00a2d53ed3`. **Overall JARVIS:** NOT_PASSED.

## Package 1 — Planner staged-transition lost-update fence

- [Source `ea970fa7`](https://github.com/Iam-2squared/ark-ai/commit/ea970fa7189d8ee1567fcc799b6c414dc778ea45) binds the original `PlanGraph._status_epoch` before a transition's preflight and rejects a newer legitimate nested transition before publishing a staged update. This matters when an injected/reentrant `dataclasses.replace` callback performs another accepted transition after the outer transition has read its expected revision. A consistent newer state was previously indistinguishable from the original snapshot; the old staged copy could silently overwrite it.
- [Three test cases `797867e3`](https://github.com/Iam-2squared/ark-ai/commit/797867e3dc23c22343a7b0c897b625375dcf621d): reentrant change of same step, independent step, and terminal dependency cascade. The same-step case already had a stricter earlier staged-revision rejection, so the initial test's assumed message was wrong. [Test-only correction `05c32504`](https://github.com/Iam-2squared/ark-ai/commit/05c32504878978ec70da41c2a69b2c00a2d53ed3) accepts the actual existing same-step rejection and retains the separate cross-step epoch assertion. Neither failure path authorizes dispatch or rolls back an already successful nested transition.

## Package 2 — synthetic revocation WAL/SHM readback alias refusal

- [Source `403501da`](https://github.com/Iam-2squared/ark-ai/commit/403501da152fef39e758e30aed393cadc49769b6) requires any present `-wal`, `-shm`, and `-journal` synthetic sidecar to be a single-link regular file both before and after independent read-only durable-veto verification. Presence/absence may legitimately change as SQLite closes; an alias is never accepted as durable custody. This changes only the disposable diagnostic script, not live Privacy/Permission policy.
- [Ten test cases `844b4133`](https://github.com/Iam-2squared/ark-ai/commit/844b4133811ca96699b156fbac08fefcfa2f71de): nine sidecar suffix/type combinations (symlink, hardlink, directory; unavailable OS alias operations explicitly skip), rejecting them before any SQLite connection, plus one canonical single-file positive control.
- **Limit:** path `lstat` preflights are not atomic open-handle identity; a pathname swap-and-restore, independent provenance, and Windows WAL/SHM last-close races remain unresolved.

## Package 3 — Memory GET callback-bound source identity

- [Source `5be712d2`](https://github.com/Iam-2squared/ark-ai/commit/5be712d2542895e7149fb6029c2b1cf6b5ed97f9) checks `SQLiteMemoryStore.path` object identity alongside original scope before and after each existing read boundary. A synthetic callback that retargets the source during opening or row hydration can no longer rely on the later expiry clock callback to restore the original pathname before a final-only comparison.
- [Three test cases `e90c8247`](https://github.com/Iam-2squared/ark-ai/commit/e90c82479d4786b4fa7717d71c1ea7ab143201af): source drift immediately after read-only connection, source drift during row hydration (both refused before a restoring clock can run), and a valid unmodified positive read.
- **Limit:** in-process source pointer preflights are not cross-process atomic SQLite file-descriptor custody; no claim of encryption, authenticated history or consent.

## CI and safety limits

- Starting Run897 checkpoint [#43721729259](https://github.com/Iam-2squared/ark-ai/actions/runs/43721729259): **GREEN 6/6** Windows/Ubuntu × Python 3.11–3.13.
- Initial Planner test head `797867e3...` [#43725844641](https://github.com/Iam-2squared/ark-ai/actions/runs/43725844641): Ubuntu Python 3.12 and other completed Ubuntu jobs **FAIL** on one incorrect test-message expectation; corrected later, no runtime safety check relaxed. Do not assign this GREEN status to any later head.
- Privacy test head `844b4133...` [#43726082121](https://github.com/Iam-2squared/ark-ai/actions/runs/43726082121) and Memory test head `e90c8247...` [#43726258238](https://github.com/Iam-2squared/ark-ai/actions/runs/43726258238): **IN PROGRESS / QUEUED**, respectively, at latest sampled stage. The expectation-only correction and report commits trigger their own PR CI.
- **16 authored regression cases; latest exact-head six-job GREEN remains unverified.** No user approval, trusted clock, protected evaluation, physical-PC identity, external effect or paid action was obtained.

Frozen V1/V2/Local UI/Launcher and detached V3 constraints unchanged. PR #5 and paused UI PR #9 remain Draft/unmerged and untouched. No new frontend work, paid compute/API/GPU, real Candidate/training, protected eval, main merge or real tool WRITE.

**Next plan / 今後の方針:** (1) certify the corrected latest-head CI and repair only actual failures; (2) isolate Windows SQLite WAL last-close refusal vs durable winner with strict independent custody; (3) preserve Memory CAS/coherent expiry/event history and Planner UNKNOWN non-replay, then (4) review immutable ToolRegistry + exact-type PermissionGate + pre-action audit with disconnected Mock READ before any integrated authorization claims.