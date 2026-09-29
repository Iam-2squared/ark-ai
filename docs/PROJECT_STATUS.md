# ARK AI Project Status

**LATEST**

Saved at: **2026-09-29 16:12:02 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / Draft PR #8

Work-basis HEAD: `78f92c75c0fe91abd361e86af4aa8a03568844c4`

Checkpoint-result HEAD: this file cannot contain the SHA of the commit that writes itself; use the commit produced by this checkpoint update.

Supersedes the prior canonical checkpoint saved at 2026-09-29 11:07:26 JST.

## Current state

V1/V2/Local UI/Launcher remain frozen and passed with their existing evidence unchanged. V3 remains Draft/unmerged under its frozen Contract. JARVIS foundation work remains isolated/reversible and is not a roadmap PASS. At this work basis, PR #8 is open, Draft, mergeable, **78 commits ahead / 0 behind** `main`.

## New work this session

- Re-read latest PR #8 state and reconciled a concurrent pre-existing scheduler-evidence commit before writing.
- Landed Planner invariant hardening at `78f92c75c0fe91abd361e86af4aa8a03568844c4`:
  - `PlanGraph.steps` is now exposed as an immutable mapping rather than a mutable public dict.
  - status snapshots are immutable mappings.
  - transition input requires exact `StepState` and exact non-bool non-negative integer revisions.
  - transition rules use an immutable mapping of frozensets.
  - derived descendant/cycle traversal uses sorted step IDs for deterministic order.
- Prepared matching Planner regression tests for unordered dependency rejection, raw-string state rejection, bool/negative revision rejection, and topology/status immutability. The normal GitHub Contents write path rejected the test-file update, so those new tests are not claimed as landed.
- Prepared Memory writer serialization / negative-schema-version hardening and a stronger schema-v1 fixture binding non-index column collation plus AUTOINCREMENT semantics. Those normal writes were also rejected by the tool safety path and are not claimed as repository state.
- Attempted to refresh the Foundation Gap Matrix through the normal write path; that write was rejected and no bypass was used.

## Tests / CI / evidence

- Exact work-basis CI #224 / run `36534961185` on `78f92c75c0fe91abd361e86af4aa8a03568844c4`: **SUCCESS, 6/6 jobs GREEN** across Windows/Ubuntu and Python 3.11-3.13.
- Ubuntu Python 3.11 job `109296787566`: **ruff PASS, pytest 163 PASS**; Local UI Node tests PASS.
- Benchmark and fixture-only V2 evaluation/compare steps completed. CI still reports `v2_gate: NOT_PASSED`, so no frozen V2 gate was reinterpreted.
- The new Planner source hardening is therefore regression-clean against the existing repository suite, but its new focused regression tests remain pending because the normal test-file write was blocked.
- PR #5 remains Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`; no preflight, GPU training, Candidate generation, or protected V2 opening was started.

## Frozen boundaries unchanged

Frozen V1/V2/Local UI/Launcher evidence is unchanged. V3 Contract semantics are unchanged. Protected V2 final evaluation remains unopened. No Candidate weights, promotion, paid/external compute, new credentials/account connection, physical-PC action, destructive/irreversible action, or main merge occurred.

## Blockers / authorization boundaries

Normal test/source/fixture/doc writes remain intermittently blocked by the tool safety path after the Planner source commit. No raw Git-object/ref write, force-push, alternate-branch bypass, or overwrite workaround was used. Existing approval boundaries remain unchanged for paid/external compute, real Candidate generation, protected evaluation, promotion, frozen-contract changes, destructive/irreversible work, new credentials/account connections, unavailable physical-PC actions, and main merge. No new user-action blocker was introduced.

## Next plan / 今後の方針

1. Land the prepared focused Planner invariant regression tests through the normal GitHub Contents path only.
2. Harden Memory writer transactions with `BEGIN IMMEDIATE`, translate expected contention into domain conflicts, reject invalid schema versions, and strengthen schema-v1 semantic validation for collation/AUTOINCREMENT.
3. Add persisted-row integrity validation, monotonic trusted-clock mutation checks, revision-bound expiry purge, and coherent multi-namespace snapshots.
4. Harden Action Audit v1 bootstrap/schema/row validation, then implement only the explicit v1-to-v2 integrity migration with matching tests.
5. Land immutable ToolRegistry and registry-bound action identity before durable one-shot authorization/execution occurrence work.
6. Integrate trusted-clock audit-before-action, disconnected/mock executor, planner recovery, and startup readiness.
7. Implement deterministic Personal Context over coherent Memory, then local proactive scheduler state.
8. Add ObservationEnvelope regression tests and fixture-only multimodal adapters before any live capture integration.
9. Continue free-only PR #5 guard closure without opening protected evaluation or starting real Candidate work.
