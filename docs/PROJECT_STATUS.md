# ARK AI Project Status

**LATEST**

Saved at: **2026-09-29 09:58:17 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / Draft PR #8

Work-basis HEAD: `beb3dbfe2b9ea6d401eb6d200c496d6ceec6de12`

Checkpoint-result HEAD: this file cannot contain the SHA of the commit that writes itself; use the commit produced by this checkpoint update.

Supersedes the prior canonical checkpoint saved at 2026-09-29 01:18:56 JST.

## Current state

V1/V2/Local UI/Launcher remain frozen and passed with their existing evidence unchanged. V3 remains Draft/unmerged under its frozen Contract. JARVIS foundation work remains isolated/reversible and is not a roadmap PASS. At this work basis, PR #8 is open, Draft, mergeable, **71 commits ahead / 0 behind** `main`.

## New work this session

- Reconciled `docs/JARVIS_FOUNDATION_GAP_MATRIX.md` at work-basis HEAD `beb3dbfe2b9ea6d401eb6d200c496d6ceec6de12`.
- The matrix now records that action-occurrence identity must be registry-bound rather than request-only, preserving `request_id` as a grouping identity while binding durable occurrence/recovery semantics to the immutable Tool Registry revision/effect/backend.
- The matrix now reflects the already-saved typed `ObservationEnvelope` source and moves multimodal next work to matching repository tests plus fixture-only TEXT/TRANSCRIPT/IMAGE/SCREEN adapters, with live capture still disconnected.
- A fresh read-only/source-ready audit confirmed current Planner, Memory, Action Audit, Tool Registry, Personal Context, observation, and V3 pre-compute boundaries against the exact branch state.
- Isolated free-only validation reproduced the frozen Tool Registry reference revision and bound-action vectors; 1,000 randomized registration orders produced one registry revision.
- Isolated durable-authorization/execution-occurrence prototypes produced exactly one winner under 20-thread and 8-process contention, rejected stale registry binding, kept bearer-token plaintext out of durable bytes, and produced distinct execution identities for separately authorized occurrences.
- SQLite semantic-integrity checks reconfirmed negative `user_version` must fail closed, `table_xinfo`/index/DDL/trigger validation is needed for supported-version schema trust, and REAL values in INTEGER-affinity fields must not be silently coerced with `int(...)`.
- Free-only V3 prototypes exercised durable one-attempt consumption and canonical output/input/code path separation without starting preflight, GPU work, training, Candidate generation, or protected evaluation.
- Fixture-only multimodal prototypes exercised TEXT/TRANSCRIPT/IMAGE/SCREEN observation adaptation without live microphone, camera, desktop capture, external model, or hardware action.
- Executable Tool Registry source and several follow-up contract/evidence updates were retried through the normal GitHub Contents path but rejected by the tool safety path. No raw Git-object/ref write, force-push, alternate-branch bypass, or overwrite workaround was used.

## Tests / CI / evidence

- Exact work-basis CI #217 / run `36506588670` on `beb3dbfe2b9ea6d401eb6d200c496d6ceec6de12`: **SUCCESS, 6/6 jobs GREEN** across Windows/Ubuntu and Python 3.11-3.13.
- Ubuntu Python 3.11: **ruff PASS, pytest 163 PASS**; Local UI Node test step PASS.
- Benchmark and V2 mock-evaluation/compare steps completed; V2 gate output remains `NOT_PASSED` / main merge blocked pending the existing real-review boundary, so no frozen review/evaluation state was reinterpreted.
- Prototype checks listed above are preparation evidence only until matching executable source/tests are saved and exact-head CI passes.
- PR #5 remains Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`.

## Frozen boundaries unchanged

Frozen V1/V2/Local UI/Launcher evidence is unchanged. V3 Contract semantics are unchanged. Protected V2 final evaluation remains unopened. No Candidate weights, promotion, paid/external compute, new credentials/account connection, physical-PC action, destructive/irreversible action, or main merge occurred.

## Blockers / authorization boundaries

Normal executable-source writes remain intermittently blocked by the tool safety path, and some richer documentation writes were also rejected. This does not justify a bypass. Existing approval boundaries remain unchanged for paid/external compute, real Candidate generation, protected evaluation, promotion, frozen-contract changes, destructive/irreversible work, new credentials/account connections, unavailable physical-PC actions, and main merge. No new user-action blocker was introduced.

## Next plan / 今後の方針

1. Retry Planner invariant hardening and immutable ToolRegistry source/tests through the normal write path only.
2. Land Memory bootstrap/schema-fingerprint/persisted-row/CAS/expiry/coherent-snapshot hardening.
3. Harden Action Audit v1 behavior and implement the explicit v1-to-v2 integrity migration only with matching tests.
4. Integrate registry-bound durable one-shot authorization, execution occurrences, trusted-clock audit-before-action, and disconnected/mock ActionExecutor.
5. Add planner recovery and startup-readiness source/tests with registry-bound execution context.
6. Implement deterministic Personal Context over the coherent Memory snapshot, then local proactive scheduler state.
7. Land ObservationEnvelope tests and fixture-only multimodal adapters before any live capture integration.
8. Continue free-only V3 guard hardening without opening protected evaluation or starting real Candidate work.
