# ARK AI Run952 — Non-UI durable ABA, atomic stale writers, abrupt-exit recovery

This report covers four **synthetic, disconnected, zero-new-cost** regression packages on Draft PR #8. It is not a JARVIS PASS, real-world exactly-once proof, approval, trusted clock, physical device test, or Candidate evaluation. Neither V1/V2/Local UI/Launcher freezes nor V3 protected gates were changed.

## Work basis / exact repository artifacts

- Previous Run951 checkpoint HEAD: `dc5ba5b128014fe0d0d67eea24c110380f4ab82c`. Its [GitHub Actions run #44173718717](https://github.com/Iam-2squared/ark-ai/actions/runs/44173718717) completed **6/6 GREEN**, Windows/Ubuntu on Python 3.11–3.13, verified before this work.
- `220e6bed0d51eaab208e3db9a1ddd782baead7cc`: [Memory ABA restart](https://github.com/Iam-2squared/ark-ai/blob/220e6bed0d51eaab208e3db9a1ddd782baead7cc/tests/test_memory_generation_aba_restart_run952.py), **4** parameterized cases. Create → delete → recreate of the *same deterministic ID*, including same-content image and unrelated-owner append, must never validate an old generation CAS token. An explicitly reobserved generation may advance only its local row.
- `687612ef47c3ac24c2cdc3d1a605c759319d258b`: [Atomic two-handle CAS](https://github.com/Iam-2squared/ark-ai/blob/687612ef47c3ac24c2cdc3d1a605c759319d258b/tests/test_atomic_two_handle_cas_occurrence_run952.py), **3** cases. An already-open independent ledger handle attempts stale or duplicate occurrence claims; no additional SQLite intent/audit row may be committed on failure. A fresh current prefix is still deny-only.
- `f4d6af815750b0c44546d78ca0850f2886c2aa1e`: [Abrupt-exit atomic intent](https://github.com/Iam-2squared/ark-ai/blob/f4d6af815750b0c44546d78ca0850f2886c2aa1e/tests/test_atomic_postcommit_abrupt_exit_run952.py), **3** cases. A detached Python child reserves one to three synthetic intent/audit pairs and terminates via `os._exit(29)` immediately after the last durable return; the parent checks cold SQLite rows, stale-witness denial and duplicate-occurrence denial. A reconstructed digest read from the **same DB** is explicitly NOT independent evidence or replay authorization.
- `a7217f05591a467473612eb35bb0a90a14c3dce3`: [Abrupt-exit Planner RUNNING](https://github.com/Iam-2squared/ark-ai/blob/a7217f05591a467473612eb35bb0a90a14c3dce3/tests/test_planner_postcommit_running_abrupt_exit_run952.py), **2** cases. A detached child appends RUNNING and terminates via `os._exit(31)`. Cold recovery from a separately retained pre-commit genesis witnesses the RUNNING step as ambiguous, preserves independent PENDING state and must deny stale revision retry and both dispatch/replay flags.

**Total: 12 newly authored tests in four separately saved packages.** No production-source changes or UI/frontend edits. Tests use only disposable local SQLite and subprocesses. No full local pytest or owner-PC GGUF run was performed; **latest-head CI green is unconfirmed** at initial report writing.

## CI pipelining / evidence distinctions

- Prior Run951 exact checkpoint HEAD `dc5ba5b1`: [#44173718717](https://github.com/Iam-2squared/ark-ai/actions/runs/44173718717) **COMPLETED GREEN 6/6**.
- Memory source/test HEAD `220e6bed`: [#44183541636](https://github.com/Iam-2squared/ark-ai/actions/runs/44183541636), **IN PROGRESS** at last sample.
- Atomic two-handle HEAD `687612ef`: [#44183654459](https://github.com/Iam-2squared/ark-ai/actions/runs/44183654459), **IN PROGRESS** at last sample.
- Atomic abrupt-exit HEAD `f4d6af81`: [#44183828150](https://github.com/Iam-2squared/ark-ai/actions/runs/44183828150), **IN PROGRESS** at last sample.
- Planner abrupt-exit HEAD `a7217f05`: [#44183907642](https://github.com/Iam-2squared/ark-ai/actions/runs/44183907642), **IN PROGRESS / QUEUED jobs** at last sample.

Only the previous checkpoint has verified GREEN. Every new test result must be attributed to its own exact GitHub HEAD. Do not treat authored tests, SHA strings, synthetic clock fields, recovered data or scheduled workflow launch as green evidence, trusted provenance, custody, human review or authorized action.

## Dependency / architecture assessment

- **Memory:** The generation-CAS optional path is distinct from frozen Memory v1. An ABA after `delete`/recreate cannot use a row revision (again 1) as its only lifetime guard; the create-event identity and retained event prefix must remain coherent. This test does not prove independent append-only storage or immunity to a coordinated full-database rewrite.
- **Atomic:** A stored audit-before-action entry is only a local reservation with a hash chain; it does **not** authenticate consent or ensure an external tool's exactly-once effect. Two handles and a postcommit process exit model important crash windows, without reexecuting a tool.
- **Planner:** A durable RUNNING step seen after process loss is COMMIT-UNKNOWN/ambiguous. Neither an intact local journal nor a valid historical prefix may authorize replay. The test never calls a real backend.
- **Independent lane audit:** The existing `src/ark/v3_detached_packet_review.py`, `src/ark/v3_detached_preflight_crossbind.py`, and `src/ark/personal_context_revocation_continuity_review.py` were inspected read-only for free-only and privacy boundaries. No protected evaluation was opened, no Candidate created and no frozen contract changed. Personal Context retains a separate SQLite veto store; it is **not** a transactional cross-store authorization barrier.

## Next plan / 今後の方針

1. Confirm exact-head Windows/Ubuntu Python 3.11–3.13 CI 6/6 for the new Planner/Atomic/Memory tests; inspect actual logs and narrowly repair any FAIL through standard GitHub Contents only.
2. Improve Memory CAS/ABA/WAL-SHM coherent snapshot diagnostics and event/expiry integrity, keeping frozen schema and regular APIs unchanged.
3. Advance Planner COMMIT-UNKNOWN + immutable ToolRegistry/PermissionGate + single-use durable authorization + trusted-clock audit-before-action as an **inert, reversible integration** only after lower-layer exact-head GREEN. No real dispatch.
4. Extend privacy revocation, proactive occurrence, Observation fixture and free V3 gate checks on separate modules, with UI paused and all PRs Draft/unmerged.

**Overall ARK/JARVIS: NOT_PASSED.** Approval/payment/credentials/physical-PC actions and all other controlling gates remain blockers, not implicit permissions.
