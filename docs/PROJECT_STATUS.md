# ARK AI Project Status

**LATEST**

Saved at: **2026-09-29 01:09:34 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / Draft PR #8

Work-basis HEAD: `f582fc936e054ebcc64ed6e1d03513e00b692d06`

Checkpoint-result HEAD: this file cannot contain the SHA of the commit that writes itself; use the commit produced by this checkpoint update.

Supersedes the prior canonical checkpoint saved at 2026-09-28 23:16:04 JST.

## Current state

V1/V2/Local UI/Launcher remain frozen and passed. V3 remains Draft/unmerged under its frozen Contract. JARVIS foundation work remains isolated/reversible and is not a roadmap PASS. Before this checkpoint commit, PR #8 was open, Draft, mergeable, 46 commits ahead and 0 behind `main`.

## New work this session

- Added `docs/FOUNDATION_SOURCE_READY_HARDENING.md` at `f582fc936e054ebcc64ed6e1d03513e00b692d06`, consolidating the exact source/test hardening queue for Planner, SQLite Memory, Action Audit, and the execution-safety chain.
- Re-read PR #5 HEAD `d6d4c1954a85fc716b1c593ac55c85417912418f` without modifying it and confirmed the official CLI has stronger proof checks than directly importable lower-level GPU runners. The review also reconfirmed the durable single-attempt, RNG seeding, whole-run resource-measurement, and Candidate output-path separation gaps. No compute was started.
- Retried the normal existing-source write path for Planner hardening after exact HEAD/blob reads. The connector safety path rejected the write, so no bypass, raw Git object write, force-push, or alternate-branch workaround was used.
- A new-source ToolRegistry implementation write and additional documentation writes were also rejected by the same safety path; work remained limited to safe review/specification after those rejections.

## Tests / CI / evidence

- CI #192 / run `36448417070` on exact work-basis HEAD `f582fc936e054ebcc64ed6e1d03513e00b692d06`: **SUCCESS**.
- PR #8 is 46 commits ahead / 0 behind `main` at the work-basis HEAD.
- PR #5 remains Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`.
- Prototype-only findings remain separate from repository implementation evidence until matching source/tests land and exact-head CI passes.

## Frozen boundaries unchanged

Frozen V1/V2/Local UI/Launcher evidence is unchanged. V3 Contract semantics are unchanged. Protected V2 final evaluation remains unopened. No Candidate weights, promotion, paid/external compute, destructive action, credentials/account connection, physical-PC action, or main merge occurred.

## Blockers / authorization boundaries

Existing executable-source updates remain blocked by the tool safety path. This is not a reason to weaken or bypass the normal write path. Existing approval boundaries remain unchanged for paid/external compute, real Candidate generation, protected evaluation, promotion, frozen-contract changes, destructive/irreversible work, new credentials/account connections, unavailable physical-PC actions, and main merge. No new user-action blocker was introduced.

## Next plan / 今後の方針

1. Retry the normal Planner source/test hardening path from the latest exact HEAD.
2. Land Memory schema/value integrity, bootstrap serialization, CAS/clock ordering, search-expiry, and revision-bound cleanup hardening.
3. Harden Action Audit initialization/append ordering and explicit migration.
4. Add the immutable ToolRegistry source/tests, then durable one-shot authorization/execution occurrence and disconnected executor integration.
5. Add planner recovery/startup-readiness source/tests.
6. Continue Personal Context, proactive, typed observation, observability, and free-only V3 guard work while earlier write lanes are blocked.
