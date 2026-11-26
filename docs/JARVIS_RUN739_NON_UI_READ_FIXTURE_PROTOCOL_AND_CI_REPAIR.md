# Run739 — FREE-ONLY non-UI READ fixture bridge, proactive/tool protocol custody and CI repair

**Branch:** `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8); OPEN, unmerged.  
**Initial exact work-basis HEAD:** `d55156f5d0969ba57273a39e6e2f68dbdf4f8e68`.  
**Initial report-basis HEAD:** `73a37d4b917dc5b3e535ad1545af23daeb246065`. **Subsequent test collection repair:** `1834255647baaae0e731fe5c93d61dabd96ec65f`.  
**Status:** new packages authored and normally saved; latest exact-head CI **NOT YET GREEN** at report creation. No real ToolBackend, restart replay, physical device, external API, protected evaluation, paid compute or Candidate activity.

## A — detached proactive recurrence diagnostic

- [Source `636411a`](https://github.com/Iam-2squared/ark-ai/commit/636411a5a2e59b4c6189044f62a27e66e9141d4c): pin original SHA-256/JSON serializer, regex domains and recurrence budgets *before* caller-asserted clock/opaque policy data is handled. Recheck codec after recurrence serialization and before digest callbacks.
- [Tests `beb2f4d`](https://github.com/Iam-2squared/ark-ai/commit/beb2f4dc54cb62ebebbeebe5d90166a7570acfc4): 13 parameter-expanded cases covering altered protocol, replaced callbacks, deterministic due/exhausted cases, and expired quarantine. No trusted clock, notification permission or durable cursor claim.
- Scope is entirely in-memory and synthetic. A mutated Python process can still compromise application code; these are defensive invariants, not authenticated sandboxing.

## B — disconnected mock tool invocation boundary

- [Source `09846f0`](https://github.com/Iam-2squared/ark-ai/commit/09846f0eb51e92d20ce9878c5374366d8c1783a3): pin `_run`, JSON object hooks, scalar validators, text/tree validators, operation/ID grammar and input limits before handling private fixture JSON. Check codec identity at the nested JSON parse and serialize boundaries.
- [Tests `ee26b2e`](https://github.com/Iam-2squared/ark-ai/commit/ee26b2e8a6cc662be621bd22836db2d20a182dfd): 18 cases. Poisoned helper functions must never receive decoded arguments; legitimate `math.sum` still yields the original deterministic, deny-only fixture.
- **Inherited test expectation repair:** [`43c5894`](https://github.com/Iam-2squared/ark-ai/commit/43c589460be89f312b6029480eadc35dbffa8364) and [`73a37d4`](https://github.com/Iam-2squared/ark-ai/commit/73a37d4b917dc5b3e535ad1545af23daeb246065). Actual Linux 3.11 log for [CI #42629385318](https://github.com/Iam-2squared/ark-ai/actions/runs/42629385318): **11,852 PASS, 5 FAIL, 1 SKIP**; all five were old tests requiring a *later* descriptor failure message after intentionally replacing `_json` or `_run`. Now the helper-graph preaccess gate rejects before either poisoned callback can execute. Existing assertions are updated to require the earlier failure and continue verifying nonexecution; source safety gate is NOT relaxed.

## C — isolated recovered READ to mock-only tool fixture integration

- [Source `2ba7a12`](https://github.com/Iam-2squared/ark-ai/commit/2ba7a12692158ab532a7bafa37f43a49fa36731b): new `ark.agency.disconnected_read_tool_bridge`. It calls the existing deny-only `schedule_detached_read_recovery` and deterministic memory-only `execute_disconnected_fixture_tool` *only for exact READY_MOCK_ONLY steps*. Unknown/running/failed/already-complete steps do not run. The bridge requires an ordered, complete set of ready-only bindings, identical operation identities and a per-step synthetic request ID derived from a domain-separated hash. Result has four permanently false authority properties. It does not persist, dispatch, notify, infer consent or authorize any external action.
- [Tests `0ec6d3b`](https://github.com/Iam-2squared/ark-ai/commit/0ec6d3b997580e5dbb599e548e24fd6d3ccc99f0): 18 cases: deterministic independent fixtures, quarantined/failed ancestors, unverified complete state, rejected duplicate/out-of-order/missing bindings, invalid operations/identities, and no real authority.
- [Collection repairs `f4a23f9`](https://github.com/Iam-2squared/ark-ai/commit/f4a23f9fff5b3f7238044d9fa6202b6217ac52cc) and [`1834255`](https://github.com/Iam-2squared/ark-ai/commit/1834255647baaae0e731fe5c93d61dabd96ec65f): actual [CI #42630060945](https://github.com/Iam-2squared/ark-ai/actions/runs/42630060945) exposed pytest collection rejection of parameter `request` (reserved fixture name). The first repair renamed the test function parameter, but CI still failed because pytest's parametrization key remained `request`. The second repair also changed the decorator to `request_id`. Neither repair changes functional semantics or test acceptance logic; only the second repair is complete.
- **Security limitations:** topological status, previous READ result digests and the bound fixture arguments remain *caller asserted*. A completed upstream status is not authenticated. A mock result is NOT a real tool execution receipt. Any future integration with ToolRegistry/PermissionGate requires independent exact-head GREEN evidence and real authorization design.

## D — read-only V3 hard-boundary audit

- Independently inspected immutable [PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) HEAD `805b377697472268db02650a89c7a94b1c5337c8`, including `src/ark/learning/preflight.py`, `src/ark/learning/training.py` and `docs/v3/PRE_PAID_COMPUTE_GATE.md`. The real training backend still raises `StopRequired`; the preflight path requires explicit authorization and runtime evidence. The gate still lists immutable model/tokenizer identities, approved dataset/provenance decisions, environment pins, actual device/cost/time ceilings and human authorization as unresolved prerequisites.
- No external GPU, paid action, protected V2 opening, Candidate generation, PR #5 write or main merge was attempted. A code-level stop is not a complete runtime security guarantee.

## CI and next verified actions

- **Inherited exact baseline:** [#42620562317](https://github.com/Iam-2squared/ark-ai/actions/runs/42620562317) on initial `d55156f5...`: Windows/Ubuntu Python 3.11/3.12/3.13 **6/6 GREEN** (read independently in this invocation).
- **New/repair CI:** latest test-repair HEAD `73a37d4...` triggered [#42630860457](https://github.com/Iam-2squared/ark-ai/actions/runs/42630860457), **QUEUED/IN PROGRESS** at last observation; do NOT borrow baseline GREEN. Earlier [#42629385318](https://github.com/Iam-2squared/ark-ai/actions/runs/42629385318) failed in five legacy message expectations. [#42630060945](https://github.com/Iam-2squared/ark-ai/actions/runs/42630060945) failed during pytest collection. Repairs have been pushed, not yet verified on six platforms.
- Prioritize (1) exact-head CI diagnosis/repair, (2) bridge result/carrier mutation tests and an explicit mock/registry identity contract, (3) Memory CAS/ABA/COMMIT-UNKNOWN and Planner restart recovery, (4) audit-before-action + one-shot occurrence integration only after GREEN, (5) Windows/POSIX SQLite TOCTOU handle/path policy and privacy-safe Personal Context.
- **Frozen refs independently read:** `main` `7a843f17eb96ed13d66f23b58b06406b3002e405`; PR #5 `805b377697472268db02650a89c7a94b1c5337c8`; paused Draft PR #9 `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`. All left unchanged, unmerged. Frozen V1/V2/Local UI/Launcher contracts/evidence untouched. ARK/JARVIS/V3 overall **NOT_PASSED**.
