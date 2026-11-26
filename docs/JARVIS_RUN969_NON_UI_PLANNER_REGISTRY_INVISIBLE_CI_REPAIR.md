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

## Follow-up after the first Run969 checkpoint — discovered legacy pre/post-commit mismatch

[Exact corrected-test CI #44318323464](https://github.com/Iam-2squared/ark-ai/actions/runs/44318323464), job Ubuntu Python 3.11 `134850262812`, progressed through Ruff and pytest and reported **18,292 PASS, 15 FAIL, 1 SKIP**. The 15 failures were exclusively older proactive/quarantine tests expecting a committed event or a legacy post-commit message after a preinstalled counterfeit receipt authority property. Run968 had deliberately established a stricter **pre-commit fail-closed** barrier: `tests/test_schedule_quarantine_vectors_run968.py` requires **zero** appended events when a receipt/witness authority descriptor changes. The earlier legacy expectations and this new stricter invariant are incompatible.

**Semantics-preserving safety resolution (not weakening any negative gate):**

- [`9d956ae4`](https://github.com/Iam-2squared/ark-ai/commit/9d956ae4435623c570d0fdfc4974ad894f994a2f) and [`91ccef02`](https://github.com/Iam-2squared/ark-ai/commit/91ccef026ddb7746223ede7aa00b099c527e7fa8) retain pre-commit refusal and include precise denial-specific diagnostics without invoking counterfeit getter code, while keeping Run968's generic carrier rejection marker.
- [`b8c9073a`](https://github.com/Iam-2squared/ark-ai/commit/b8c9073aaa56890999ca2806b834ab336f133688) updates six legacy `test_quarantine_original_denial_descriptors_run588.py` negative cases to require **zero** quarantine writes and retained genesis witness (rather than accepting an append before denial).
- [`470fad02`](https://github.com/Iam-2squared/ark-ai/commit/470fad026310c15734a10749aea78256993b38d6) updates nine `test_schedule_quarantine_postcommit_denial_run528.py` negative cases to require **zero** writes. Positive recovery tests remain unchanged.

No assertions were deleted, no precommit guard weakened, no synthetic backend executed. These are tighter no-effect invariants for the opt-in quarantine adapter. Their exact post-fix HEAD CI across all six OS/Python jobs remains **UNVERIFIED** until fresh Actions finish. The first Run969 checkpoint `2f74ddb7` predates this discovered failure and corrective work; update canonical status after this report through normal GitHub Contents and confirm the result HEAD. Protected PRs/main/frozen interfaces remain unchanged.
