# ARK AI Run981 — Planner CI compatibility and non-UI policy-vector safety

**Prepared at (Asia/Tokyo/JST): 2026-11-19T10:45:14.341+09:00.** Reporting clock only; NOT an authenticated audit/expiry/consent/scheduler/provenance time.

**Invocation work-basis HEAD:** `d03d1eebd53536429e62e2e466f374ea2377875f` (Run980 checkpoint, Draft PR #8 on `research/jarvis-foundations`). **Latest executable source+test HEAD at report prewrite:** `774d37c18bced2843459e7a90f2b34d5af41c6a7`. **ARK/JARVIS overall NOT_PASSED.** No real tool dispatch or external compute.

## Four coherent non-UI work packages

1. **Planner CI semantics-preserving repair** — [`e1ac5186`](https://github.com/Iam-2squared/ark-ai/commit/e1ac51868ce4cf6741735022577b12ae57cd2f8b). Run980 exact checkpoint [CI #44432224876](https://github.com/Iam-2squared/ark-ai/actions/runs/44432224876) **FAIL 6/6**. Ubuntu Python 3.11: **18,717 PASS, 4 FAIL, 1 SKIP**. All four failures are parameterizations of `test_verifier_rejects_preinstalled_false_getter_before_projection`: the old test expected `changed before replay`, but strengthened pre-replay descriptor custody now rejects earlier with `terminal receipt changed: policy vector`. Updated only the expected diagnostic in the existing test; its assertion that the malicious getter never executes is retained. Production denial, terminal semantics and contracts unchanged. [Repair CI #44438525772](https://github.com/Iam-2squared/ark-ai/actions/runs/44438525772) IN PROGRESS at last observation.
2. **Privacy erasure diagnostics** — [source `2a9213d6`](https://github.com/Iam-2squared/ark-ai/commit/2a9213d670987814f6e9893f66f5dfad2063be5f) + [tests `e374c98c`](https://github.com/Iam-2squared/ark-ai/commit/e374c98c9bcede07da7835df80b678fbb1f91710). Import-pin the complete denial, observation, assessment and class-hook name tuples. Equal-value rebinds, truncation or reordering now fail before accessing untrusted claim fields; a truncated policy cannot conceal a counterfeit False-returning cleanup property or malicious observation getter. **15 authored synthetic cases**. Existing categorical forensic-erasure/cleanup denials unchanged; no actual deletion or file access.
3. **Memory v1 read-only expiry preview** — [source `50030a72`](https://github.com/Iam-2squared/ark-ai/commit/50030a723f603b57914ff9138e42ba6c84487b26) + [tests `8b3ea25e`](https://github.com/Iam-2squared/ark-ai/commit/8b3ea25ed47ec41753118faac52afeda80f7a269). Import-pin all five deny-only receipt property names and complete receipt field/hook vectors; refuse a missing/reordered/rebound vector before private SQLite access on both preview and retained verification. **20 authored disposable local-fixture regression cases.** No schema change, purge, authenticated owner consent or trusted-clock claims.
4. **Disconnected mixed READ/WRITE recovery fence** — [source `a9380e39`](https://github.com/Iam-2squared/ark-ai/commit/a9380e39ddee9e3334fef72c4b7dacc3c3e8648f) + [tests `774d37c1`](https://github.com/Iam-2squared/ark-ai/commit/774d37c18bced2843459e7a90f2b34d5af41c6a7). Import-pin all Step, Disposition, Fence and denied-authority vectors to block shortened zip inspections before reading untrusted synthetic recovery claims. **15 authored cases** including forged replay property, counterfeit claim getter and intact UNKNOWN-WRITE quarantine. No real Planner dispatch/replay or WRITE.

**Total: 50 newly authored parametrized cases plus correction of four existing parametrized assertions.** Only static checks on the changed exact-head files (no >100-column lines) were performed locally; no local full pytest run. These cases are **not yet certified CI PASS**. Each source/test write triggers ordinary CI; no duplicate manual workflow dispatch.

## CI evidence as observed during this invocation

- Run980 checkpoint [#44432224876](https://github.com/Iam-2squared/ark-ai/actions/runs/44432224876): **FAIL 6/6**, four test-diagnostic assertions as above.
- Previous exact source/test [#44431379089](https://github.com/Iam-2squared/ark-ai/actions/runs/44431379089): **GREEN 6/6** on an older startup-readiness commit, not this newer code.
- Repair [#44438525772](https://github.com/Iam-2squared/ark-ai/actions/runs/44438525772) IN PROGRESS; privacy source [#44438676343](https://github.com/Iam-2squared/ark-ai/actions/runs/44438676343) IN PROGRESS and privacy tests [#44438739867](https://github.com/Iam-2squared/ark-ai/actions/runs/44438739867) IN PROGRESS at last observation.
- Memory source [#44438839228](https://github.com/Iam-2squared/ark-ai/actions/runs/44438839228), Memory tests [#44438893901](https://github.com/Iam-2squared/ark-ai/actions/runs/44438893901), recovery source [#44438962550](https://github.com/Iam-2squared/ark-ai/actions/runs/44438962550) and newest source/test HEAD [#44438997464](https://github.com/Iam-2squared/ark-ai/actions/runs/44438997464): **QUEUED** at last observation.
- **Latest exact code/test and future report/checkpoint CI all-six GREEN remains UNVERIFIED.** Branch checks may have concurrent updates after observation. Failures require direct log confirmation before any fix or PASS claim.

## Frozen boundaries and unresolved blockers

main base `7a843f17eb96ed13d66f23b58b06406b3002e405`; PR #5 gated Draft/unmerged `805b377697472268db02650a89c7a94b1c5337c8`; PR #9 paused UI Draft/unmerged `3b49048dd70eebcb6268299b9ecef4e301bbc0fd` at latest inspected refs. V1/V2/Local UI/Launcher evidence, Memory v1, PlanStep/ToolCall v1, Observation Envelope v1 and protected V2/V3 evaluation boundaries preserved. No UI/frontend changes, no main merge, no paid/billable compute, GPU, external API/service, secrets or connections, Candidate/weight generation, training, promotion, protected evaluation opening, actual tool execution, irreversible erasure, or automatic replay. Local policy-vector checks and SQLite self-hashes do not provide independent provenance, a trusted clock, authenticated user approval, or real effect evidence.

## Next plan / 今後の方針

1. Inspect latest exact-head Windows/Ubuntu Python 3.11–3.13 CI jobs and fix red failures via normal contents writes only; overlap independent non-UI review.
2. Memory: WAL/SHM races, coherent expiry/event observations, CAS/ABA, restart-safe unknown-commit no-replay quarantine.
3. Planner persistent terminal recovery + immutable registry/PermissionGate + restart-safe one-use authority + audit-before-action; only disconnected/mock integration after exact-head GREEN.
4. Privacy-safe Personal Context retention/revocation, proactive occurrence/replay fence, observation fixture adapters and V3 free-only authorization/path/identity/reproducibility. **UI remains PAUSED.**

**ARK/JARVIS: NOT_PASSED.**
