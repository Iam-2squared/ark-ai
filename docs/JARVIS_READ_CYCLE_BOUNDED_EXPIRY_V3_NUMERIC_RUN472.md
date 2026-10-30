# Run472 — READ-only DAG simulation, bounded Memory expiry and V3 numeric input fences

Work basis: PR #8 `c3724274b9444d170afc719914b5a0156949ce24`; PR #5 `2072549789588939dc958aa0ce51f74edf04da28`.

Exact source/test heads before this technical document: PR #8 `41153b2bf772a8f3ab2434c46b8e21b6637824b8`; PR #5 `b8cd2ca0c8668b52677af2668689569afaca7a8f`.

## 1. Disconnected READ-only DAG cycle

- New `src/ark/agency/disconnected_read_cycle.py` blob `4ee7f7076f564ceab7102c9f8021b61453b67431`. This runs the existing READ registry/gate preflight for each ready wave on an isolated shadow `PlanGraph`, transitions only detached PENDING → RUNNING → SUCCEEDED statuses, and emits content-free digests. It NEVER calls `ToolBackend.execute`, writes durable records, changes the caller's plan, grants real execution permission or authenticates time/consent.
- New `tests/test_disconnected_read_cycle_run472.py` blob `7cebb27ead5a36d36dd77854ae60a55c51529798`: 18 parametrized cases (including full DAG progression, independent waves, missing/expired grants, WRITE rejection, source-plan mutation and forged callbacks). The fixture backend raises if called.
- Simulation completion proves only that a synthetic local PlanGraph can advance under mock READ preflights. It does NOT prove a backend request was executed, completed or authorized. Source and permission evidence is rechecked after callbacks; same-process malicious modification of trusted class internals is not an independently attested security boundary.

## 2. Memory bounded expiry purge

- Extended `SQLiteMemoryStore.purge_expired(*, scope=None, limit=None)` without schema migration or changing the legacy no-limit default; source blob `423211852eee228d95ed2c44e3e1f9a236449767`.
- Optional exact integer `1 <= limit <= 1000` bounds SELECT hydration and the number of deletions/events **per call**, preserving a single `BEGIN IMMEDIATE` transaction, canonical row validation, owner/namespace predicates, revision/expiry-qualified DELETE and one same-transaction `expire` event per deleted row. Batches are ordered by `memory_id`. A caller may explicitly repeat limited calls; no automatic background purge is started.
- New `tests/test_memory_bounded_expiry_purge_run472.py` blob `c3cbb82dc5263f1a5ff2c4ba17135cb6b4e661f9`: 14 cases including repeated batches, deterministic row identity, cross-owner isolation, future expiry, legacy unbounded behavior and invalid limits.
- Deliberate compatibility caveat: **omitting** `limit` still uses the original unbounded scan; this opt-in helper does not silently change existing API semantics or guarantee atomicity across multiple *separate* bounded calls. Other writers may legitimately commit between calls.

## 3. V3 free-only numeric safeguards

- PR #5 `runtime_guard.py` blob `8faae10f6991c2c0757de0f07c47c600316977bd`: checked conversion of huge user-supplied tolerance to float; exact non-bool tolerance type; boolean and oversized monotonic sample rejection; explicit non-finite elapsed checks. No GPU or training was invoked.
- New `tests/v3/test_runtime_guard_numeric_boundary_run472.py` blob `8e8acd10e357e98aa2883e2785921a89ca7893ab`: 22 parametric checks of mocked identity/tolerance and monotonic edge values.
- Exact-head CI **#1520**, run `41010777327`, PR #5 source/test HEAD `b8cd2ca0c8668b52677af2668689569afaca7a8f`: **COMPLETED SUCCESS, 6/6 Ubuntu/Windows Python 3.11–3.13**.
- Earlier V3 intermediate #1518, run `41010647959`, failed two tests: (1) the prior preflight capacity-overflow test correctly required the existing downstream `capacity conversion overflow` error, not an earlier measured-identity rejection; (2) the new test incorrectly regarded finite `1e308` tolerance as non-finite. The smallest fix restored the preflight's established error boundary and corrected that test's input expectations. The earlier intermediate failures remain historical FAIL; only the final #1520 is exact-head GREEN. The soft wall-time checks are not a hard watchdog and do not impose any cloud/provider billing cap.

## CI/evidence status at document preparation

- PR #8 source/test #1522, run `41010963942`, exact HEAD `41153b2bf772a8f3ab2434c46b8e21b6637824b8`: **IN PROGRESS** at the prior inspection; do not inherit older CI GREEN until this exact run succeeds. Earlier checkpoint #1514, run `41005198026`, is confirmed **6/6 GREEN** for prior HEAD `c3724274b9444d170afc719914b5a0156949ce24`.
- The six new/modified implementation and test files were independently fetched on their named branches and their blob SHA values match the above. Local entire-repository `pytest`/`ruff` is **NOT RUN** because the isolated container cannot resolve github.com for clone; source-level independent test evidence is from GitHub Actions only.
- New test cases authored this invocation: **54** (READ 18, Memory 14, V3 22), not interchangeable with claims of local test PASS.

## Safety and follow-on gates

PR #5 and PR #8 remain Draft/open/unmerged. No frozen V1/V2/Local UI/Launcher evidence, Memory v1 DDL, protected V2 evaluation, Candidate approval or model identities were changed. No paid/external compute, real GPU, candidate weights, dataset download, credentials, personal data, real camera/microphone/OS/Tool dispatch, destructive mutation or main merge. Mock approvals and source-level digests are not authenticated user consent or reliable external action evidence.

Next: verify exact PR #8 CI #1522; on a real failure inspect actual job logs and minimally correct the affected path while working separate lanes. Consider a bounded proactive purge *driver* only with independent trusted clock and privacy retention authorization; do not loop automatically without an explicit gate. Continue planner READ-stage-to-durable-journal recovery mock integration only after its lower-level exact-head checks are GREEN; avoid inferring WRITE exactly-once from shadow simulation. V3 stays free-only and approval-blocked.
