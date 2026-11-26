# ARK AI Run919 — Planner status carrier preaccess, inert registered policy, WAL probe and observation privacy

**Observed report time (Asia/Tokyo/JST):** 2026-11-16T22:00:34.251+09:00. This is a reporting wall-clock observation, **not** a trusted clock for tool actions, approval, authorization or audit.

**Work basis:** `15f93c5437be10dc557ccf75f7902d2b336c7f44` (Run918 checkpoint). **Branch / PR:** `research/jarvis-foundations` / [Draft #8](https://github.com/Iam-2squared/ark-ai/pull/8). All work was disconnected, zero-new-cost, non-UI and reversible. **Overall ARK/JARVIS: NOT_PASSED.**

## Four coherent independent work packages — 45 regression cases authored

1. **Planner foreign-status label preaccess** — [source `235553ec`](https://github.com/Iam-2squared/ark-ai/commit/235553ecd513631161949c98dad575cdbf9f8a2c), [17 tests `331775a8`](https://github.com/Iam-2squared/ark-ai/commit/331775a896703f04dc8982c6529d5d320147544a). `PlanGraph._assert_status_epoch` now requires an exact `str` for a retained status `step_id` **before** calling equality. A reflectively substituted field cannot execute a foreign `__eq__`/`__ne__` merely because the graph checks its own status. Test public reads `statuses`, `status_digest`, `ready_steps`, `transition` against four foreign fields; an unaffected detached-status control still permits normal transitions. No frozen `PlanStepStatus` API or journal schema changed.
2. **Registered PermissionGate non-dispatch** — [5 tests `93b3fabc`](https://github.com/Iam-2squared/ark-ai/commit/93b3fabc0613943beabb61a1039cc3bf48a730ed). Mutating previously yielded exact grants, one-shot token IDs or action scopes in a generator must fail before a process-local token is consumed. The registry's WRITE effect cannot be downgraded by omitting the token. A valid local token-spend control still **never executes the inert backend**. The test does not establish a durable approval or restart-safe exactly-once effect.
3. **Disposable WAL diagnostic preflight** — [12 tests `64b0b5a1`](https://github.com/Iam-2squared/ark-ai/commit/64b0b5a1964711c1103d4712e9328f732f210c27). Reject wrong type, foreign equality/hash, alias string kind, unknown store kind and nonboolean keeper before temporary-file or subprocess creation. Exercise bounded CLI iteration parse. These tests do **not** reproduce or resolve the actual two-process last-close WAL/SHM race; the sidecar issue remains UNKNOWN/FAIL.
4. **Observation metadata before private hashing** — [11 tests `0de4c0d8`](https://github.com/Iam-2squared/ark-ai/commit/0de4c0d88a1bf0f26648a1f42b4d309377c5462b). Invalid multibyte source, NUL privacy label, Boolean time, nonlowercase parent digest and surrogate label never reach a substituted private fixture hash callback, for both text and binary modes. A valid synthetic text control contains only its digest in the envelope. Direct frozen ObservationEnvelope NUL behavior was **not** changed.

**CI-compatible formatting repairs:** [Planner import `5310600b`](https://github.com/Iam-2squared/ark-ai/commit/5310600b1a06c6d453a73dc87b168ca181d51f08), [policy import `5c4403b9`](https://github.com/Iam-2squared/ark-ai/commit/5c4403b907de6f67e45087d60b2abc40d883c32e), [WAL import `d38e6451`](https://github.com/Iam-2squared/ark-ai/commit/d38e645184180e752183c0f3c8eedfb7e2483659). All preserve test semantics and production safeguards. Initial new-test CI failed before pytest on Ruff I001 in these files; this is **not** evidence of a Python runtime regression or a test PASS.

## CI snapshots: no stale-head promotion

- Run918 checkpoint `15f93c54`: [#43867929396](https://github.com/Iam-2squared/ark-ai/actions/runs/43867929396) **IN PROGRESS**, observed Ubuntu Python 3.11/3.12/3.13 **GREEN 3/3**, Windows three pending at last read.
- First Run919 test HEAD `331775a8`: [#43870497375](https://github.com/Iam-2squared/ark-ai/actions/runs/43870497375) **FAIL 6/6** from newly introduced Ruff import ordering.
- Registered policy HEAD `93b3fabc`: [#43870648557](https://github.com/Iam-2squared/ark-ai/actions/runs/43870648557) **FAIL 6/6**, same inherited lint defect.
- WAL HEAD `64b0b5a1`: [#43870866049](https://github.com/Iam-2squared/ark-ai/actions/runs/43870866049) **FAIL 6/6**, inherited lint defect.
- Observation HEAD `0de4c0d8`: [#43871083825](https://github.com/Iam-2squared/ark-ai/actions/runs/43871083825) observed Ubuntu FAIL; inherited lint defect.
- Lint-repaired source/test HEAD `d38e6451`: [#43871632186](https://github.com/Iam-2squared/ark-ai/actions/runs/43871632186) **IN PROGRESS** at last read. All six-job GREEN **NOT CERTIFIED** on this HEAD. A later report/checkpoint commit triggers a new check without manual workflow dispatch.

**45 new tests AUTHORED**, not 45 passing tests or verified real hardware results. No local full suite or real GGUF run was performed.

## Frozen contracts, safety and remaining gates

Unchanged: V1/V2/Local UI/Launcher frozen contracts and evidence; protected V2 evaluation; V3 fixed Candidate/provenance/approval/evaluation gates and Draft PR #5; paused new UI/frontend development and Draft PR #9; existing main; SQLite Memory v1 persisted schema, existing Planner journal, PermissionGate's refusal to claim durable authorization. No external/paid compute, real Candidate adapter/training, real user content ingestion, new credentials, backend execution, trusted human decision, automatic retry, force push, raw Git safeguard workaround, irreversible action or main merge.

**Unresolved:** exact-head six-matrix CI pending; actual WAL/SHM two-process last-close/alias custody race; persistent independent authorization and audit-before-action; cross-store CAS/occurrence integrity; real human approval, trusted clock, and physical offline model gate. JARVIS complete system **NOT_PASSED**.

## Next plan / 今後の方針

1. Inspect the final exact HEAD's six CI jobs and address any Python test/runtime errors via the normal Contents API. Keep lint fixed, do not weaken rejection checks; overlap with different non-UI modules.
2. Improve disposable WAL/SHM last-close constructor/read/sidecar phase diagnosis, with no automatic unknown retry and no path disclosure.
3. Prove Memory event high-water/CAS/expiry and Planner COMMIT-UNKNOWN end-to-end recovery on exact verified lower-layer HEAD.
4. Bind immutable Registry, exact PermissionGate, trusted-clock audit-before-action and occurrence ledger to a **disconnected mock executor only** after the prerequisite GREEN gate. Continue Personal Context privacy, proactive backend and free-only V3 path/identity work.
