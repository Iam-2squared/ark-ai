# ARK AI Run860 — disconnected SQLite ancestry, WRITE path admission and Planner UNKNOWN regression

Work-basis HEAD: `bb0929bac5fd55b43db3d7f2ed670dda896c0c1d` (Run859 checkpoint, [CI #43537180572](https://github.com/Iam-2squared/ark-ai/actions/runs/43537180572) **GREEN 6/6**, checked at start). Last executable/source/test HEAD before this report: `ae0c9bd858967aab776713d182fa2d5b323c0d1d`. Only opt-in disconnected/fixture code and tests changed; **no UI and no real action dispatch**.

## Packages committed on Draft PR #8

1. **POSIX SQLite held-descriptor ancestry (source `445ea30f9c151dc79eb0fca11028fb0cd79b5fa7`, tests `ae0c9bd858967aab776713d182fa2d5b323c0d1d`):** `src/ark/disconnected_sqlite_sidecar_custody.py` now rechecks the complete named directory ancestry *after* its final named main/sidecar `stat` pass **and** final still-open-FD `fstat` pass. Previously a parent rename/retarget after the original directory check could leave the old held FDs valid while a new named path selected a different source. A final recheck refuses that observed drift. Four new POSIX-only tests simulate renames during main/sidecar named `stat` and during final held-FD metadata inspection. Only disposable files; the transient rename is restored for positive control.
2. **Disconnected WRITE slot native SQLite path budget (source `c056b1497356a065bdad21b889155db1953defb7`):** `src/ark/agency/disconnected_write_slot_ledger.py` rejects path NUL and oversized native filesystem-encoded bytes, including the `-journal` sibling, before any `lstat`/SQLite open. `os.fsencode`, module identity and the 4096-byte limit are pinned to their original values for local fault-injection refusal. Existing reservation/CAS/UNKNOWN and schema/provenance gates remain unchanged.
3. **Planner post-COMMIT-UNKNOWN isolation (test commit `c6c0946702858dcaaea8e285d1024e1493ab4cdd`):** Two new synthetic test cases lose the callback response *after* durable `root_a RUNNING` COMMIT, allow independent `root_b` to complete `SUCCEEDED` or `FAILED`, then cold-recover. `root_a` remains ambiguous, `child_a` remains unavailable, and the same stale revision cannot restart `root_a`. This exercises independent branch progress without granting replay or treating an exception as rollback.
4. **Atomic preaction native SQLite path budget (source `f4506501bc4cdbcdd8a879a544eb66d2ef8e330e`, shared tests `3331b4dbbf267e344460a3aa73fa494cd6a3879d`):** `src/ark/agency/disconnected_atomic_preaction_ledger.py` refuses NUL, missing basename and native-byte-overlong raw/absolute journal paths before filesystem inspection. Local `os.fsencode` identity is pinned. Fourteen shared tests cover `WRITE Slot` and `Atomic Preaction` create/reopen, NUL/multibyte/journal-boundary rejection before `lstat`, and positive non-authorizing fixture reopening.

**20 regression cases AUTHORED** (4 + 2 + 14). This is not a PASS claim; no full local Ruff/pytest, physical Windows/GGUF or authenticated live side-effect tests ran. Source changes were committed before their independent tests; automatic CI is the only hosted execution initiated through normal GitHub writes. No duplicate manual reruns.

## CI exact-HEAD evidence at report preparation

- Basis `bb0929ba`: [#43537180572](https://github.com/Iam-2squared/ark-ai/actions/runs/43537180572), **GREEN 6/6** Windows/Ubuntu × Python 3.11–3.13. It does **not** validate the new work.
- SQLite sidecar source `445ea30f`: [#43542131044](https://github.com/Iam-2squared/ark-ai/actions/runs/43542131044), **IN PROGRESS** at observation.
- WRITE slot source `c056b149`: [#43542266805](https://github.com/Iam-2squared/ark-ai/actions/runs/43542266805), **IN PROGRESS** at observation.
- Planner UNKNOWN test `c6c09467`: [#43542357741](https://github.com/Iam-2squared/ark-ai/actions/runs/43542357741), **IN PROGRESS** at observation.
- Atomic preaction source `f4506501`: [#43542415269](https://github.com/Iam-2squared/ark-ai/actions/runs/43542415269), **IN PROGRESS** at observation.
- WRITE/Audit shared test `3331b4db`: [#43542532774](https://github.com/Iam-2squared/ark-ai/actions/runs/43542532774), **QUEUED** at observation.
- Latest source/test HEAD `ae0c9bd8`: [#43542592130](https://github.com/Iam-2squared/ark-ai/actions/runs/43542592130), **QUEUED** at observation.

This report and later checkpoint commits can trigger additional automatic CI. Final-source and checkpoint-result **all-six GREEN NOT YET VERIFIED**. Never transfer an older commit's GREEN to another HEAD.

## Safety and limits

- POSIX held-file checks cannot pin a name after the last inspection, make SQLite's later pathname open atomic with preflight, prove rollback resistance, identify an independent source owner, or close concurrent WAL/SHM last-close races. An untrusted writer with directory control can still race later reopens.
- A 4096-byte `os.fsencode` check only bounds fixture admission; it cannot prove native per-component limits, filesystem permissions, authenticity, atomic multi-store transactions or tamper-resistant execution.
- Planner `RUNNING` after a crash stays UNKNOWN/manual-only, even if other independent steps become terminal. A local SQLite receipt cannot prove an external effect, caller authorship, or permission to retry.
- PermissionGate one-shot tokens remain process-local. The disconnected WRITE and atomic ledgers are reservations, not trusted-issuer approval, authenticated consent, a trusted clock, independently retained witnesses, exact-once external effects, or permission to call ToolBackend.
- Frozen V1/V2/Local UI/Launcher contracts and evidence unchanged. PR #5 and UI PR #9 untouched, open/Draft/unmerged; PR #8 remains Draft/unmerged. UI development paused. No paid service, API, GPU, Candidate generation/weights/training/promotion, protected V2 final evaluation, new secrets/accounts, irreversible operation, physical-PC action, real backend dispatch or main merge.

## Next plan / 今後の方針

1. Check exact latest HEAD CI across all six jobs and apply minimal semantics-preserving fixes for any failing job, switching to independent lanes while builds run.
2. Further investigate Memory/ActionAudit last-close WAL/SHM and descriptor open-to-use races with disposable held-FD/unknown-commit fixtures; do not relax alias rejection.
3. Strengthen retained Memory COMMIT-UNKNOWN causal witnesses and Planner durable terminal/UNKNOWN CAS; independent progress must not become replay permission.
4. Continue privacy-safe Personal Context revocation/recovery, proactive scheduler and observation backend-only fixture contracts.
5. Integrate immutable ToolRegistry, exact-type PermissionGate, durable occurrence reservation, preaction audit and disconnected Mock Executor only after exact-HEAD GREEN dependencies, without authorizing live WRITE, trusted approval, or real dispatch. Preserve free-only V3 guards and protected evaluation gates.
