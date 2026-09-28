# ARK AI Project Status

**LATEST**

Saved at: **2026-09-28 23:16:04 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / Draft PR #8

Work-basis HEAD: `109f411bdea17d91f18e977475785bd13d07bf63`

Checkpoint-result HEAD: this file cannot contain the SHA of the commit that writes itself; use the commit produced by this checkpoint update.

## Current state

V1/V2/Local UI/Launcher remain frozen and passed. V3 remains Draft/unmerged under its frozen Contract. JARVIS foundation work remains isolated/reversible and is not a roadmap PASS. PR #8 is open, Draft, mergeable, 44 commits ahead and 0 behind `main`.

## New work this session

- `109f411bdea17d91f18e977475785bd13d07bf63`: added SQLite persisted-value integrity findings.
- Reproduced that legacy SQLite affinity can preserve REAL values in INTEGER-affinity fields while current readers can coerce them; legacy Memory primary-key DDL can also admit NULL rows.
- A stricter persisted-row validator rejected 13/13 malformed Memory fixtures.
- Planner source-ready checks remained deterministic across 1000 randomized registration orders and rejected unordered dependencies, raw-string states, and bool revisions.
- An isolated Action Audit migration reference preserved historical timestamps and completed 20/20 rounds of 16-way concurrent migration with exactly one migrator per round.
- Normal executable-source writes were retried after exact-head/blob reads and remained blocked by the tool safety path; no bypass path was used.

## Tests / CI / evidence

- CI #190 / run `36434202878` on exact work-basis HEAD: **SUCCESS, 6/6 jobs GREEN**.
- Prior CI #189 / run `36413875696`: SUCCESS, 6/6 GREEN.
- Memory persisted-row validator: 13/13 malformed fixtures rejected.
- Planner prototype: deterministic across 1000 randomized registration orders.
- Action Audit migration prototype: 20/20 concurrent rounds PASS.
- Prototype-only checks remain separate from repository implementation evidence.
- PR #5 remains Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`.

## Frozen boundaries unchanged

Frozen V1/V2/Local UI/Launcher evidence is unchanged. V3 Contract semantics are unchanged. Protected V2 final evaluation remains unopened. No Candidate weights, promotion, paid/external compute, destructive action, or main merge occurred.

## Blockers / authorization boundaries

Executable source/test writes remain blocked by the tool safety path. Existing approval boundaries remain unchanged for paid/external compute, real Candidate generation, protected evaluation, promotion, frozen-contract changes, destructive/irreversible work, new credentials/account connections, unavailable physical-PC actions, and main merge. No new user-action blocker was introduced.

## Next plan / 今後の方針

1. Retry the normal planner source/test hardening path.
2. Land Memory schema/value integrity, CAS, clock-ordering, search-expiry, and revision-bound cleanup hardening.
3. Harden Action Audit initialization/append ordering and explicit schema migration.
4. Continue immutable ToolRegistry, durable one-shot authorization/execution occurrence, and disconnected executor integration.
5. Add planner recovery and startup-readiness source/tests.
6. Continue Personal Context, proactive, typed observation, observability, and free-only V3 guard work.
