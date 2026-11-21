# ARK AI — Run931: non-UI CI repair, late proactive policy custody, occurrence replay

**Scope:** zero-cost, disconnected non-UI core work on Draft PR #8 (`research/jarvis-foundations`). **Actual work-basis:** `2f39c00886861db4bf1a9d737eb351812f8a7452` (Run930 checkpoint). Frozen V1/V2/Local UI/Launcher and protected evaluation boundaries remain unchanged. This report is evidence about synthetic code and CI, never human consent, authorized tool execution, real Candidate/GGUF training or a PASS claim.

## Package 1 — Repair proven Run930 CI mismatch without weakening rejection

- Baseline [CI #43983558945](https://github.com/Iam-2squared/ark-ai/actions/runs/43983558945), SHA `2f39c008`, **completed FAILURE on all six Windows/Ubuntu × 3.11–3.13 jobs**.
- Both inspected Ubuntu 3.12 and Windows 3.11 logs report **six failures** in `tests/test_memory_sql_text_type_preflight_run930.py`; SQL preflight correctly raised `MemorySchemaError("stored memory row exceeds MemoryWrite bounds")`, but the test's `pytest.raises(match="hydration")` rejected that diagnostic. No observed failure was the corruption being accepted.
- [Commit `42fd6c88`](https://github.com/Iam-2squared/ark-ai/commit/42fd6c889e76fc46affa2cfab054b0c5667322c7): update **one assertion shared by six parameterizations** to match the established SQL-side early admission diagnostic. Source and fail-closed behavior are unchanged. This does **not** remove the test of malformed BLOB storage, no implicit repair, or event nonmutation.
- Repair [CI #43990297887](https://github.com/Iam-2squared/ark-ai/actions/runs/43990297887) at report inspection: **Ubuntu Python 3.11/3.12/3.13 all GREEN, Windows 3 jobs IN PROGRESS**. No all-six success claim at this point.

## Package 2 — Reentrant identity policy must remain import-original after every callback

- [Source `e237f08b`](https://github.com/Iam-2squared/ark-ai/commit/e237f08b597ebe989354e6c1d7528c529698fb77) reasserts `_require_original_policy_contract()` inside the per-phase `assert_epoch()` of `review_prepared_trigger_freshness`, before each subsequent policy getter or `identity()` lookup. Initial admission alone cannot establish that a *later* retained witness, SQLite schema, row digest, or continuity callback did not replace `SyntheticTriggerPolicy.identity`.
- [Tests `1191be96`](https://github.com/Iam-2squared/ark-ai/commit/1191be96bbb413a5b5d1f64e7728b586f493a46d) add **four parameterized, disposable fixture cases**: callback-time identity replacement in retained integrity, schema validation, row hashing, and history continuity. Each asserts fail-closed before injected replacement code executes. This is local in-process callback custody, not cryptographic provenance or proactive notification permission.
- [Source CI #43990937678](https://github.com/Iam-2squared/ark-ai/actions/runs/43990937678) and [test CI #43991221039](https://github.com/Iam-2squared/ark-ai/actions/runs/43991221039) were **IN PROGRESS** at report inspection. Four newly authored tests are not claimed GREEN until their exact SHA is verified.

## Package 3 — Restart-safe synthetic occurrence uniqueness across registry revisions

- [Tests `f79e2a38`](https://github.com/Iam-2squared/ark-ai/commit/f79e2a3833caacb22cfa0fb9219548a2250c9730) add **two parameterized SQLite fixture cases** for a changed registered backend ID (therefore a changed registry revision/bound-action identity): (a) same token with a different occurrence ID, (b) different token with the same occurrence ID. Both must reject against the previously reserved global one-shot ledger after re-instantiating the local store, and must never call the inert backend.
- This verifies only synthetic uniqueness under this fixture's single local SQLite ledger. It cannot authenticate token issuer, consent, external effects, trusted time, or an exactly-once WRITE action.
- [CI #43991448602](https://github.com/Iam-2squared/ark-ai/actions/runs/43991448602), exact source/test SHA `f79e2a38`, was **IN PROGRESS** at report inspection; 6/6 PASS not yet verified.

## Independent free-only V3 read review

Read-only inspection of `src/ark/v3_detached_preflight_crossbind.py` and `src/ark/v3_detached_packet_review.py` confirms these are explicitly detached, synthetic checks with **False** approval/paid-compute/promotion properties; no Candidate runtime, GPU, protected final evaluation, external provider or training was invoked or modified. This is a scope/contract review, not a security proof or a protected V3 gate opening.

## Evidence limits and next work

- **6 NEW parametrized test cases authored (4 proactive + 2 occurrence)**, plus six existing Memory cases repaired by one test expectation change. No full local pytest, local GGUF run, live user private data, external tool execution, credentials, paid compute or provider invocation.
- **Latest source/test SHA `f79e2a38...` remains pending full CI closure.** CI from earlier SHAs cannot validate newer edits. Do not label unfinished CI GREEN or JARVIS PASSED.
- Known unresolved: SQLite WAL/SHM cross-process/alias races; Memory CAS/expiry authenticated evidence; Planner COMMIT-UNKNOWN requires manual disposition; durable registry-bound consent, signed/token provenance, trusted-clock audit-before-action and actual exactly-once effects; physical Windows/GGUF gates.
- **Next:** inspect exact latest six-job CI and smallest semantics-preserving repair on any genuine FAIL; concurrently continue safe independent Memory/Planner/privacy/recovery work; keep candidate/paid and frozen approval gates CLOSED, UI paused, PR #5/#8/#9 Draft/unmerged and main unchanged.

**No frontend/UI files, main, frozen specs, protected evaluation, or PR #5/#9 branches changed.**
