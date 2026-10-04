# ARK AI Project Status

**LATEST**

Saved at: **2026-10-05 01:50:55 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / Draft PR #8

Work-basis HEAD: `59696fc22abd0a3b434efa73970230b2f2e426c5`

Checkpoint-result HEAD: this file cannot contain the SHA of the commit that writes itself; use the commit produced by this checkpoint update.

Supersedes the prior canonical checkpoint saved at 2026-10-01 22:45:29 JST.

## Current state

V1/V2/Local UI/Launcher evidence remains frozen and unchanged. PR #5 remains Draft/unmerged under its frozen V3 Contract. JARVIS foundation work remains isolated/reversible and is not a roadmap PASS. At the work-basis HEAD, PR #8 is open, Draft, mergeable, **102 commits ahead / 0 behind** `main`.

The Planner exact-terminal hardening is now source-saved and regression-covered on GitHub. `src/ark/agency/planner.py` remains blob `f0e08756b82522e90a34b62d9bcd15799b61d51a`.

## New work this session

- Saved commit `59696fc22abd0a3b434efa73970230b2f2e426c5`: dedicated Planner regressions now cover exact transition `step_id`, bool revision rejection, CANCELLED transitive blocking, and explicit BLOCKED transitive blocking.
- Exact-head CI #248 / run `37217751164` completed **SUCCESS, 6/6 GREEN** for the Planner regression commit.
- A normal Contents-API update for `src/ark/observations.py` was attempted twice after exact-head re-read and was rejected by the OpenAI/GitHub write-safety path. No raw Git object/ref, force-push, alternate branch, or hidden write route was used.
- A normal Contents-API update for PR #5 `src/ark/learning/execution.py` strict canonical snapshot loading was also rejected by the write-safety path. PR #5 remains unchanged at `d6d4c1954a85fc716b1c593ac55c85417912418f`.
- Source-ready Startup Readiness core now defines an immutable acyclic component graph, exact local/effective states, stable failure codes, deterministic snapshot identity, and lane-local dependency blocking. Focused validation: **9/9 PASS**.
- The prior source-ready lane-exposure tests were found incompatible with the new readiness-core invariant because non-READY components lacked stable failure codes. A replacement lane-exposure package was produced; combined readiness-core + lane-exposure validation is **17/17 PASS**. The older lane-exposure source-ready patch is superseded.
- PR #5 free-only source-ready approval-consumption ledger now records exactly-once use of already-reviewed approval evidence by SHA-256 and scope before runtime entry. It does not create/forge approval or start compute. Focused validation: **7/7 PASS**.
- PR #5 free-only verify-to-use materialization now copies only an exact approved local file manifest into a new create-only directory, rejects symlinks/path traversal/extra files, and re-verifies bytes before use. Focused validation: **7/7 PASS**. No model load, GPU, network, or external compute occurred.

## Tests / CI / evidence

- Exact work-basis CI #248 / run `37217751164`: **SUCCESS, 6/6 GREEN**.
- Jobs GREEN:
  - Windows 3.13 `111481637017`
  - Ubuntu 3.12 `111481637091`
  - Ubuntu 3.11 `111481637117`
  - Windows 3.12 `111481637123`
  - Ubuntu 3.13 `111481637150`
  - Windows 3.11 `111481637174`
- `main...59696fc22abd0a3b434efa73970230b2f2e426c5`: **102 ahead / 0 behind**.
- Source-ready focused checks this session:
  - Startup Readiness core: **9/9 PASS**.
  - Startup Readiness core + replacement lane exposure: **17/17 PASS** combined.
  - V3 approval-consumption ledger: **7/7 PASS**.
  - V3 verify-to-use materialization: **7/7 PASS**.
- Source-ready evidence remains prototype/local evidence until each package is saved to GitHub and exact-head CI is GREEN.

## Frozen boundaries unchanged

Frozen V1/V2/Local UI/Launcher evidence, V3 Contract semantics, protected evaluation state, Candidate state, PR #5 Draft/unmerged state, and `main` remain unchanged.

No paid/external compute, real training, Candidate adapter/weight generation, protected/frozen V2 opening, Candidate promotion, new credentials/account connection, destructive action, unavailable physical-PC action, or main merge occurred.

## Blockers / authorization boundaries

Normal executable-source writes remain intermittently rejected by the safety path even though the Planner regression test update succeeded through the normal Contents API. Continue to retry only the normal permitted path; do not bypass safeguards.

PR #5 still requires explicit authorization before any external compute, real Candidate generation, protected V2 opening, or promotion. The new approval-consumption and materialization packages are local governance foundations only and do not constitute human approval or compute authorization.

## Next plan / 今後の方針

1. Retry Observation exact-type source/tests only through the normal Contents API; after source lands, take exact-head GREEN before adding dependent fixture adapters.
2. Land Planner durable recovery journal/anchor/replay now that Planner terminal propagation and dedicated regressions are exact-head GREEN.
3. Land Startup Readiness core, then the replacement lane-exposure package and exact-head integration evidence.
4. Continue Memory exact ingress -> semantic schema/bootstrap -> row/event integrity -> serialized writer/CAS/trusted-clock/expiry -> coherent single/multi-namespace snapshots -> Personal Context.
5. Land immutable ToolRegistry -> exact PermissionGate -> durable authorization -> durable execution occurrence -> occurrence-bound Action Audit v2 -> disconnected/mock executor.
6. Continue PR #5 free-only strict canonical snapshot/evidence, reviewed approval consumption, verify-to-use materialization, runtime binding, CandidateRegistry durability, attempt ledger/runner, run-manifest and execution-receipt closure.
7. Keep populated Action Audit v1 -> occurrence-bound v2 migration blocked until a reviewed historical occurrence-mapping policy exists; do not fabricate `execution_id` or `bound_action_id`.
