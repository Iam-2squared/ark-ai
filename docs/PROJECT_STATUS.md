# ARK AI Project Status

**LATEST**

Saved at: **2026-10-07 14:47:50 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / Draft PR #8

Work-basis HEAD: `0906c13a356664d17da27f00a5559562bb86d14b`

Checkpoint-result HEAD: this file cannot contain the SHA of the commit that writes itself; use the
resulting commit SHA from this checkpoint update as the authoritative checkpoint-result HEAD.

## Current state

V1/V2/Local UI/Launcher evidence is frozen and unchanged. PR #5 remains Draft/unmerged at
`d6d4c1954a85fc716b1c593ac55c85417912418f` under its controlling V3 Contract. JARVIS
foundation work remains isolated/reversible and is not a roadmap PASS.

PR #8 is open, Draft, mergeable, **112 commits ahead / 0 behind** `main` at this work basis.

## New work this session

- Commit `0906c13a356664d17da27f00a5559562bb86d14b` reconciled
  `docs/JARVIS_FOUNDATION_GAP_MATRIX.md` with the actual landed planner/observation source:
  exact nested ToolCall/transition ingress and FAILED/CANCELLED/BLOCKED descendant propagation
  are already repository source, while reusable production observation adapters remain unlanded.
- CI #258 / run `37577772525` for `0906c13a356664d17da27f00a5559562bb86d14b`
  completed **SUCCESS, 6/6 GREEN**.
- Immutable ToolRegistry source was revalidated locally against the frozen registry/bound-action
  vectors and 256 randomized registration orders; focused local suite **4/4 PASS**.
- Exact PermissionGate ingress/non-consuming grant validation was revalidated locally; focused
  local suite **9/9 PASS**.
- Fixture-only production Observation adapters for TEXT/TRANSCRIPT/IMAGE/SCREEN were revalidated
  locally with adapter-owned hashing, deterministic identity, lineage, and no action authority;
  focused local suite **7/7 PASS**.
- Planner Recovery journal candidate was advanced to append-only SQLite explicit transitions,
  topology/status digests, hash chain + independent tail anchor, public PlanGraph replay,
  fault-before-commit rollback safety, trusted-clock rollback rejection, and same-revision
  concurrency; focused local suite **9/9 PASS**.
- PR #5 free-only strict JSON guard candidate was revalidated against duplicate decoded keys,
  nested duplicates, NaN/Infinity, float overflow, invalid UTF-8, and exact str/bytes ingress;
  focused local suite **11/11 PASS**.
- Total new isolated focused checks this session: **40/40 PASS**. These are local prototype
  results only until the matching source/tests are saved and exact-head CI is GREEN.

## Tests / CI / evidence

CI #258 GREEN jobs:
- Windows 3.12 `112650409243`
- Ubuntu 3.13 `112650409426`
- Ubuntu 3.11 `112650409443`
- Ubuntu 3.12 `112650409456`
- Windows 3.11 `112650409471`
- Windows 3.13 `112650409482`

The prior PR #8 exact source evidence at `9c8a24a4e50a73fdb9e4ca68f1b9fc3cc025d619`
remains CI #257 / run `37384181765` **SUCCESS, 6/6 GREEN**.

PR #5 remains at `d6d4c1954a85fc716b1c593ac55c85417912418f` with prior
CI #151 / run `36223644908` **SUCCESS, 6/6 GREEN**.

Local source-ready evidence is not repository evidence until its source/tests are saved and
exact-head CI is GREEN.

## Frozen boundaries unchanged

No paid/external compute, real training, Candidate adapter/weight generation, protected V2
opening, Candidate promotion, frozen-contract change, new credentials/account connection,
live capture, destructive action, unavailable physical-PC action, or main merge occurred.

## Blockers / authorization boundaries

Executable source/test writes through the normal GitHub Contents path are currently rejected by
the safety layer. This session reconfirmed the blocker for ToolRegistry creation, production
Observation-adapter creation, and PermissionGate source update. No raw Git objects, ref
manipulation, force push, hidden route, or other safeguard bypass was used.

Documentation writes remain possible through the normal Contents path. Do not treat local
source-ready candidates as landed implementation while this blocker persists.

PR #5 still requires explicit authorization before any external compute, real Candidate
generation, protected V2 opening, or promotion.

Populated Action Audit v1 -> occurrence-bound v2 migration and populated Memory v1 ->
independently anchored event-log v2 migration remain blocked until reviewed historical mapping
policies exist.

## Next plan / 今後の方針

1. Retry only the normal permitted source path later: immutable ToolRegistry -> exact-head CI ->
   focused registry tests/export -> exact PermissionGate.
2. While source writes are blocked, continue independent free lanes: Planner Recovery strict
   schema/replay evidence, Memory integrity/CAS/expiry/coherent snapshot, and Observation adapter
   fixtures without connecting live capture.
3. After Registry + PermissionGate are exact-head GREEN, land durable registry-bound one-shot
   authorization -> execution occurrence/replay protection -> trusted-clock audit-before-action
   disconnected executor.
4. After Memory hardening is exact-head GREEN, land coherent multi-namespace snapshot ->
   privacy-safe Personal Context.
5. Continue PR #5 free-only guard closure only; do not start preflight/training, external GPU,
   Candidate generation, protected evaluation, or promotion.
