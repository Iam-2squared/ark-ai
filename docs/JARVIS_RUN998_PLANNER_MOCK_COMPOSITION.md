# Run998 — Isolated Planner / registry / mock-executor composition

**Work basis:** Draft PR #19 exact head `c08c7e9e6c836285362da96663dee903479da98a`; its path-fenced Planner journal CI [#44549000547](https://github.com/Iam-2squared/ark-ai/actions/runs/44549000547) completed GREEN across all six jobs.

**Reused lower-level evidence (each exact head independently verified GREEN 6/6):**

- Draft PR #14 mock-only executor: `00fee30e4004a56bb73d7161070c6a31661bc9e3`, CI [#44528750916](https://github.com/Iam-2squared/ark-ai/actions/runs/44528750916).
- Draft PR #15 read-only plan/registry preflight: `75680991e1f48d047d5f48aa51d4ceec99393eb8`, CI [#44530235330](https://github.com/Iam-2squared/ark-ai/actions/runs/44530235330).
- Draft PR #18 durable Planner journal: `976aea9d1b5573045ebc18045b3b2ce9d879b9c2`, CI [#44538278870](https://github.com/Iam-2squared/ark-ai/actions/runs/44538278870).
- Draft PR #19 journal path fence: `c08c7e9e6c836285362da96663dee903479da98a`, CI [#44549000547](https://github.com/Iam-2squared/ark-ai/actions/runs/44549000547).

**Isolated branch:** `research/planner-mock-composition-run998`, based on PR #19. The PR #14/#15 source and regression files are copied unchanged from their green branches; this branch adds only a new composition module, its integration tests, and this report.

## New composition boundary

`execute_one_mock_step` executes at most one currently-ready PlanStep:

1. Cold-recover the durable Planner journal.
2. Bind every plan step against one immutable ToolRegistry revision using the read-only preflight.
3. Reject non-ready steps, mismatched effect inputs, or any backend other than the exact in-process `MockToolBackend` before writing RUNNING.
4. Append the durable RUNNING transition.
5. Invoke the existing mock executor, which applies the local PermissionGate, durable synthetic WRITE occurrence reservation, and audit-before-mock sequence.
6. Append SUCCEEDED only after a matching mock receipt is returned.

The function does not loop, dispatch a real ToolBackend, or automatically replay. Any exception after RUNNING—including uncertain audit, mock, or terminal journal outcome—propagates. Recovery leaves RUNNING ambiguous unless a durable terminal event is present. The next caller cannot reuse the stale graph/sequence.

## Regression coverage

- A dependent READ then WRITE plan advances through two separately journaled mock-only cycles.
- A non-ready child is rejected before any journal, audit, occurrence, or backend write.
- READ rejects WRITE-only authorization inputs before RUNNING.
- A non-mock backend is rejected before RUNNING or audit.
- A pre-action audit failure leaves RUNNING ambiguous, makes no mock call, and prevents automatic retry.

The existing PR #14 and #15 regression suites are included unchanged so the copied components are exercised on this exact composition branch.

## Safety and limits

All calls use synthetic ToolCalls, grants, one-shot tokens, occurrence IDs, caller-supplied time, and disposable local SQLite files. The audit and occurrence stores are separate; this does **not** prove cross-store atomicity, authenticated consent, trusted time, independent custody, exactly-once external effects, or production dispatch safety. A failure after RUNNING requires manual recovery/review.

No real backend, external effect, model, paid service, external compute, credentials, personal data, frozen contract, V1/V2/V3 evidence, UI branch, or main branch is touched.

**Validation:** source, copied lower-level tests, integration tests, and this report are saved. Exact-head CI is pending; no PASS is claimed. No local pytest or physical-machine result is claimed.
