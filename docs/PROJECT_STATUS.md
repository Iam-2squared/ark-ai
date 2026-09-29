# ARK AI Project Status

**LATEST**

Saved at: **2026-09-29 11:07:26 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / Draft PR #8

Work-basis HEAD: `7b613e6c8010329101e99e353fdaee55143d441d`

Checkpoint-result HEAD: this file cannot contain the SHA of the commit that writes itself; use the commit produced by this checkpoint update.

Supersedes the prior canonical checkpoint saved at 2026-09-29 09:58:17 JST.

## Current state

V1/V2/Local UI/Launcher remain frozen and passed with their existing evidence unchanged. V3 remains Draft/unmerged under its frozen Contract. JARVIS foundation work remains isolated/reversible and is not a roadmap PASS. At this work basis, PR #8 is open, Draft, mergeable, **74 commits ahead / 0 behind** `main`.

## New work this session

- Added `tests/fixtures/memory_schema_v1.json` at commit `a208ed52b3dc318bbc426ff3df32c1bc338fddef`, freezing the existing Memory schema-v1 semantic descriptor for future same-version validation without changing frozen schema DDL.
- Hardened `PlanStep.depends_on` at commit `7b613e6c8010329101e99e353fdaee55143d441d`: dependency input now requires an ordered `Sequence` and is canonicalized to tuple, so set/frozenset/generator inputs no longer create process-dependent dependency order.
- Re-read PR #5 at `d6d4c1954a85fc716b1c593ac55c85417912418f` and kept it Draft/unmerged. Free-only review reconfirmed that full Candidate compute still needs a distinct hash-addressed second approval artifact in addition to existing preflight approval and snapshot booleans.
- Retried Planner immutability/transition hardening, immutable ToolRegistry source, Memory negative-version hardening, focused regression tests, Action Audit schema fixture, and follow-up docs through the normal GitHub Contents path. Those writes were rejected by the tool safety path; no raw Git-object/ref write, alternate-branch bypass, force-push, or overwrite workaround was used.

## Tests / CI / evidence

- Exact work-basis CI #220 / run `36510625086` on `7b613e6c8010329101e99e353fdaee55143d441d`: **SUCCESS, 6/6 jobs GREEN** across Windows/Ubuntu and Python 3.11-3.13.
- Ubuntu Python 3.11 job `109221689442`: **ruff PASS, pytest 163 PASS**; Local UI Node tests PASS.
- Benchmark and fixture-only V2 evaluation/compare steps completed. The CI output remains `v2_gate: NOT_PASSED` / main merge blocked, so no frozen V2 review/evaluation state was reinterpreted.
- The new Memory schema fixture is reference data only; runtime semantic-schema validation source/tests are still pending.
- PR #5 remains Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`; no preflight, GPU training, Candidate generation, or protected V2 opening was started.

## Frozen boundaries unchanged

Frozen V1/V2/Local UI/Launcher evidence is unchanged. V3 Contract semantics are unchanged. Protected V2 final evaluation remains unopened. No Candidate weights, promotion, paid/external compute, new credentials/account connection, physical-PC action, destructive/irreversible action, or main merge occurred.

## Blockers / authorization boundaries

Normal executable-source/test writes remain intermittently blocked by the tool safety path. This does not justify a bypass. Existing approval boundaries remain unchanged for paid/external compute, real Candidate generation, protected evaluation, promotion, frozen-contract changes, destructive/irreversible work, new credentials/account connections, unavailable physical-PC actions, and main merge. No new user-action blocker was introduced.

## Next plan / 今後の方針

1. Land matching Planner regression tests, then finish immutable topology/status, exact transition type/revision checks, immutable transition rules, and sorted derived traversal through the normal write path only.
2. Consume `tests/fixtures/memory_schema_v1.json` in Memory bootstrap/schema validation; then add persisted-row validation, writer locking, CAS normalization, expiry-safe purge, and coherent multi-namespace snapshot.
3. Harden Action Audit v1 bootstrap/row validation and implement only the explicit v1-to-v2 integrity migration with matching tests.
4. Land immutable ToolRegistry and registry-bound action identity before durable one-shot authorization/execution occurrence work.
5. Integrate trusted-clock audit-before-action, disconnected/mock executor, planner recovery, and startup readiness.
6. Implement deterministic Personal Context over coherent Memory, then local proactive scheduler state.
7. Add ObservationEnvelope tests and fixture-only multimodal adapters before any live capture integration.
8. Continue free-only PR #5 guard closure, including separate hash-addressed full-training approval and exactly-once attempt consumption, without opening protected evaluation or starting real Candidate work.
