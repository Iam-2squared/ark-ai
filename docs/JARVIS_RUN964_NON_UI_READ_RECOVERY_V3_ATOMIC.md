# ARK AI Run964 — non-UI detached READ recovery, V3 numeric and atomic audit fences

**Scope:** Zero-cost, disconnected/synthetic/local-only. This is **NOT** a JARVIS, training, V3, external tool or model PASS. No physical hardware, GPU, paid API, user credentials, protected evaluation, approval issuance, live tool invocation, Candidate or main merge.

**Work-basis:** `f41e9d94137e2baabc6b8e3c1639b5f5e3fb49c0` (Run963 canonical checkpoint). **PR/branch:** Draft #8 / `research/jarvis-foundations`, isolated from main and paused UI Draft #9. Frozen V1/V2/Local UI/Launcher/Observation-v1 and protected V3 Contract 1 remain unchanged.

## New work — four coherent packages, one optional source guard, 30 regression cases authored

1. **Disconnected READ recovery admission / source** — [`cdd1a0e1`](https://github.com/Iam-2squared/ark-ai/commit/cdd1a0e190e11c181384d56ae2bff4ed81c957ae). Enforce `req_` + 32 hex (36 chars) before request regex; `step_` + 16 hex (21 chars) before step regex; bounded operation (12 chars), state (11 chars), dependencies (21 chars each) before sorting, and success digest (64 chars) before digest regex. Exact valid grammar and denial-only behavior unchanged. This reduces resource-amplification potential at a disconnected recovery ingress; it does not establish trusted provenance, safe real dispatch or authentic restart history.
2. **V3 detached free-only numeric precision regression** — [`ead98988`](https://github.com/Iam-2squared/ark-ai/commit/ead9898822ebb106e53cfb4ae273506b46c05e2b), 15 cases in `tests/test_v3_direct_numeric_precision_run964.py`. Covers non-representable and precision-losing large integers, positive huge float capacity with MiB overflow, wrong types, zero/negative or infinite measurements, wall-budget limits and valid normalized integer/boundary fixtures. The detached reviewer never grants paid compute, training, Candidate promotion or independent provenance.
3. **Atomic audit-before-action corruption quarantine** — [`29449140`](https://github.com/Iam-2squared/ark-ai/commit/294491400c0800bc1edb41235cf908fa836026c6), 5 cases in `tests/test_atomic_audit_two_row_corruption_run964.py`. Valid-width but forged local audit/intent values or a missing first audit row must cause cold-open, inspect and further reserve to refuse without ledger self-repair. A separate intact two-occurrence prefix remains consistently deny-only; SQLite CAS is not an external exactly-once effect.
4. **Disconnected READ recovery input and quarantine regressions** — [`3b17a7de`](https://github.com/Iam-2squared/ark-ai/commit/3b17a7debb57785f6281428eede844c6abe88c96), 10 cases in `tests/test_detached_read_recovery_bounded_ids_run964.py`. Oversized or noncanonical request, step, operation, state, success digest and dependency labels are rejected; a valid RUNNING ancestor remains quarantined while an independent NOT_STARTED READ receives only `READY_MOCK_ONLY` with all authorization/replay flags False.

**Verification caveat:** the 30 cases are *authored*, not an exact-head GREEN claim. No local pytest/Ruff or hardware execution was available in this invocation. Each normal GitHub Contents write automatically triggered existing CI; no duplicate workflow dispatch. Inspect the specific latest job logs if FAIL and repair without weakening gates. Existing Run951 already covered related audit tamper paths; the added audit cases specifically exercise the *first* persisted row and fail-closed refusal of subsequent reservations.

## CI / evidence, sampled during Run964

- Prior canonical `f41e9d94137e2baabc6b8e3c1639b5f5e3fb49c0`: [CI #44265818707](https://github.com/Iam-2squared/ark-ai/actions/runs/44265818707) observed **5/6 GREEN**, Windows 3.13 IN PROGRESS at last observed per-job read. No claim of 6/6 until observed.
- READ source `cdd1a0e1`: [CI #44270218285](https://github.com/Iam-2squared/ark-ai/actions/runs/44270218285), six jobs IN PROGRESS at last sample.
- V3 tests `ead98988`: [CI #44270403367](https://github.com/Iam-2squared/ark-ai/actions/runs/44270403367), six jobs IN PROGRESS at last sample.
- Atomic tests `29449140`: [CI #44270646085](https://github.com/Iam-2squared/ark-ai/actions/runs/44270646085), six jobs IN PROGRESS at last sample.
- READ test `3b17a7de`: [CI #44270786460](https://github.com/Iam-2squared/ark-ai/actions/runs/44270786460), QUEUED at sample. **Exact newest checkpoint HEAD GREEN 6/6 remains pending**; report/checkpoint commits each trigger CI.

## Blockers and next plan

1. Verify six jobs at exact newest HEAD; inspect actual failing job logs before modifying tests or source.
2. Continue Memory WAL/SHM last-close, generation CAS/ABA and event-row coherent snapshots; Planner unknown-COMMIT and restart-safe authority quarantine.
3. After dependent exact-head GREEN, combine immutable ToolRegistry, exact PermissionGate, one-shot occurrence and trusted-clock audit-before-action in *disconnected/mock-only* integration. Never infer real-world exactly-once from local SQLite.
4. Continue privacy-safe Personal Context revocation, Proactive scheduler and Observation back-end provenance, V3 free-only path/resource/reproducibility guards; leave UI paused and PRs #5/#8/#9 Draft/unmerged.

**ARK/JARVIS NOT_PASSED.**
