# ARK — Run614: disconnected non-UI authority and preflight boundaries

This report records **source/test changes authored**, not an assertion that the
latest commit has passed CI. All exercises are local synthetic fixtures.
No network ToolBackend, real notification, OS scheduling, user context
disclosure, Candidate creation, protected final evaluation, or main merge.

## Dependency and scope

- **Work-basis:** Run613 checkpoint `d818c0dde01327c58854dc477869f3ec576b2d8b`.
  The prior exact-head workflow [#41900476436](https://github.com/Iam-2squared/ark-ai/actions/runs/41900476436)
  was observed **6/6 GREEN** for Ubuntu/Windows Python 3.11–3.13.
- **Isolated Draft PR:** [#8](https://github.com/Iam-2squared/ark-ai/pull/8)
  on `research/jarvis-foundations`. PR #5 and UI-paused PR #9 remain
  Draft/unmerged. No UI/frontend work.
- **Package A, offline Personal Context prefix:** source
  `8269c3742834eb0c7ce2241733705e4f8281f267`, test
  `fb371fe8785677bc1a4d55baf2cbbca3cf5236c6`.
  Pin the original prefix-review result class and seven deny-only descriptors
  before exercising any potentially replaced getter. Recheck each original
  descriptor across result validation. Retained witness checks reuse the
  replay ledger's exact original witness-denial validation. Authored **10**
  parameter-expanded pytest cases, including original positive outcome.
- **Package B, detached recurrence preview:** source
  `1330c9ee568dd2a11ec128da4ca4b4b48223e672`, test
  `5d8f1dea1520e20e1237a2e0f667420175a85432`.
  Pin imported policy, cursor, and result constructors before input field
  access. Build with the pinned result constructor and use static original
  denial-descriptor checks. Authored **5** pytest cases. The `DUE_UNVERIFIED`
  label never grants notification, consent or execution authority.
- **Package C, synthetic Planner SQLite journal preflight:** source
  `76a4592f2b898de30207c8072712ca5a87a8a4be`, test
  `15cbf219ce69ce57bbbe30972b26b2e1c1e79795`.
  Reject unknown/malformed step IDs and nonexact/out-of-range expected
  revision *before* SQLite replay and any write transaction. Authored **13**
  pytest cases, including a legitimate RUNNING restart that must remain
  ambiguous and non-replayable.

Total: **28 authored new parameter-expanded test cases**, not a local
pytest PASS count. Actions CI for the latest source/test HEAD was **queued**
on initial observation as
[#41910131288](https://github.com/Iam-2squared/ark-ai/actions/runs/41910131288).
Individual later HEADs have their own automatically triggered runs; verify
their exact SHA and all six job outcomes separately before claiming GREEN.
Do not launch redundant manual reruns.

## Security interpretation and limitations

- Forged False-returning Python properties are still executable callbacks;
  their static original definitions must be preserved before getter access.
  Import-time pins provide *process-local* integrity, not external
  authentication or protection from all hostile Python code.
- A callback can still change other objects, SQLite files, or clock sources.
  This work cannot authenticate an observer, consent, writer, OS clock, or
  provide durable exactly-once guarantees outside local SQLite.
- Input rejection in the Planner avoids unnecessary SQLite access, but does
  not authorize dispatch or retry a RUNNING/UNKNOWN WRITE after restart.
- The synthetic schedule does not operate timers or deliver notifications.
- Frozen V1/V2/Local UI/Launcher contracts and evidence are not modified.
  V3 remains behind separate approval and reproducibility gates.

## Verification and next dependency

1. Confirm every source/test checkpoint SHA against actual Actions jobs. If
   a prior test expects a different rejection precedence, preserve the
   safety invariant and repair the specific test/implementation accordingly.
2. Continue disconnected Memory COMMIT-UNKNOWN manual reconciliation and
   full-event prefix integrity without claiming writer attribution.
3. Integrate registry-bound Tool permission, audit-before-*mock*-action,
   occurrence replay fencing and Planner restart recovery only after exact
   source-head GREEN.
4. Keep UI paused and PR #5/#8/#9 Draft/unmerged, with no paid compute,
   real Candidate, protected V2 evaluation, credentials, or main merge.

**ARK/JARVIS/V3: NOT_PASSED.**
