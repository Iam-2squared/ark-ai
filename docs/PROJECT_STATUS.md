# ARK AI Project Status

**LATEST**

Saved at: **2026-10-13, 00:37:52 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / Draft, unmerged PR #8

Work-basis HEAD: `1ebeafe6d7ba8ffd58a32cd0d83d0567a66d256c`.

Checkpoint-result HEAD: this self-updating file cannot contain the SHA of the commit that
writes it. The GitHub Contents update result for this checkpoint commit is authoritative;
CI #267 below applies to the **work-basis source HEAD**, not automatically to this
subsequent documentation-only checkpoint commit.

## Overall current ARK state

V1/V2/Local UI/Launcher contracts and evidence remain frozen and unchanged.
`main` is `7a843f17eb96ed13d66f23b58b06406b3002e405`.
PR #5 V3 remains Draft/unmerged at `d6d4c1954a85fc716b1c593ac55c85417912418f`;
no protected evaluation was opened or later PASS declared. PR #8 remains Draft,
reversible, and unmerged, not a JARVIS completion or official roadmap PASS.

## NEW work this invocation

- Restored PR #8 source CI after public registry exports commit
  `3ea77091a9725341f3e3e79d77ff0257f577b26b` caused Ruff I001.
  The **only source change** was a reorder of the `.policy` and `.registry`
  imports in `src/ark/agency/__init__.py`. Normally permitted GitHub Contents
  update succeeded at `1ebeafe6d7ba8ffd58a32cd0d83d0567a66d256c`.
- The exact source HEAD above passed CI #267 / run `38270375604`:
  **SUCCESS 6/6 GREEN**, Windows and Ubuntu, Python 3.11/3.12/3.13.
  Previous #266 / run `38244247324` was FAIL 6/6 for I001 on an older HEAD.
- Prepared reference-vector/non-dispatch ToolRegistry repository tests for the
  already-committed fixture files. A normal GitHub Contents `create_file` write
  for `tests/test_tool_registry_committed_vectors.py` was blocked by safety
  checks, so no such test was saved and **its CI evidence does not exist**.
- Advanced two **detached, reversible, offline-only** modules in Run 121:
  paged Memory event-chain continuity (21 new tests) and per-source Observation
  liveness (23 new tests). Neither source/test module is in PR #8.
  Run121 detached Linux/Python 3.13.5 Agency **2555/2555 PASS**,
  independent V3 guards **186/186 PASS**, total **2741/2741 PASS**;
  source ZIP SHA-256 `f49aff22ec9fc0c5204719b305b658a81b3316f9108f6c941c2be432275f601d`.
  All 311 prior Run120 source bytes are unchanged; 4 new files; 315 source
  hashes match the ZIP manifest. Clean patch replay new tests **44/44 PASS**.
  No Windows/actual Python 3.11/3.12/Ruff run was performed for the detached candidate.

## Tests / CI / evidence

CI #267 / `38270375604`, source HEAD `1ebeafe6d7ba8ffd58a32cd0d83d0567a66d256c`:

- Ubuntu 3.11 job `114882867967`: SUCCESS
- Ubuntu 3.12 job `114882868485`: SUCCESS
- Ubuntu 3.13 job `114882868378`: SUCCESS
- Windows 3.11 job `114882868301`: SUCCESS
- Windows 3.12 job `114882868373`: SUCCESS
- Windows 3.13 job `114882868279`: SUCCESS

Run121 offline test evidence is **not** exact-head GitHub CI evidence.
The Run121 ZIP is not safe to overwrite onto PR #8: its lower-level module
dependencies and implementation differ from the GitHub branch.

## Frozen boundaries unchanged

No paid/external GPU compute, paid APIs/services, model training, real Candidate
adapter/weight generation, protected V2 final-evaluation opening, promotion,
frozen-contract change, credentials/account connection, physical-PC device
capture, actual tool dispatch, destructive action, or main merge.

## Blockers / authorization boundaries

Normal GitHub source/test write safety layer rejected the focused ToolRegistry
repository-test addition. No bypass, raw Git object, alternate ref-write, force
push, or duplicate CI workflow was used. Keep all detached Memory/Observation/
Planner/Scheduler/Personal Context work isolated until prerequisites are
reviewed and integrated with exact-head GREEN evidence.

PR #5 remains subject to frozen Contract and explicit approval for any real
training, provider/billing, Candidate generation, protected evaluation or promotion.
Preserve populated historical audit/Memory migration boundaries until reviewed.

## Next plan / 今後の方針

1. Add focused ToolRegistry committed-fixture identity/immutability/non-dispatch
   tests through the normal path when permitted; require exact-head CI GREEN.
2. Then integrate Registry-bound PermissionGate, durable one-shot authorization,
   execution occurrence/replay protection and trusted-clock audit-before-action
   only after their prerequisite invariants are GREEN.
3. Advance independently tested Memory CAS/event/expiry and coherent snapshots;
   integrate detached chain review only once its underlying interfaces match.
4. Continue Planner ambiguous-RUNNING recovery without automatic WRITE replay.
5. Stage fixture-only Observation session/liveness adapters and privacy-safe
   Personal Context/Scheduler without live capture, action authority or user
   consent assumptions. Keep free-only V3 guards isolated.

---

## Historical checkpoint — 2026-10-07 (preserved)

**HISTORICAL — superseded by LATEST above**

