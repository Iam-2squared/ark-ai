# Run1120 — proactive state process-crash recovery

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Parent HEAD at child creation: `71a983db75184b76079648a362638332dc151741`.
- Child branch: `research/run1120-proactive-state-process-crash`.
- Test commit: `3df6e2c161262f56eb03c0fa8e5ad648a5af3515`.

## Coverage

The new spawned-process regression:

1. Initializes an empty local synthetic proactive-state SQLite ledger.
2. Starts a fresh child process, commits one `ELIGIBLE_PREVIEW` state through the public ledger API, then exits abruptly with `os._exit` after the API returns.
3. Reopens the same database in a cold parent-side ledger and verifies the exact revision, observation digest, decision and rolling-window entry.
4. Confirms the raw synthetic observation text is not stored and all notification, dispatch, replay and consent flags remain false.
5. Proves a stale revision cannot overwrite the recovered state, then performs an explicit CAS using the recovered revision and confirms the unchanged-observation decision does not create a second preview.

## Evidence boundary

This is a process-restart durability test after a successful API return. It does **not** inject process death inside native SQLite COMMIT, claim COMMIT-UNKNOWN resolution, provide a trusted clock, authorize a timer/notification, or enable external actions. The existing state schema, digest, policy, CAS semantics and denial-only behavior are unchanged.

All data is disposable local SQLite and synthetic strings. No external scheduler, notification service, paid compute, credentials, hardware, UI or main merge is involved. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed. PR #8 remains Draft/unmerged and ARK/JARVIS remains NOT_PASSED.
