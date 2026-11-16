# ARK AI Run920 — WAL silent-read denial, privacy claim budgets, startup identity boundary

**Basis:** `b57d971e2efc2370542efa1da2709aa62676ad60` on Draft PR #8 (`research/jarvis-foundations`). **Source + regression-test HEAD:** `afadf164880c6375296ea6428a43f0d87cf2e19e`. **ARK/JARVIS: NOT_PASSED.** Only free/local, inert non-UI work; no new UI/Frontend.

## Package A — fail closed on silent WAL cold-restart data mismatch

- Source `466ccde05c8a23ff6df331747c6f639c0b2b1809`: `scripts/diagnose_ark_store_wal_last_close.py` no longer returns `status=OK` when reopened Memory/ActionAudit/revocation read silently disagrees with retained synthetic evidence. It returns `COLD_READ_MISMATCH` and `phase=cold_restart_read` without exporting SQLite values or file paths. Existing `main()` returns nonzero on a mismatch. This avoids falsely classifying a completed-but-wrong recovery as success. It does **not** grant retry/repair authority.
- Tests `90b8fc35dac59bffa92977212c927fbf93b9f233`: six combinations (3 disposable stores × with/without keeper) inject a silent cold-read mismatch after a real fixture write, and one CLI test verifies nonzero return and no success authority. **Seven cases authored; latest-head GREEN not yet certified.**
- Independent local disposable SQLite subprocess sanity exercise (not ARK store): 8 iterations each of keeper/no-keeper, with an opened `-shm` FD. For both modes, final client close unlinked `-shm`; with a keeper, it remained linked after child exit until keeper close. This **does not resolve** ARK's intermittent WAL/SHM process/sidecar alias race or validate Windows.

## Package B — bounded privacy-erasure claim admission

- Source `452d1cec4c34d2e4770184b5aa798238fcc713f7`: `privacy_erasure_evidence_review.py` checks the exact 64-character digest width and caps vocabulary labels (32 characters) **before** regexp matching or set membership, preventing resource-heavy scans/hashes on forged large exact-string carriers. Existing accepted labels and all forensic-erasure denials remain unchanged. No file reads or cleanup.
- Tests `b72b33135231f6d00d072da18b118ba4d0d02dc0`: six oversized inputs, six string-subclass hash/equality traps, and one positive, explicitly non-authorizing synthetic claim. **Thirteen cases authored; exact-head GREEN pending.**

## Package C — disconnected startup readiness NUL identity fence

- Source `19f17eaf4702f08b840a074d8c105efe953e89ed`: `startup_readiness_review._identifier` rejects a NUL separator for component ID, dependency, failure code or schema revision, after exact type/character length validation and before UTF-8 encoding or graph retention. No frozen schema, real startup, ToolBackend or dispatch changes.
- Tests `afadf164880c6375296ea6428a43f0d87cf2e19e`: four NUL denial cases, four foreign-string callback denial cases, and a valid detached readiness DAG. **Nine cases authored; newest HEAD CI pending.**

**Total:** three independent non-UI source/test packages, **29 new parameterized regression cases authored** (7+13+9). All source writes used the standard GitHub Contents API, reading exact branch HEAD before each write, with no force push or raw Git workaround. No direct local ARK pytest suite was run.

## Read-only dependency review

`disconnected_write_recovery_fence.py` classifies a pending reserved WRITE step with unresolved parents as `QUARANTINE_RESERVED_WRITE` before checking inherited `HOLD_TERMINAL`/ `HOLD_UNCERTAIN`. Existing `test_mixed_recovery_topology_matrix_run609.py` explicitly expects that priority. Both decisions withhold execution; this is a **review item**, not proof of unsafe dispatch. Do not change the precedent without contract/test reconciliation; no write occurred in that lane.

## CI and evidence boundaries

- Baseline Run919 checkpoint `b57d971e2efc2370542efa1da2709aa62676ad60`, CI [#43872251702](https://github.com/Iam-2squared/ark-ai/actions/runs/43872251702): **GREEN 6/6**, Windows/Ubuntu × Python 3.11–3.13, observed this invocation, **baseline only**.
- First source `466ccde0`: [#43889443438](https://github.com/Iam-2squared/ark-ai/actions/runs/43889443438), IN PROGRESS at mid-run read.
- WAL test HEAD `90b8fc35`: [#43889625224](https://github.com/Iam-2squared/ark-ai/actions/runs/43889625224), IN PROGRESS at mid-run read.
- Privacy source `452d1cec`: [#43889866948](https://github.com/Iam-2squared/ark-ai/actions/runs/43889866948), IN PROGRESS at mid-run read.
- Privacy test `b72b3313`: [#43889982078](https://github.com/Iam-2squared/ark-ai/actions/runs/43889982078), IN PROGRESS at mid-run read.
- Startup source `19f17eaf`: [#43890439311](https://github.com/Iam-2squared/ark-ai/actions/runs/43890439311), QUEUED at mid-run read.
- Startup test `afadf164`: [#43890527650](https://github.com/Iam-2squared/ark-ai/actions/runs/43890527650), QUEUED at mid-run read.
- **Do not count any prior GREEN as proof on the latest source/test/report/checkpoint commit.** No manual duplicate runs.

## Frozen contracts and hard blockers

**Unchanged:** V1/V2/Local UI/Launcher frozen evidence, protected V2 final evaluation, V3 Draft PR #5 gates, UI Draft PR #9 paused/unmerged, main, ARK Memory persisted v1 schema, existing planner/audit/recovery acceptance boundaries. PR #5/#8/#9 remain Draft/unmerged. No paid/external GPU/API/compute, real Candidate/weights/training/promotion, trusted human review, credential/account onboarding, protected final eval, physical PC, actual backend WRITE, automatic UNKNOWN retry, irreversible action, or main merge.

**Still blocked/unknown:** latest CI 6/6 GREEN; real cross-process WAL/SHM alias/last-close race; externally trustworthy clock/audit custody and restart-safe once-only authorization; cross-store atomic Memory/Planner/occurrence proof; real V3 model/weight identity and target-PC offline GGUF gate.

## Next plan / 今後の方針

1. Resolve exact latest HEAD six-job CI and any test regressions via normal semantics-preserving Contents writes; avoid duplicate workflows and overlap independent lanes.
2. Reproduce the ARK-specific cold-read/sidecar path race with a disposable two-process test matrix, recording pre/post close phases, never auto-retrying an UNKNOWN effect.
3. Strengthen Memory high-water/CAS and Planner COMMIT-UNKNOWN durability; only then connect immutable registry, exact PermissionGate, durable occurrence, audited pre-action custody and disconnected mock executor.
4. Maintain privacy-safe Personal Context, proactive/observation contracts, and free-only V3 guards. Preserve frozen gates, no UI development, all three PRs Draft/unmerged.
