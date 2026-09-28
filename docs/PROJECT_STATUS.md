# ARK AI Project Status

**LATEST**

Saved at: **2026-09-29 01:18:56 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / Draft PR #8

Work-basis HEAD: `3ec18a96fdd90de43e808ddc1e16d1ffc890098e`

Checkpoint-result HEAD: this file cannot contain the SHA of the commit that writes itself; use the commit produced by this checkpoint update.

Supersedes the prior canonical checkpoint saved at 2026-09-29 01:09:34 JST.

## Current state

V1/V2/Local UI/Launcher remain frozen and passed. V3 remains Draft/unmerged under its frozen Contract. JARVIS foundation work remains isolated/reversible and is not a roadmap PASS. Before this checkpoint commit, PR #8 was open, Draft, mergeable, **51 commits ahead / 0 behind** `main`.

## New work this session

- Added `docs/FOUNDATION_SOURCE_READY_HARDENING.md` to consolidate the exact Planner, Memory, Action Audit, registry, durable-authorization, executor, and recovery implementation queue.
- Added `docs/TOOL_REGISTRY_IMPLEMENTATION_CONTRACT.md` with deterministic registry-revision, duplicate-rejection, immutable lookup, and exact backend-binding rules.
- Added `docs/PERSISTED_EVENT_VALIDATION_CONTRACT.md` so Memory/Audit/Planner persisted events must be exact-value validated before conversion or recovery.
- Added `docs/STARTUP_READINESS_IMPLEMENTATION_PLAN.md` with deterministic component-scoped readiness propagation and lane isolation.
- Added executable source `src/ark/observations.py` at `3ec18a96fdd90de43e808ddc1e16d1ffc890098e`: typed content-minimized observation envelopes with exact kind/time/schema/digest validation and deterministic observation IDs.
- Isolated validation of the observation-envelope logic completed **15 focused assertions PASS**, including deterministic identity, seven field-binding changes, raw-string kind rejection, bool/negative time rejection, malformed digest rejection, and bool schema rejection.
- Matching repository test-file creation and existing Planner source hardening were retried through the normal write path but rejected by the tool safety path. No alternate branch, raw Git object write, force-push, or overwrite workaround was used.
- PR #5 was re-read without modification. Its existing hard stops remain intact; no external compute or Candidate work was started.

## Tests / CI / evidence

- Exact-head CI #197 / run `36449571876` on `3ec18a96fdd90de43e808ddc1e16d1ffc890098e`: **SUCCESS, 6/6 jobs GREEN**.
- Ubuntu Python 3.11 log: **ruff PASS, pytest 163 PASS**; Local UI Node test step also PASS.
- Observation envelope isolated checks: **15 PASS**. These are prototype/focused evidence until matching repository tests are saved.
- PR #5 remains Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`.

## Frozen boundaries unchanged

Frozen V1/V2/Local UI/Launcher evidence is unchanged. V3 Contract semantics are unchanged. Protected V2 final evaluation remains unopened. No Candidate weights, promotion, paid/external compute, credentials/account connection, physical-PC action, destructive/irreversible action, or main merge occurred.

## Blockers / authorization boundaries

Normal updates to existing executable source and the attempted observation test file remain intermittently blocked by the tool safety path. This does not justify a bypass. Existing approval boundaries remain unchanged for paid/external compute, real Candidate generation, protected evaluation, promotion, frozen-contract changes, destructive/irreversible work, new credentials/account connections, unavailable physical-PC actions, and main merge. No new user-action blocker was introduced.

## Next plan / 今後の方針

1. Retry matching repository tests for `src/ark/observations.py` through the normal path.
2. Retry Planner exact-type/immutability source hardening, then land Memory bootstrap/integrity/CAS/expiry hardening.
3. Harden Action Audit initialization/append ordering and explicit migration.
4. Implement immutable ToolRegistry, durable one-shot authorization/execution occurrence, and disconnected ActionExecutor.
5. Implement startup readiness and planner recovery source/tests.
6. Add deterministic Personal Context retrieval over hardened Memory, then continue proactive/observability/local multimodal integration.
7. Continue free-only V3 guard review without opening protected evaluation or starting real Candidate work.
