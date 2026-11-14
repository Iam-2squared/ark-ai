# ARK — Run807 non-UI core: frozen Observation compatibility, occurrence frontier custody and Planner quarantine

**Prepared (observed wall-clock JST): 2026-11-12T11:50:50+09:00.**
**Work basis:** `47d96c48109c49ae4f39b8a1833a22b2df91d433` (Run806 checkpoint).
**Working branch:** `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), OPEN/DRAFT/UNMERGED.
**Result status:** three independent non-UI work packages written via the normal GitHub Contents API; latest exact-head six-matrix CI GREEN is **NOT VERIFIED**, ARK/JARVIS **NOT_PASSED**.

## 1. CI-driven frozen Observation v1 compatibility correction

[Run806 checkpoint CI #43138334908](https://github.com/Iam-2squared/ark-ai/actions/runs/43138334908) completed **6/6 FAIL**, despite Ruff passing. Inspected Ubuntu 3.11 job `130918968920`, Ubuntu 3.12 job `130918968859` and Windows 3.11 job `130918968718`: **9 pytest failures** from `tests/test_observation_direct_nul_identity_run768.py` (3) and `tests/test_observation_fixture_nul_framing_run745.py` (6). The new Run806 direct `ObservationEnvelope.__post_init__` NUL denial contradicted frozen v1 historical identity, which deliberately permits NUL in inert direct envelopes while strict disconnected fixture adapters and chain reviewers **must reject** NUL.

- `src/ark/observations.py`: removed **only the newly introduced Run806 direct-constructor NUL rejection**, preserving exact carrier identity, digest, type, Unicode and length guards. Commit `638dbc737edcaffc8f412f2964286da338eef97f`.
- `tests/test_observation_direct_nul_boundary_run806.py`: replaced contradictory assertions with v1 deterministic JSON NUL identity, strict adapter denial and cached window mutation review; corrected NUL-only comparison against a valid nonempty alternate label. Final test-update commit `e76d4808d5c28cfa8fe76d3fd561d2b648e1906a`, earlier `2fae015e5fa9ed13964122c9622addd52df97c44`. The revised file has **20 parameterized/test cases** (9 direct identity, 6 adapter rejection, 1 ordinary identity, 3 reflective identity, 1 window mutation). Older frozen test files remain unchanged.
- This is **restoration of the frozen v1 interface**, not relaxation of fixture ingress, privacy review, permission or provenance gates.

## 2. Occurrence snapshot protocol custody

`src/ark/agency/disconnected_occurrence_frontier_review.py` now pins the original domain separator, regex descriptor, source store type, and `hashlib`/`json`/`sqlite3` module references before any retained witness or local SQLite row is read. Existing original callback, budget, timestamp and result-denial fences remain. Commit `33fb8663fe1f16cafb7d7dd832ccc16c61ae8bfa`.

New `tests/test_disconnected_occurrence_frontier_custody_run807.py` submits **6 regression cases** for same-shaped protocol substitutions, using an intentionally absent database and asserting rejection **before SQLite creation/read**; final test-correction commit `9ff4d3f7bd455faea15831157b321594c231e44b` (distinct regex-flag identity to avoid Python `re.compile` cache); earlier `a1cb418d148eaba4863285ccbf4436ad3695d3e6`, initial `f4dd7ded20ae6845f54f94e20596972e5288abe5`. This snapshot remains a bounded, synthetic, **read-only** local digest; it cannot authenticate independent custody, authorize dispatch, establish exactly-once physical effects, or warrant automatic retry.

## 3. Planner WRITE quarantine matrix independent regression

New `tests/test_write_quarantine_matrix_terminal_run807.py` at `fab5d225cd9d7b45ea01abc32231593a247991cb` submits **22 regression cases** against the existing isolated `synthetic_write_quarantine_matrix_review` contract: 15 state × reservation combinations, 3 cross-store orphan cases, 3 invalid Planner state cases, 1 stable deny-only digest case. All expected decisions are diagnostic and deny-only; no executor, audit storage mutation or actual ToolRegistry WRITE path is enabled. The production quarantine module and pre-existing tests were not modified.

**Test accounting:** 28 new cases across two new files (6 + 22); the pre-existing Run806 test file is corrected and now contains 20 cases instead of 14 (net +6). No exact-head local pytest/Ruff or full repository checkout has been performed; tests are **SUBMITTED**, not declared PASS.

## CI timeline / evidence truth

- Previous Run806 checkpoint `47d96c48109c49ae4f39b8a1833a22b2df91d433`: [#43138334908](https://github.com/Iam-2squared/ark-ai/actions/runs/43138334908) **6/6 FAIL** with 9 known NUL interface regressions; concrete job logs inspected.
- Corrected compatibility intermediate HEAD `e76d4808d5c28cfa8fe76d3fd561d2b648e1906a`: [#43143681137](https://github.com/Iam-2squared/ark-ai/actions/runs/43143681137) **IN PROGRESS** at last inspection, not evidence for later changes.
- Occurrence test final HEAD `a1cb418d148eaba4863285ccbf4436ad3695d3e6`: [#43143972306](https://github.com/Iam-2squared/ark-ai/actions/runs/43143972306) **QUEUED** at last inspection.
- Planner test HEAD `fab5d225cd9d7b45ea01abc32231593a247991cb`: [#43144143388](https://github.com/Iam-2squared/ark-ai/actions/runs/43144143388) **QUEUED** at last inspection. The later documentation/checkpoint commits have distinct HEADs and potentially new CI runs. Do **not** transfer older-head GREEN to them.

## Fixed constraints and limitations

PR #5 stays Draft/unmerged, protected V3 Contract 1 and V2 frozen final evaluation unopened. PR #9 and all UI/frontend development remain paused, Draft/unmerged and untouched. Frozen V1/V2/Local UI/Launcher contract/evidence files are unmodified. No paid/external GPU, paid APIs, subscription, new credentials, account connections, Candidate/weights, Candidate promotion, physical PC/real-model action, real ToolBackend WRITE, irreversible erasure, external dispatch, automatic replay, or main merge. No hashes or human permissions inferred from model output.

## Next plan / 今後の方針

1. Verify the actual checkpoint-result HEAD and latest six GitHub Actions matrix conclusions; diagnose concrete logs before modifying any failed path, and never trigger duplicate equivalent workflows.
2. After exact-head GREEN, advance Memory CAS/ABA/expiry, COMMIT-UNKNOWN recovery quarantine, Planner exact recovery/terminal propagation and immutable registry-bound PermissionGate, using disconnected/mock-only execution and read-only witnesses.
3. Continue proactive restart readiness, privacy-safe Personal Context, observation fixture adapters and zero-cost V3 preflight. Keep frozen evidence, PR #5 gate and PR #9/UI pause unchanged. **ARK/JARVIS NOT_PASSED.**
