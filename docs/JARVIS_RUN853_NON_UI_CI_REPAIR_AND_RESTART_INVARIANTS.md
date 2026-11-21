# Run853 — CI fail-closed reconciliation and disconnected restart invariants

**Scope:** `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), non-UI/disconnected only. Initial work-basis HEAD `631cf28b0acfbb28cc32b6054e4758345d1baafb` (Run852 final source/test HEAD); repair source+test HEAD `c6079392e76a40da3f69a5d5c248bb53dfb3ea48`. **ARK/JARVIS NOT_PASSED.** No frozen V1/V2/Local UI/Launcher files, PR #5 or UI PR #9 changed.

## Grounded failure triage

Run852's corrected [CI #43478278440](https://github.com/Iam-2squared/ark-ai/actions/runs/43478278440), exact HEAD `631cf28b`, completed **FAIL 6/6**. Ubuntu 3.12 job `132067815415`: 11 failed, 15,175 passed, 1 skipped; Windows 3.12 job `132067815738`: 9 failed, 15,088 passed, 90 skipped. Failures were not a single pytest fixture-name problem: source guards added in Run852 rejected tests that monkeypatched the **shared** `sqlite3.connect` before the intended injected callback could run, alongside two erroneous `Path.exists()` assertions on >4096-character paths. The guard correctly rejected a changed connector; the tests incorrectly assumed interception was permitted. Do not weaken the guard to accommodate test interception.

## NEW: coherent repair packages

1. **Atomic UNKNOWN review API and preflight denial:** `src/ark/agency/disconnected_atomic_unknown_outcome_review.py` now maps the lower-level pinned-connector `AtomicPreactionRejected` to the review API's own `AtomicUnknownOutcomeRejected` with an explicit cause. `tests/test_atomic_unknown_ledger_epoch_run820.py` validates zero invocation of a substituted connector and no late mutation; a retained genesis witness is constructed **before** the hostile monkeypatch. `tests/test_atomic_unknown_outcome_protocol_run816.py` similarly captures the witness before module substitution, preserving an actual reviewer-boundary test. This is early rejection, not a demonstrated late-hook recovery.
2. **Proactive due and WRITE-slot restart:** `tests/test_due_restart_read_only_run490.py` and `tests/test_write_slot_restart_readonly_run490.py` no longer patch the shared connector to spy on SQL (which the custody contract now prohibits). Instead they assert unchanged SQLite data dumps on reopen, actual read success while another SQLite connection holds a RESERVED write transaction, and explicit early rejection of substituted connectors with zero callback invocation. These observations do **not** independently prove every SQL statement or race-free pathname custody.
3. **WRITE slot unauthorized post-COMMIT wrapper injection:** `tests/test_disconnected_write_slot_ledger_run465.py` now verifies that an attempted substituted `sqlite3.connect`/commit wrapper cannot alter the claim/receipt or insert a reservation at all; after restoring the connector, normal synthetic reservation remains non-authorizing. Historical post-COMMIT injection by a globally patched connector is no longer reachable at the strict preflight boundary. This does **not** establish independently authenticated COMMIT-UNKNOWN recovery, external effect status or exactly-once dispatch.
4. **Long pathname negative-test reliability:** `tests/test_atomic_preaction_sqlite_ingress_run852.py` no longer invokes `Path.exists()` on a too-long component (which itself raises OS `ENAMETOOLONG`); it checks the disposable fixture directory remains empty. Production long-path admission remains unchanged.

These are primarily regression-test repairs plus the reviewer exception-translation fix. Do not count modified cases as new passing cases, and do not claim latest-head GREEN before all six conclusions are observed.

## CI / evidence

- [Old failing run #43478278440](https://github.com/Iam-2squared/ark-ai/actions/runs/43478278440) **FAIL 6/6** at `631cf28b`.
- [#43486065812](https://github.com/Iam-2squared/ark-ai/actions/runs/43486065812) at `38096220` and [#43486126122](https://github.com/Iam-2squared/ark-ai/actions/runs/43486126122) at `59788d98`: **IN PROGRESS** at last observation.
- [#43486258382](https://github.com/Iam-2squared/ark-ai/actions/runs/43486258382) at `a11f4551`: **IN PROGRESS**. [#43486301287](https://github.com/Iam-2squared/ark-ai/actions/runs/43486301287) at `56630957`, [#43486383243](https://github.com/Iam-2squared/ark-ai/actions/runs/43486383243) at `45d6c407`, [#43486469035](https://github.com/Iam-2squared/ark-ai/actions/runs/43486469035) at `2a77e31e`, and [#43486566990](https://github.com/Iam-2squared/ark-ai/actions/runs/43486566990) at `81e2f0aa`: **QUEUED** at last observation. Latest repair HEAD `c6079392` CI may not yet be visible. These runs cannot prove the latest HEAD. No rerun was manually launched.
- No local full Ruff/pytest, real GGUF or physical-PC verification executed. **Exact latest all-six CI = NOT CONFIRMED**.

## Remaining gates / prioritized Next plan / 今後の方針

1. Verify exact latest HEAD's full Windows/Ubuntu × Python 3.11–3.13 CI; fix any remaining failure using normal Contents API and only after checking the current branch+PR HEAD.
2. Keep SQLite connector pins. Investigate disposable Memory/ActionAudit WAL/SHM last-close unlinked held-descriptor and aliasing races without weakening no-follow/single-link rules.
3. Resume coherent Memory row/event/highwater and manual COMMIT-UNKNOWN work, Planner persistent UNKNOWN/terminal quarantine, then (after exact-head GREEN) immutable ToolRegistry/exact-type PermissionGate/audit-before-action/disconnected Mock integration.
4. Review independent privacy-safe Personal Context, observation, proactive scheduler and free-only V3 identity/approval/reproducibility lanes.

**Unchanged hard boundaries:** no UI/frontend development, main merge, PR #5 merge, protected V2 final evaluation, Candidate generation/promotion, paid compute/API/service, real credentials, cameras/microphones, external effects, real tool execution or fabricated human approval. `PermissionGate` token consumption is still process-local; restart-safe exactly-once authorization and execution **NOT_PASSED**. A committed local digest alone never authorizes external action.