Saved at: **2026-10-07 18:50:20 JST (+09:00)**

Branch/PR: `research/jarvis-foundations` / Draft PR #8

Work-basis HEAD: `eb49558c0e6a80df53e246aa1fb0a71b93ec3932`

Checkpoint-result HEAD: this file cannot contain the SHA of the commit that writes itself; use the
resulting commit SHA from this checkpoint update as the authoritative checkpoint-result HEAD.

## Current state

V1/V2/Local UI/Launcher evidence is frozen and unchanged. PR #5 remains Draft/unmerged at
`d6d4c1954a85fc716b1c593ac55c85417912418f` under its controlling V3 Contract. JARVIS
foundation work remains isolated/reversible and is not a roadmap PASS.

PR #8 is open, Draft, mergeable, **114 commits ahead / 0 behind** `main` at this work basis.

## New work this session

- Landed immutable ToolRegistry source at
  `eb49558c0e6a80df53e246aa1fb0a71b93ec3932` through the normal GitHub Contents path.
- The registry snapshots exact `ToolRegistration` values, rejects duplicate names, sorts by
  tool name, exposes a read-only mapping, computes a registration-order-independent revision,
  resolves exact capabilities, and derives registry-bound action IDs from request + registry
  revision + capability/effect/backend identity.
- CI #260 / run `37603020130` for that exact source HEAD completed **SUCCESS, 6/6 GREEN**,
  including Ruff and pytest on Windows/Linux Python 3.11-3.13.
- Offline focused validation reproduced the frozen registry revision and all three bound-action
  reference vectors, exercised 256 randomized registration orders, and verified lookup/bind
  caused zero backend executions: **260 focused checks PASS**. This focused result is local
  evidence only until matching repository tests are saved.
- Read-only Memory review reconfirmed the highest-risk v1 gaps remain exact request/scope ingress,
  persisted row/event storage-class and digest validation, lock-before-clock mutation ordering,
  revision-bound expiry purge, and coherent read snapshots.
- PR #5 free-only audit reconfirmed **8 production modules / 9 `json.loads` parse sites**.
  A shared strict decoder package was prepared for duplicate decoded keys, NaN/Infinity,
  float-overflow-to-infinity, invalid UTF-8, and exact str/bytes ingress, but the normal source
  write was safety-blocked and therefore did not land.
- Production Observation fixture adapters and focused ToolRegistry repository tests/public exports
  were also prepared, but their normal source/test writes were safety-blocked and did not land.

## Tests / CI / evidence

CI #260 GREEN jobs:
- Ubuntu 3.11 `112731721391`
- Ubuntu 3.12 `112731721723`
- Windows 3.11 `112731721736`
- Windows 3.12 `112731721767`
- Ubuntu 3.13 `112731721779`
- Windows 3.13 `112731721793`

The prior PR #8 checkpoint HEAD
`ae967e5cb8a5df40162c3a9223cc25582bae7fb2` remains CI #259 /
run `37578146322` **SUCCESS, 6/6 GREEN**.

PR #5 remains at `d6d4c1954a85fc716b1c593ac55c85417912418f` with
CI #151 / run `36223644908` **SUCCESS**.

Focused local/source-ready evidence is not repository test evidence until matching tests are
saved and their exact-head CI is GREEN.

## Frozen boundaries unchanged

No paid/external compute, real training, Candidate adapter/weight generation, protected V2
opening, Candidate promotion, frozen-contract change, new credentials/account connection,
live capture, destructive action, unavailable physical-PC action, or main merge occurred.

## Blockers / authorization boundaries

After the ToolRegistry source write succeeded, later normal GitHub Contents writes for production
Observation adapters, focused ToolRegistry tests, agency public exports, the PR #5 strict JSON
guard, and a Gap Matrix reconciliation were rejected by the safety layer. No raw Git objects,
ref manipulation, force push, hidden route, or other safeguard bypass was used.

The ToolRegistry source is landed and exact-head CI GREEN, but its frozen-vector/randomized-order
focused repository regressions and public package exports remain pending; do not integrate durable
authorization on top of it until those tests/exports are saved and exact-head GREEN.

PR #5 still requires explicit authorization before any external compute, real Candidate
generation, protected V2 opening, or promotion.

Populated Action Audit v1 -> occurrence-bound v2 migration and populated Memory v1 ->
independently anchored event-log v2 migration remain blocked until reviewed historical mapping
policies exist.

## Next plan / 今後の方針

1. Retry only the normal permitted path later for focused ToolRegistry fixture/reference-vector
   tests and public exports; require exact-head GREEN before dependent integration.
2. Then harden exact PermissionGate ingress + non-consuming grant validation and, only after GREEN,
   land durable registry-bound one-shot authorization -> execution occurrence/replay protection ->
   trusted-clock audit-before-action disconnected executor.
3. Continue independent Memory v1 hardening: exact ingress, schema/row/event integrity,
   lock-before-clock CAS/expiry, then coherent multi-namespace snapshot -> Personal Context.
4. Continue Planner Recovery against the already-landed exact planner state machine; preserve
   rollback safety and RUNNING ambiguity without automatic write replay.
5. Land fixture-only Observation adapters when the normal source path permits; keep live capture
   disconnected.
6. Continue PR #5 free-only guard closure only; do not start preflight/training, external GPU,
   Candidate generation, protected evaluation, or promotion.
