# ARK AI Run806 — Disconnected occurrence frontier, strict V3 recursion and observation ingress

**Prepared:** 2026-11-12T10:56:09.729+09:00 (observed JST wall clock, not an authenticated runtime clock).  
**Branch/PR:** `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8).  
**Initial work basis:** `229b812cae70b35e24d75fe085c43a119f8aa910`, exact-head CI [#43131287447](https://github.com/Iam-2squared/ark-ai/actions/runs/43131287447) **six of six GREEN** (Windows/Ubuntu × Python 3.11–3.13). This prior CI does **not** validate Run806 changes.

## Package 1 — Coherent, read-only synthetic occurrence frontier

- `src/ark/agency/disconnected_occurrence_frontier_review.py`, source commit `029554326f2c852d9b547f3b448e9c5e2c191d75`. New opt-in function `review_synthetic_occurrence_frontier` checks the existing exact synthetic occurrence schema and all bounded rows in **one SQLite read transaction**, ordered by token digest. It creates a stable domain-separated SHA-256 commitment to the complete row set and reports only count, digest and maximum local reservation timestamp. No token digest or private ToolCall identity leaves the result.
- `tests/test_disconnected_occurrence_frontier_run806.py`, test commit `1f995fdb7e921dababddcc6ec6843745e87038be`; Ruff import-only repair commit `4fa1057471500b8332a5c0b1fd0cb7f0ee84f9cc`. New tests cover empty and single-row states, canonical order independence, same-count valid-looking rewrite, append/deletion drift, malformed retained carrier, missing source, exact store type, changed result descriptor and changed digest callback.
- Scope: forensic snapshot matching only. The canonical set digest is **NOT an append-prefix proof** or an independently authenticated witness. Equal-count rewrites are detected only when a separately retained earlier digest is supplied. It cannot prove database-owner honesty, a legitimate issuer, human consent, exactly-once real effects or authority to retry a WRITE.

## Package 2 — Bounded V3 JSON recursion denial

- `src/ark/v3_detached_packet_review.py`, source commit `9c44c3a6fdfaf4a5e44d47e28b23b740e4c7549e`, classifies `RecursionError` during JSON parsing or canonical serialization as an explicit `DetachedV3PacketRejected` rather than allowing a raw parser/serializer exception. The existing 4096-byte limit, strict canonical payload, duplicate-key/nonfinite rejection and offline crossbinding remain intact.
- `tests/test_v3_packet_deep_nesting_run806.py`, commit `023b3400a781be24f274ff09e86808335714b648`, covers bounded hostile deep arrays, nested snapshot values, byte budget and exact bytes type. No model, GPU, file weights, Candidate, paid service or protected evaluation is opened.

## Package 3 — Direct ObservationEnvelope NUL ingress

- `src/ark/observations.py`, source commit `d055ec573ded9dcb67d5df5438127098728c2daf`, rejects NUL in directly supplied `source_id`, `adapter_id` and `privacy_scope` before any observation ID hash. This aligns the direct metadata contract with existing fixture-adapter preflight, preventing ambiguous native-boundary labels from bypassing the adapter.
- `tests/test_observation_direct_nul_boundary_run806.py`, commit `8669fa57d6627378e24b5c2f0f45f98956fd9063`, includes parametrized direct-ingress, reflected identity-mutation and cached-window consistency cases. No real media acquisition or disclosure.

## CI and evidence accuracy

- Baseline prior HEAD `229b812cae70b35e24d75fe085c43a119f8aa910` [#43131287447](https://github.com/Iam-2squared/ark-ai/actions/runs/43131287447): six matrix jobs **GREEN**, observed this invocation.
- New test-bearing earlier-head [#43137100712](https://github.com/Iam-2squared/ark-ai/actions/runs/43137100712) and intermediate [#43137357599](https://github.com/Iam-2squared/ark-ai/actions/runs/43137357599): six jobs **FAIL early at Ruff I001** in the new occurrence test. The exact log recommended moving `from ark.agency import disconnected_occurrence_frontier_review` above the submodule import; corrected without changing test assertions at `4fa10574...`. Those historical red runs do not establish a new code failure.
- Latest source/test checkpoint CI must be independently verified; no full-run pytest, local Ruff, exact-head six-job GREEN, real-machine gate, benchmark performance or user permission is claimed here.

## Boundaries and integration plan

All three packages are opt-in and reversible on Draft PR #8. Existing V1/V2/Local UI/Launcher evidence untouched. Draft PR #5 remains protected/unmerged, Draft PR #9 and all new UI/frontend work remain paused and untouched. No paid/external compute or API, real tool execution, actual owner consent, irreversible deletion, Candidate creation/promotion, training, protected final evaluation or main merge. In-process class/function pinning is **not** sandboxing, independent custody or a trusted clock.

Next: verify exact current HEAD, inspect six matrix conclusions and actual failure logs if any; keep the new occurrence frontier isolated until exact-head GREEN. Then prioritize Memory CAS/ABA/COMMIT-UNKNOWN, Planner restart UNKNOWN quarantine and immutable registry-bound PermissionGate/audit/mock integration after respective invariants are GREEN. **ARK/JARVIS remains NOT_PASSED.**
