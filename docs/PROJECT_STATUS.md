# ARK AI Project Status

**LATEST**

Saved at: **2026-09-29 23:15:39 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / Draft PR #8

Work-basis HEAD: `de642e9724e1f7b053636962bf3b407066465022`

Checkpoint-result HEAD: this file cannot contain the SHA of the commit that writes itself; use the commit produced by this checkpoint update.

Supersedes the prior canonical checkpoint saved at 2026-09-29 16:12:02 JST.

## Current state

V1/V2/Local UI/Launcher evidence remains frozen and unchanged. V3 remains Draft/unmerged under its frozen Contract. JARVIS foundation work remains isolated/reversible and is not a roadmap PASS. PR #8 is open, Draft, mergeable, **82 commits ahead / 0 behind** `main`.

## New work this session

- ToolRegistry capability-change semantics were clarified at `17274a0413db3741872b20c5678c44ba70091037`: stale capability mismatch fails closed; a new capability requires a new request and bound-action identity.
- Memory v1 hardening was strengthened at `5f0271de51ce380acec7478f6c8c7ca3343628ae`: semantic schema validation now explicitly binds non-index collation and AUTOINCREMENT semantics and distinguishes ordinary contention from persisted identity corruption.
- V3 pre-compute review was extended at `de642e9724e1f7b053636962bf3b407066465022`: the reviewed preflight artifact must be consumed by the runtime, and full training requires a distinct post-preflight approval artifact plus durable exactly-once attempt consumption.
- PR #5 authorization/preflight/training CLI source was re-read at exact head `d6d4c1954a85fc716b1c593ac55c85417912418f`.
- Prepared Planner regression tests and further Action Audit / ObservationAdapter / gap-matrix hardening were not saved because normal writes to those paths were rejected. No alternate write route was used.

## Tests / CI / evidence

- Exact work-basis CI #228 / run `36580958900`: **SUCCESS, 6/6 GREEN** across Windows/Ubuntu and Python 3.11-3.13.
- Ubuntu Python 3.11 job `109448697696`: **ruff PASS, pytest 163 PASS**, Local UI loopback mock smoke PASS.
- That job still reports `v2_gate: NOT_PASSED`; no frozen V2 gate was reinterpreted.
- Planner focused tests remain pending because the test-file write was rejected.

## Frozen boundaries unchanged

Frozen V1/V2/Local UI/Launcher evidence, V3 Contract semantics, protected evaluation state, Candidate state, and `main` remain unchanged. No external compute, Candidate generation, promotion, protected-evaluation opening, new credentials, destructive action, or main merge occurred.

## Blockers / authorization boundaries

Normal executable-source/test writes remain intermittently blocked by the tool safety path. The three documentation commits above were saved normally; prepared Planner tests and several additional docs were rejected. No raw Git-object/ref write, force-push, alternate-branch bypass, or overwrite workaround was used.

PR #5 still requires explicit authorization before external compute or real Candidate work. Its free guard closure also requires runtime binding to the exact reviewed preflight artifact plus a separate post-preflight/full-training approval with durable one-attempt semantics.

## Next plan / 今後の方針

1. Land prepared Planner focused tests through the normal Contents path.
2. Implement Memory serialization, row/schema integrity, trusted-clock checks, revision-bound expiry cleanup, and coherent snapshots.
3. Harden Action Audit v1 before its explicit v2 integrity migration.
4. Land immutable ToolRegistry source/tests, then registry-bound durable authorization and execution occurrence.
5. Integrate mock-only audit-before-action, planner recovery, and startup readiness.
6. Continue Personal Context, proactive scheduler, and fixture-only multimodal foundations.
7. Continue free-only PR #5 guard closure without external compute or protected evaluation.
