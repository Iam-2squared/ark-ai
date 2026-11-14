# Run518 — detached READ post-append custody and Memory event lifecycle

**Evidence scope:** local synthetic SQLite and caller-retained witnesses only. This
document describes code committed on PR #8, **not** an assertion of execution,
independent custody, actual user permission, real ToolBackend outcome, trusted
time, privacy erasure or historical writer authenticity.

## Exact source/test changes

- **Synthetic READ append bridge** `src/ark/agency/disconnected_read_receipt_bridge.py`:
  source commit `97989735abdc14869c82e6acc7eefa47179d7612`, blob
  `de72444f782d8517e9d20d1541e3ee45673008cb`.
  The bridge derives the *expected* v1 chain tip for its exact receipt
  BEFORE calling the journal append, compares the reported count **and tip**
  afterward, then uses `journal.verify(saved)` to inspect a durable local
  SQLite snapshot. A callback cannot claim an append with a fabricated tip or
  claim persistence without a row. After the verifier, it rechecks witness
  carriers and all no-authority flags. No automatic retry is performed after
  a possible COMMIT: an error is an **unknown outcome**, not proof of rollback.
  Test commit `c274c4296f3e00096af5b750b60fed99a26c7486`,
  `tests/test_read_bridge_persisted_tip_run518.py`: **6 authored pytest cases**
  including a valid local append, wrong tip, false committed tip, a different
  persisted row, equal-valued retained tip replacement and forged verifier
  output. No external service is called.

- **Memory row/event coherence** `src/ark/memory/sqlite_retained_row_delta_review.py`:
  source commit `06874d5484cc9df8644360e151ebbdfed8a8b5cd`, blob
  `c0ba78c72795b19e1d2917ae04986792f3adc124`. The standalone local
  row-delta snapshot now checks event scope, live/predecessor lifecycle,
  create/update/delete/expire revision continuity and whether the terminal
  event's live/deleted state matches the current row, in the **same SQLite
  read transaction**. This closes a gap where a newly captured local baseline
  could adopt a row with missing creation history or a mismatched event
  revision. It retains the existing digest/evidence schema and never
  authenticates the author of an appended event.
  Test commit `e197cbe9b1fa4a1df815c0be8a00104d0a5ba096`,
  `tests/test_memory_row_delta_lifecycle_run518.py`: **9 authored pytest
  cases** covering seven malformed history/row states and valid
  update-delete and delete-recreate lifecycles.

- **Personal Context retained-prefix final denial** 
  `src/ark/personal_context_replay_prefix_review.py`: source commit
  `8f1140c5fac8672090474fc460e2e40c02d79e4e`, blob
  `26bf48c7d80a506b99ba48734d7ae0a255483a47`. Recheck all
  local summary counters, status carrier identities, hashes, and seven denied
  authority flags after the final witness/denial property callbacks; never
  treat a local prefix hash as consent, revocation freshness or disclosure.
  Test commit `827d04bc149a01f35f4d08fd5bfcb2e175071213`,
  `tests/test_context_prefix_final_denial_run518.py`: **7 authored pytest
  cases** (five late-result substitutions, one final retained-witness
  callback substitution and one inert stable fixture).

**22 total newly authored local pytest cases** in the three PR #8 packages.
Source and tests were saved through standard GitHub Contents API after a fresh
HEAD read, without raw Git objects, force pushes or protected contract edits.
Authored cases are not an independently executed local PASS count.

## CI and evidence boundaries

- Prior Run517 PR #8 exact source+test `2ceaf41277c40292b3ba999170448ad0858f6849`
  [CI 41262669072](https://github.com/Iam-2squared/ark-ai/actions/runs/41262669072)
  completed SUCCESS, as did the Run517 checkpoint
  [41262797540](https://github.com/Iam-2squared/ark-ai/actions/runs/41262797540).
- Run518 Agency source/test
  [41266319918](https://github.com/Iam-2squared/ark-ai/actions/runs/41266319918)
  and final combined PR #8 source/test
  [41266474450](https://github.com/Iam-2squared/ark-ai/actions/runs/41266474450)
  were **IN PROGRESS** when the first version of this document was prepared. No final 6/6 GREEN
  claim is inherited from an older HEAD.
- Independent full-checkout local pytest/Ruff, physical-PC runtime, external
  identity, trusted clock and storage forensics were NOT performed.

## Frozen controls and next step

PR #8 remains **Draft/unmerged**; main and frozen V1/V2/Local UI/Launcher,
Memory and Agency contracts stay unchanged. PR #5 remains Draft under its own
gate. Zero paid/external compute, training, real Candidate/weight generation,
protected final V2 evaluation, automatic promotion, real READ/WRITE dispatch,
credential setup, destructive cleanup or main merge.

After exact-head CI evidence is GREEN, prioritize connecting read-only
Planner/Registry/PermissionGate intent to this verified local READ journal
without granting dispatch; strengthen Memory CAS/retained cross-process
witnesses, UNKNOWN WRITE manual-only recovery and trusted-clock
audit-before-action. Avoid any implication that local hashes authenticate
external effects, approval or data deletion.

### Later CI failure and semantics-preserving correction

The preliminary combined source/test CI
[41266474450](https://github.com/Iam-2squared/ark-ai/actions/runs/41266474450)
reported **three existing Run512 test assertion failures**: the new
fail-closed Memory lifecycle check rejects malformed states earlier with
`live Memory row differs from event lifecycle` or
`live Memory row lacks creation event`, before the previous fallback
`without its own` / `event prefix` checks. The normal Contents API
updated **only the corresponding regex expectations** in
`tests/test_memory_retained_row_delta_run512.py`, commit
`94ec1ee60a0bb0a7aa99ad22cf4e8ad765f8a2f9`, blob
`244c96015e4b54831ceb1b1ccdafd9a1a4383abb`. No safety check,
contract, lifecycle rule or rejection was weakened. Corrected CI
[41266626048](https://github.com/Iam-2squared/ark-ai/actions/runs/41266626048)
was **IN PROGRESS** when this amendment was prepared; Context source/test
[41266752405](https://github.com/Iam-2squared/ark-ai/actions/runs/41266752405)
was **QUEUED**. Do not inherit older GREEN onto either final HEAD.
