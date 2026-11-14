# ARK AI — Run581: non-UI audit, Planner and Memory custody

## Boundaries and basis

Run581 started from PR #8 `986b4950c405839edeab772ab4c71f46dcddb82d`
(`research/jarvis-foundations`, Draft). This work is **local-only,
synthetic/disconnected and strictly free-only**. No user-PC action,
live backend, billing, Candidate, protected evaluation, irreversible
operation, main merge, UI/frontend change, or PR #9 branch modification.
All three packages use the ordinary GitHub Contents API, with latest
branch HEAD re-read before each write and no forced update.

### Package A: SQLite Action Audit paginated clock continuity

- Source: `src/ark/agency/audit.py`, commit
  `661f49d13478a357aadc3704b57fd2b33d86dec5`.
- Tests: `tests/test_action_audit_paged_chronology_run581.py`,
  commit `cd62325497cef338ee39b0210078231f371bc711`
  (**4 authored cases**).
- Under one SQLite read transaction, `events(after_event_id=...)`
  now captures the predecessor timestamp alongside its selected page.
  The returned page must be nondecreasing, with a valid nonnegative
  integer predecessor; equal timestamps remain valid.
- Detects local chronological contradictions during a full or
  adjacent paged read without modifying historical v1 rows or schema.
  A page does **not** independently verify every earlier page.
  Persisted clocks remain unauthenticated; no receipt proves real
  audit-before-action, independent actor identity, or external exactly-once.

### Package B: Planner retained synthetic tail carrier identity

- Source: `src/ark/agency/planner_journal_review.py`,
  commit `5218026fc96fec5451b8d755233cc8d2cf1a10ff`.
- Tests: `tests/test_planner_retained_carrier_epoch_run581.py`,
  commit `d56cb1357e2b7b404b4d90372d7beb54e38bbcb4`
  (**5 authored cases**).
- Recovery and local CAS append compare the retained tail's *original
  scalar objects* as well as the scalar values around topology,
  replay, snapshot and post-COMMIT callback boundaries. A value-equal
  new SHA carrier is a new input epoch and cannot be silently accepted.
- The journal remains replay-only and disconnected; a failed
  post-COMMIT witness check is **not rollback evidence** and never
  authorizes automatic WRITE retry or real ToolBackend dispatch.

### Package C: Memory ambiguous-COMMIT retained token continuity

- Source: `src/ark/memory/ambiguous_commit_pair_review.py`,
  commit `5f803606d10f50e60053614561f35765d1e01f5d`.
- Tests: `tests/test_memory_ambiguous_token_epoch_run581.py`,
  commit `0414fadf38e6e74be02a4bf1e8ea7668dcc25bd2`
  (**3 authored cases**).
- Two local no-write reviewers now reject value-equal replacement of
  a retained generation-token field between callback checks, not
  only changed scalar values. A normal unchanged local evidence path
  still produces a **manual-only, denial-only** reconciliation.
- Two local readers do not prove writer identity, consent, original
  COMMIT outcome, cross-process independence or retry authorization.

## CI evidence: exact SHAs and status separation

- Prior PR #8 checkpoint `986b4950c405839edeab772ab4c71f46dcddb82d`:
  [Actions #41635105734](https://github.com/Iam-2squared/ark-ai/actions/runs/41635105734)
  **6/6 GREEN** (this verifies the *previous* state only).
- Audit test HEAD `cd623254...`:
  [#41638433803](https://github.com/Iam-2squared/ark-ai/actions/runs/41638433803)
  **Ubuntu 3/3 GREEN, Windows 3/3 IN PROGRESS** at sampled review.
- Planner test HEAD `d56cb135...`:
  [#41638803511](https://github.com/Iam-2squared/ark-ai/actions/runs/41638803511)
  **Ubuntu 3/3 GREEN, Windows 3/3 IN PROGRESS** at sampled review.
- Memory test HEAD `0414fad...`:
  [#41639073112](https://github.com/Iam-2squared/ark-ai/actions/runs/41639073112)
  **IN PROGRESS / QUEUED**, no final six-job verdict at sampling.
- 4 + 5 + 3 = **12 newly authored pytest definitions**, not an
  independently executed local pytest PASS count.
  This technical-note commit and the later checkpoint have their own
  exact-head CI. **Do not infer their result from predecessor runs.**

## Frozen and protected material

- PR #8 `src/ark/memory/contracts.py` blob
  `b6e93821ecd69270a7634aceb20775dc36e9953c`.
- PR #8 `src/ark/agency/contracts.py` blob
  `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`.
- PR #5 `docs/v3/CONTRACT.md` blob
  `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`.
- PR #5 `805b377697472268db02650a89c7a94b1c5337c8` is
  Draft/unmerged with prior [#41634014158](https://github.com/Iam-2squared/ark-ai/actions/runs/41634014158)
  **6/6 GREEN**, and was untouched here. PR #9
  `3b49048dd70eebcb6268299b9ecef4e301bbc0fd` is also untouched,
  Draft/unmerged, with UI/frontend work entirely paused.
  main `7a843f17eb96ed13d66f23b58b06406b3002e405` unchanged.
  V1/V2/Local UI/Launcher freezes preserved. ARK/JARVIS/V3
  **NOT_PASSED**.

## Next plan / 今後の方針

1. Confirm new exact-head Ubuntu/Windows CI; on FAIL inspect the failing
   job logs and repair only the failing semantics-preserving path.
2. Continue audit-before-action occurrence/replay fences, local-only
   Planner FAILED/BLOCKED recovery, immutable ToolRegistry/PermissionGate,
   and second-observer Memory COMMIT UNKNOWN review.
3. Extend privacy revocation/expiry snapshots, Personal Context,
   Scheduler reboot duplicate prevention and Observation mock backends.
4. Keep all UI work paused and protected/free-only Draft boundaries intact.
