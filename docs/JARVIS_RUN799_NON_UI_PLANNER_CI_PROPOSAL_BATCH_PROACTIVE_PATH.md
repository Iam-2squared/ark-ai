# ARK Run799 — Non-UI CI recovery, proposal CAS/batch and proactive SQLite path custody

**Work basis:** Draft PR #8 `research/jarvis-foundations` at `0aae0b199d831c4dbed3c089e9f3881162141fe1` (the Run798 checkpoint head). **Saved report preparation:** 2026-11-12 05:02 JST. **Overall:** ARK/JARVIS NOT_PASSED; this is disconnected, local-only, free work. Frozen V1/V2/Local UI/Launcher evidence and V3 Contract 1 untouched.

## 1. CI failure diagnosis and regression-safe Planner repair

Run798 exact-head workflow [#43083772796](https://github.com/Iam-2squared/ark-ai/actions/runs/43083772796) completed with **six failed jobs**, not GREEN. The inspected Ubuntu job `130742760654` completed **9 failed, 13,523 passed, 1 skipped**. All 9 failures were legacy WRITE restart fault-injection expectations: `tests/test_write_restart_final_denial_run524.py` and `tests/test_write_restart_final_callback_custody_run541.py` expected precise post-getter failure diagnostics, but the newly introduced early denial-descriptor pin rejected with `WRITE restart report constructor changed` before those prior callbacks ran.

- Source `src/ark/agency/disconnected_write_restart_binding.py` fixed by normal GitHub Contents API at `a22179ec9bceb475dc39f561af42b513784be27e`. All original field/hook/constructor guards remain early, and the six false-only denial descriptors are now **also checked after** final callback and final independent SQLite review. Original post-getter report/ledger/state drift checks remain intact; UNKNOWN WRITE remains quarantined.
- `tests/test_write_restart_original_denials_run798.py` expectation update at `fe9aa0e1e7a7dd23abc8d2d394460285efd2bfda` preserves both malicious `False` and `True` cases, expecting a terminal descriptor denial or acquired-authority rejection. Existing Run524/Run541 tests were **not modified**. This preserves their ability to detect last-getter mutation and ledger drift.
- CI [#43090923490](https://github.com/Iam-2squared/ark-ai/actions/runs/43090923490) verified **Ubuntu 3/3 GREEN** at subsequent inspection; Windows jobs were still in progress. Do not infer this validates later source packages or the checkpoint HEAD.

**Boundary:** The import-original false-only getter check no longer runs before SQLite inspection. The final deny checks and previously tested reentrant guards are retained. This remains process-local mutation detection only, not authenticated permission or proof of an external WRITE result.

## 2. Concurrent proposal global-CAS proof

`tests/test_disconnected_proposal_concurrent_cas_run799.py` was created at `a9023e5355db41b450f2b38fa86c64b3af585b12`: **six parameterized test cases** covering two, three and four concurrent SQLite writer connections, both same proposal and competing proposal identities, all presenting the same initially retained global witness. Expected result is exactly one new event/one winner; other contenders are denied and no snapshot grants execution, human review or Candidate promotion.

The first CI [#43091266118](https://github.com/Iam-2squared/ark-ai/actions/runs/43091266118) failed Ruff `I001` on an extra blank after imports; formatting-only fix committed `803ee7a8158a72dee1e13544a4175b28b68de39a`. Test concurrency behavior was not altered.

## 3. Coherent read-only multi-proposal snapshot

New `src/ark/agency/disconnected_proposal_snapshot_bundle.py` committed `763989cd589c82f472a889a2e45d8a603845fb34`. It inspects up to 32 exact, distinct proposal identifiers in **one read-only SQLite transaction** with the existing store's full schema/event-prefix checks. The output contains ordered tips and one shared global witness; no separate read-per-ID race is presented as coherent. Import-original store/lifecycle dependencies, result descriptors and false-only capability flags are checked. Existing store schema and append/CAS behavior unchanged.

New `tests/test_disconnected_proposal_batch_snapshot_run799.py` committed `1f57a99d84ec89e66ddfd6c02c7238cf8ef26db3`: **13 parameterized tests** for ordering, shared snapshot and prefix, rollback denial, duplicate/type/overbudget IDs, swapped denial properties and substituted SQLite scan. Intermediate CIs [#43091639374](https://github.com/Iam-2squared/ark-ai/actions/runs/43091639374), [#43091760300](https://github.com/Iam-2squared/ark-ai/actions/runs/43091760300) failed Ruff `I001` from the new tests. Import-block whitespace only was fixed at `803ee7a8158a72dee1e13544a4175b28b68de39a` and `dfa55c2829ff4bba7e3286f1332bebb6fa73c016` (the two test files). The corrected head's CI is [#43091923275](https://github.com/Iam-2squared/ark-ai/actions/runs/43091923275); confirm individual jobs before claiming GREEN.

**Boundary:** The observed witness is local SHA chain, not independent tamper-proof provenance. Batch result cannot authenticate approvals, run training or execute a tool.

## 4. Independent proactive path custody

`src/ark/proactive_synthetic_review.py` hardened in `668768d79a6c27229b73f028c07cf694019d3e43` with **read-only lstat preflight** at initialization, before the synthetic prepare write and read-only count, and after relevant SQLite open/read-write phases. It refuses known symbolic-link ancestors, linked or nonregular main SQLite files, suspicious linked/nonregular `-wal/-shm/-journal` and orphan sidecars on initial creation. It does not delete any file, invoke a real notification or claim atomic race resistance; a missing main file still lets the existing sqlite3 read/write error route reject without recreating.

`tests/test_proactive_sqlite_alias_preaccess_run799.py` committed `db9896899dcb816dd0b2989aeae0f11ee01fae94`: **12 regression cases** for main-path symlink (initialization/count/prepare), hardlink, sidecar symlink (three types), orphan regular sidecars (three types), symlink ancestor and normal inert fixture. Tests skip platform-unsupported symlink/hardlink creation; Windows/Linux exact HEAD CI still required. Source CI [#43092540731](https://github.com/Iam-2squared/ark-ai/actions/runs/43092540731), test CI [#43092597442](https://github.com/Iam-2squared/ark-ai/actions/runs/43092597442) were IN PROGRESS/QUEUED at report preparation.

**Boundary:** `lstat` before/after use does **not** eliminate time-of-check/time-of-use replacement races. No trusted clock, human consent, real process isolation or external file protection is claimed.

## Validation / strict gates

- Last **previous completed baseline** verified for Run797: [#43071826276](https://github.com/Iam-2squared/ark-ai/actions/runs/43071826276), Ubuntu/Windows × 3 Python versions **GREEN 6/6**. Not evidence for Run798/Run799.
- Original Run798 head [#43083772796](https://github.com/Iam-2squared/ark-ai/actions/runs/43083772796) **FAIL 6/6** (9 old test expectation conflicts).
- Subsequent fix [#43090923490](https://github.com/Iam-2squared/ark-ai/actions/runs/43090923490) **Ubuntu 3/3 GREEN**, Windows pending at initial read; later commits under distinct CI.
- Six new proposal concurrency, 13 proposal batch, 12 proactive aliases = **31 newly submitted test cases**. Four substantial work packages including Planner CI repair; **not certified all-six exact-head GREEN until the final run completes**. No duplicate CI rerun launched.
- Latest technical status and job evidence are in `docs/PROJECT_STATUS.md`; its eventual commit HEAD must be obtained from GitHub after writing, not guessed.

Frozen V1/V2/Local UI/Launcher/V3 Contract 1 and protected evaluation remain unchanged. PR #5 stays Draft/unmerged; PR #9 remains Draft/unmerged and **untouched** with ALL UI DEVELOPMENT PAUSED. No paid API/external GPU/compute/service, new credential/account, real model or real ToolBackend, automatic unknown WRITE replay, Candidate generation/promotion, protected evaluation opening or main merge.

## Next plan / 今後の方針

1. Verify latest exact-head six CI jobs. Repair failures only using concrete job logs and normal GitHub Contents API; preserve existing test oracles.
2. Advance Memory CAS/ABA, privacy retention, expiry and coherent recovery, and Planner terminal/WRITE restart integrity without opening real execution.
3. Integrate isolated ToolRegistry, PermissionGate, durable audit-before-action and mock executor only after separately validated exact-head GREEN gates.
4. Deepen proposal snapshot retained lineage and independent read-only rollback review; keep all proposal state descriptive, never authenticated approval.
5. Strengthen privacy-safe Personal Context and observation/proactive non-UI fixtures; keep V3 free-only guards and all UI work paused.
