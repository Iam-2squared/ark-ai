# ARK AI Project Status

**LATEST**

Saved at: **2026-09-28 15:19:18 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / Draft PR #8

Work-basis HEAD: `d416540dbfb58affd4a2b9f055682c33b1d7ce45`

Checkpoint-result HEAD: this file cannot contain the SHA of the commit that writes itself; use the commit produced by this checkpoint update.

## Current state

V1/V2/Local UI/Launcher remain frozen and passed. V3 remains Draft/unmerged under its frozen Contract. JARVIS foundation work remains isolated/reversible and is not a roadmap PASS. At the work-basis HEAD, PR #8 is open, Draft, mergeable, 39 commits ahead and 0 behind `main`.

## New work this session

- `955d161c62730412928a05f079eb2dbe8c4e306d`: added the local-state migration contract.
- `665ccfae471ed560acca130a6a4e07682b2817fd`: recorded isolated foundation prototype evidence, explicitly separated from repository implementation evidence.
- `d416540dbfb58affd4a2b9f055682c33b1d7ce45`: added component-scoped startup readiness/recovery semantics.
- Isolated validation advanced planner invariants, Memory snapshot/expiry ordering, SQLite migration crash recovery, startup dependency readiness, proactive scheduler state, typed observations, Personal Context determinism, and free-only V3 resource/path guards.
- The normal executable-source update for planner hardening was re-attempted after exact-head/blob checks and rejected by the tool safety path; no bypass was used and that source change is not counted as landed.

## Tests / CI / evidence

- CI #183 / run `36384714675` on `955d161c62730412928a05f079eb2dbe8c4e306d`: SUCCESS, 6/6 jobs GREEN. Ubuntu 3.11: Ruff PASS, pytest 163 PASS, Local UI Node tests 6 PASS.
- CI #185 / run `36385339804` on work-basis HEAD `d416540dbfb58affd4a2b9f055682c33b1d7ce45`: SUCCESS. One Windows Python 3.12 job initially hit a transient socket-abort failure in the oversized-body UI test; only that failed job was rerun and it passed. Final job set is 6/6 GREEN. Frozen Local UI source was unchanged.
- PR #5 remains Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`.
- Prototype-only checks are not promoted to repository implementation evidence.

## Frozen boundaries unchanged

Frozen V1/V2/Local UI/Launcher evidence is unchanged. V3 Contract semantics are unchanged. Protected V2 final evaluation remains unopened. No Candidate weights, promotion, paid/external compute, destructive action, or main merge occurred.

## Blockers / authorization boundaries

Normal writes to executable source/tests remain blocked by the tool safety path. Existing authorization gates remain in force for paid/external compute, real Candidate generation, protected evaluation, promotion, frozen-contract changes, destructive/irreversible work, new credentials/account connections, unavailable physical-PC actions, and main merge. No new user-action blocker was introduced.

## Next plan / 今後の方針

1. Retry only the normal source path for planner invariant hardening after an exact-head re-read.
2. Land Memory durability plus snapshot-after-read expiry semantics.
3. Harden Action Audit initialization, shape/integrity checks, and lock-before-clock ordering.
4. Implement reusable local-state migration/startup-readiness source and process recovery tests.
5. Continue immutable ToolRegistry, durable one-shot authorization, action-occurrence reconciliation, and mock ActionExecutor integration.
6. Continue Personal Context, proactive scheduler, typed observation, and V3 free-only path/resource guard work as dependencies permit.
