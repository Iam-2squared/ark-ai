# ARK AI Run969 — Disconnected Planner/Registry identity admission and Run968 CI repair

**Work basis:** Run968 checkpoint `eb73c94218b856d98d4b355708984930141a264a`. **Current code/test HEAD before this report:** `100a268446bc64a10e923a064ca15165ecbfd644`. **Branch:** `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). Work is opt-in local non-UI; JARVIS **NOT_PASSED**.

## Work packages saved in this invocation

1. **Run968 CI repair** — original checkpoint [#44309582973](https://github.com/Iam-2squared/ark-ai/actions/runs/44309582973) was **completed FAILURE 6/6**, all jobs stopped at Ruff I001 for `tests/test_startup_readiness_guard_vectors_run968.py`. A first semantics-preserving import replacement [`1a1f2562`](https://github.com/Iam-2squared/ark-ai/commit/1a1f25621004bf86d81aea9bcf6db5148887c737) did not fix the spacing error: CI [#44317642122](https://github.com/Iam-2squared/ark-ai/actions/runs/44317642122) **FAILURE 6/6**. The exact Ruff diagnostic identified an extra blank line before a top-level constant, not the Python import expression. Normal Contents API edits `dc51f9fc`, `3434a163`, `100a2684` removed only the excess import-to-constant blank line from three test files. No test assertions changed or disappeared. Later CI must verify.
2. **Standalone Planner pre-DAG identity admission** — [source `645b733e`](https://github.com/Iam-2squared/ark-ai/commit/645b733ee2f146999393751025534db7c60b6127) rejects 18 invisible Unicode scalars in optional PlanGraph step IDs, dependencies and tool/capability/scope labels *before* DAG construction, request digest or readiness decisions. [92 authored negative/positive cases `36379435`](https://github.com/Iam-2squared/ark-ai/commit/36379435196b4a71f0cbb025288cbca15963e12c) exercise 18 × five admission positions and ordinary multilingual labels. Frozen `PlanStep`/`ToolCall` constructors and V2/final-eval contract unchanged.
3. **Immutable ToolRegistry registration/binding identity admission** — [source `2e8c8532`](https://github.com/Iam-2squared/ark-ai/commit/2e8c853287f114e570a822299cd7c97963abdb8e) rejects the same 18 scalars in opt-in name, capability, backend ID and exact permission scope, including both `resolve` and `bind`. [91 authored regression cases `005a62e7`](https://github.com/Iam-2squared/ark-ai/commit/005a62e7474d0568f44d59636f7e08a7a66d6ea1) cover all boundaries and permitted Japanese names. Mock backend never executes; no permission grant, consumption or live dispatch.

**183 authored new tests**, **not verified 183 passes**. The new tests plus Run968 test correction are separate from frozen interfaces. No local full pytest, Ruff, device, or independent provenance verification.

## CI progression and limits

- Run968 checkpoint **FAILURE 6/6** at `eb73c942`: [#44309582973](https://github.com/Iam-2squared/ark-ai/actions/runs/44309582973), Ruff I001; no pytest.
- `1a1f2562` **FAILURE 6/6**: [#44317642122](https://github.com/Iam-2squared/ark-ai/actions/runs/44317642122), same import-to-constant spacing issue; no pytest.
- `36379435` **FAILURE 6/6**: [#44317944978](https://github.com/Iam-2squared/ark-ai/actions/runs/44317944978), startup and newly authored Planner test import spacing; no pytest.
- `100a2684` [#44318323464](https://github.com/Iam-2squared/ark-ai/actions/runs/44318323464) **IN PROGRESS (6/6 running at sample)** after spacing corrections; no latest exact-head GREEN. Subsequent report/checkpoint commits can each trigger CI and must be evaluated at their own commit SHA. Do not infer a pass from an earlier commit.
- GitHub repository visibility is **public**, so repository CI uses the public-repository Actions pathway; no manual duplicate workflow or paid external compute was launched.

## Gates preserved and correctness limits

**Frozen V1/V2/Memory v1/Local UI/Launcher/Observation Envelope v1/V3 Contract 1/evaluation, contamination, provenance and reproducibility rules unchanged**. Draft PR #5 protected/unmerged, paused UI Draft PR #9 untouched, main untouched; PR #8 remains Draft. No paid GPU/API/service, Candidate adapter or weight generation/promotion, protected evaluation opening, credentials, user hardware action, real tool effect or main merge. Process-local pins and snapshots do not independently prove consent, authenticated provenance, trusted clock or exactly-once external effects.

## Follow-on priorities

1. Confirm exact latest checkpoint-result HEAD CI across Windows/Ubuntu Python 3.11–3.13; on RED inspect failing job's full traceback, apply smallest semantics-preserving normal Contents fix while working independent lanes.
2. Continue Memory WAL/SHM and CAS/ABA, coherent snapshot and manual-only ambiguous COMMIT reconciliation, preserving frozen Memory v1.
3. Continue Planner terminal/UNKNOWN cold recovery and exact-type registry–permission–durable audit integration only after lower-level exact-head GREEN.
4. Privacy-safe Personal Context, proactive occurrence fences, Observation fixtures/startup readiness and free-only V3 identity/path approvals. UI remains paused.

**ARK/JARVIS NOT_PASSED.**
