# ARK AI Run861 — offline Planner and privacy restart evidence, CI repair

## Scope and basis

- Repository: `Iam-2squared/ark-ai`
- Branch: `research/jarvis-foundations` / Draft PR #8; no merge
- Work basis: `a8ce0c41296c7a9dedb6be706058080198a377a8` (Run860 checkpoint)
- New source/test commits before this report: `f959c9546ac778b89cdeafbffc52546525fca212`, `cd1ef451f22ede6055b96500edcd000a0fb79754`, `989449f79f22d745580502509663caa638a308bd`, `86ba6a8ce657bf8b83366947eb5cf5a18244166f`
- This is **test/diagnostic work**, not a gate PASS or evidence of any externally executed action.

## NEW — three independent, reversible packages

### 1. Cross-platform CI source repair, not relaxed checks

Run860 latest checkpoint [CI #43542920093](https://github.com/Iam-2squared/ark-ai/actions/runs/43542920093) failed all six Linux/Windows matrix jobs at Ruff **I001 + E501** in `tests/test_disconnected_sidecar_final_ancestry_run860.py`; Python tests never started. The first repair `f959c954` corrected line length but mistakenly removed the required Ruff separator between third-party `pytest` and first-party `ark`. [CI #43548082827](https://github.com/Iam-2squared/ark-ai/actions/runs/43548082827) still failed all six matrix jobs at I001, independent of application semantics. `989449f7` restores the exact blank-line grouping. Production custody code and all fail-closed assertions are unchanged.

### 2. Planner, spawned independent interpreters

`tests/test_planner_spawned_unknown_isolation_run861.py` (commit `cd1ef451`) adds **two cases** that instantiate fresh SQLite handles in spawned child processes (Windows/Linux compatible):

1. Child commits `root_a: RUNNING` and exits without transferring a result receipt; parent restarts from its independently held genesis tail. Recovery must retain `root_a` as ambiguous, deny replay and dependent `child_a` dispatch, yet allow an independent `root_b` local transition to SUCCEEDED. A second cold restart must replay the same complete journal and still report the ambiguity.
2. Two spawned interpreters attempt exactly the same synthetic `root_a: RUNNING` transition from an identical retained tail. Only one local CAS/journal append may commit; the other is stale. Cold recovery must show one durable event and no execution permission.

A committed SQLite event is not a ToolBackend effect. Neither a matching state nor a child-process exit code proves issuer identity, trusted approval, audit-before-action, or exactly-once external execution. These tests cannot authorize a retry.

### 3. Personal Context, cold-restart retention/revocation

`tests/test_personal_context_cold_restart_retention_run861.py` (commit `86ba6a8c`) adds **three cases** using only disposable private fixtures and fresh Memory/revocation SQLite handles:

1. A previous retention inventory at synthetic time 100 is rechecked at time 151. The expiry boundary is classified without exposing private content or granting erasure/disclosure/use.
2. A revocation written after cached capture must invalidate reuse of that cached inventory after restart; exception text must not disclose private content or owner.
3. An independently committed Memory revision change after capture must invalidate the earlier inventory after restart; no private content is echoed.

Synthetic timestamps are **not trusted wall-clock evidence**. No deletion, publication, real context acquisition, user consent or backup erasure is performed or inferred.

## CI and evidence, not PASS claims

- Last verified previous source+test matrix GREEN: commit `3331b4dbbf267e344460a3aa73fa494cd6a3879d`, [CI #43542532774](https://github.com/Iam-2squared/ark-ai/actions/runs/43542532774), **6/6 GREEN**. This does not certify later heads.
- Run860 latest checkpoint `a8ce0c41`, CI `43542920093`: **6/6 FAIL (Ruff)**.
- First repair `f959c954`, CI `43548082827`: **6/6 FAIL (remaining Ruff I001)**.
- Spawned Planner test commit `cd1ef451`, CI `43548286189`: **FAIL**, prior to the final lint fix; do not attribute it to the new Planner tests.
- Corrected lint commit `989449f7`, [CI #43548347401](https://github.com/Iam-2squared/ark-ai/actions/runs/43548347401): **IN PROGRESS** when inspected; final outcome unverified.
- Latest test commit `86ba6a8c`, [CI #43548446858](https://github.com/Iam-2squared/ark-ai/actions/runs/43548446858): **IN PROGRESS** when inspected; final outcome unverified.
- **Five new test cases authored; PASS of these cases not yet verified.** No local full pytest/Ruff run, no physical Windows/GGUF gate, no duplicate workflow launch. GitHub CI invocation should remain automatic and no external paid compute was requested.

## Frozen boundaries and next dependent gates

V1/V2/Local UI/Launcher frozen evidence/contracts unchanged. PR #5 and PR #9 remain Draft/unmerged; PR #9 and all new UI/frontend work remain paused. No Candidate work, paid services, external GPU, protected evaluation, physical-PC actions, real backend, secret/account connection, automatic promotion or main merge.

`NOT_PASSED` remains the only overall JARVIS completion label. A local CAS proves only one SQLite journal winner, not exactly-once external side effects. WAL/SHM final close and open-to-use custody races remain unresolved. Memory COMMIT-UNKNOWN and recovered Planner RUNNING remain manual/UNKNOWN only. Policy one-shot grant state remains process-local; independent issuer attestation, trusted-clock audit-before-action and reliable restart-safe external execution are NOT_PASSED.

### Next plan / 今後の方針

1. Inspect the exact final-head six-job CI; repair any failing implementation/test with the smallest fail-closed patch. Do not equate earlier GREEN with latest-head GREEN.
2. Verify new spawned and privacy cases on all supported OS/Python combinations, then review any cross-process timing or data-budget mismatches without relaxing invariants.
3. Advance independent Memory/ActionAudit WAL/SHM terminal-close races with disposable abrupt-exit fixtures, and retained Memory causal/COMMIT-UNKNOWN witnesses.
4. Extend Planner durable UNKNOWN/terminal CAS and Personal Context retention/revocation on isolated non-UI paths.
5. Only after lower-level exact-head GREEN: connect immutable ToolRegistry, PermissionGate, durable occurrence/audit-before-action and disconnected Mock Executor, preserving fail-closed boundaries and all authorization gates.
