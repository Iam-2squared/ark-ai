# ARK AI Run837 — Non-UI WAL last-close isolation and explicit keeper epochs

Reporting basis: `6078227b3f40e25a5d6cbd77abd9174f499af24b` (Run836 checkpoint). Source/test result before this report: `d65bd4124fc114f22e63805abe5f7714e9571348` on `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). Document authored at **2026-11-13T14:51:57.339+09:00 JST** (reporting clock; **not** a trusted action/approval clock).

## Observed issue, precisely bounded

Run836 checkpoint CI [#43368494922](https://github.com/Iam-2squared/ark-ai/actions/runs/43368494922) finished **FAIL**: five of six jobs GREEN, Ubuntu/Python 3.12 FAIL in `tests/test_memory_cross_process_create_race_run435.py`, variant `separate-source`. One worker emitted CREATED, the other failed closed with `MemorySchemaError` describing a transient-looking `-shm` regular-file `st_nlink=0` during independent-process WAL access. This proves an observed refusal, **not** root-cause attribution or safety of retrying. It does not justify accepting a zero-link path or bypassing symlink/hardlink/sidecar safety.

The original test comment claimed that two live `SQLiteMemoryStore` handles kept WAL open. They do not: the store object retains no live SQLite connection between method calls, and child processes can close their last WAL connection during the concurrent CAS test. This mixes a separate last-close lifecycle with revision-zero CAS assertions.

## Five non-UI packages saved by the normal GitHub Contents API

1. **Memory CAS test isolation:** [`39e91b5e`](https://github.com/Iam-2squared/ark-ai/commit/39e91b5eebe58679d12fe9861922f4f7cef3ba19) pins a real parent SQLite WAL read transaction (`BEGIN` + schema read) until both workers exit, so the existing 4 revision-zero CAS modes specifically test competing writes rather than WAL last-close. Closes the keeper in the test cleanup. No production Memory guard or expected CAS result was relaxed.
2. **ActionAudit independent append isolation:** [`43f2d61c`](https://github.com/Iam-2squared/ark-ai/commit/43f2d61c6024327d12342853d1965562fd407c8c) uses an equivalent real parent WAL read epoch around the existing independent audit append workers, preserving unique event IDs and complete digest-only audit assertions. Production audit unchanged.
3. **Memory disposable diagnostic:** [`acaa1efc`](https://github.com/Iam-2squared/ark-ai/commit/acaa1efca627d616bb273c884de398e819f28955) makes opt-in `--wal-keeper` establish an actual read snapshot, rather than only holding an idle connection.
4. **ActionAudit disposable diagnostic:** [`dec61039`](https://github.com/Iam-2squared/ark-ai/commit/dec610392285ce2936dabebd0eaea1fab91922cf) similarly pins a read transaction for the opt-in keeper control.
5. **Personal Context revocation disposable diagnostic:** [`d65bd412`](https://github.com/Iam-2squared/ark-ai/commit/d65bd4124fc114f22e63805abe5f7714e9571348) pins an actual pre-revocation WAL read epoch while the two synthetic revocation workers proceed.

The three diagnostics still expose their original **no-keeper** operation; no anomalous status is silently retried or promoted to success. The keeper is strictly a controlled disposable test condition, not production lifecycle/COMMIT-UNKNOWN recovery, independent attestation, consent, or effect authority. Snapshot values held by the keeper need not reflect later child commits; durable success is checked separately after the keeper closes.

The exact [initial-to-last-source diff](https://github.com/Iam-2squared/ark-ai/compare/6078227b3f40e25a5d6cbd77abd9174f499af24b...d65bd4124fc114f22e63805abe5f7714e9571348) consists of **five modified non-UI files**, two existing process tests and three opt-in diagnostic scripts, five sequential non-force commits. **No new test cases were counted**; existing cases have stronger isolation. No contract, protected branch, UI, or production Memory/Audit/Context implementation was modified.

## Validation and residual limitations

- Local sandbox ran a **separate miniature SQLite WAL protocol control**, 4/4 same-key and 4/4 separate-key repetitions with live reader + independent worker processes. This validates only SQLite control mechanics, **not** repository test results, production safety or physical Windows behavior.
- Run836 pre-checkpoint [#43368332837](https://github.com/Iam-2squared/ark-ai/actions/runs/43368332837) was **GREEN 6/6**, but different HEAD; Run836 final checkpoint [#43368494922](https://github.com/Iam-2squared/ark-ai/actions/runs/43368494922) **FAIL 1/6**.
- Source/test head `39e91b5e`: [#43373725302](https://github.com/Iam-2squared/ark-ai/actions/runs/43373725302); `43f2d61c`: [#43373814955](https://github.com/Iam-2squared/ark-ai/actions/runs/43373814955); `acaa1efc`: [#43373927558](https://github.com/Iam-2squared/ark-ai/actions/runs/43373927558); `dec61039`: [#43373972632](https://github.com/Iam-2squared/ark-ai/actions/runs/43373972632); `d65bd412`: [#43374227595](https://github.com/Iam-2squared/ark-ai/actions/runs/43374227595). These CI runs were **IN PROGRESS/QUEUED at the reviewed snapshot**, not GREEN by inference. Exact post-report/latest-head CI will need separate confirmation; automatic GitHub CI only, no manual duplicate run.
- No full local ARK pytest/Ruff, target Windows hardware, real GGUF or actual tool execution was conducted. The historical `-shm` zero-link root cause is **UNRESOLVED**. No connection keeper should be inferred to solve production path custody, and no guard was weakened.

## Frozen and authorization boundaries unchanged

V1/V2/Local UI/Launcher frozen contracts/evidence intact. [PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) remains Draft/protected/unmerged; [PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) remains Draft/paused/untouched; PR #8 remains Draft/unmerged. No UI/frontend work, paid/potentially billable service, external GPU, API use, Candidate adapter/weights/training, protected final evaluation, promotion, credentials, destructive action, unauthenticated approval, real ToolBackend/notification, automatic ambiguous retry, or main merge. Overall **ARK/JARVIS NOT_PASSED**.

## Next plan / 今後の方針

1. Determine the six exact-head CI outcomes; investigate any new FAIL from logs with minimal non-weakening fixes, and isolate work in unrelated modules while CI runs.
2. Compare bounded disposable keeper/no-keeper WAL lifecycle states across Memory, ActionAudit and revocation; identify last-close zero-link timing without opening, adopting, or auto-retrying unsafe sidecars.
3. Advance Memory COMMIT-UNKNOWN manual reconciliation, coherent CAS/ABA/expiry, Planner terminal/UNKNOWN crash recovery, and registry-bound exact permission + audit-before-action + disconnected mock integration only on independently GREEN lower-level contracts.
4. Continue privacy-safe Personal Context, proactive occurrence, offline observation and free-only V3 guard work; preserve all approval/frozen boundaries.
