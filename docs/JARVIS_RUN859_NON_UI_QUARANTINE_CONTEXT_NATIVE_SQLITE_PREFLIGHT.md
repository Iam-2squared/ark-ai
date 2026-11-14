# ARK AI Run859 — disconnected Quarantine + Personal Context SQLite preaccess hardening

**Work basis:** `c11d1b6a0aee546e29ff64444d85bbee1fdb895f` (Run858 checkpoint).
**Branch:** `research/jarvis-foundations`, Draft [PR #8](https://github.com/Iam-2squared/ark-ai/pull/8).
**Scope:** free-only synthetic fixtures, no UI, real effect, protected evaluation, paid compute or main merge.
**Overall ARK/JARVIS:** NOT_PASSED.

## Package A — proactive expiry-quarantine SQLite admission

- [Source `f2153826`](https://github.com/Iam-2squared/ark-ai/commit/f2153826fa1856e4cdad78334ad4fca8575f0192): the disconnected expiry quarantine ledger rejects NULs, incorrect native pathname encoding, overlong `os.fsencode` paths INCLUDING the longest SQLite `-journal` sibling before `lstat`/SQLite. Import-time OS encoder and exact 4,096-byte limit are pinned. Validation is lexical, not an atomic descriptor/open guarantee.
- [9 new cases `8a35e8ca`](https://github.com/Iam-2squared/ark-ai/commit/8a35e8ca227b3d0f3df93db00bfb63225f34cc30) check both create/read paths: NUL in directory and basename (4), multi-byte overbudget (2), journal-sidecar-only overflow (1), in-process native encoder substitution (1), ordinary cold restart (1).
- **CI failure and real fix:** [CI #43536180671](https://github.com/Iam-2squared/ark-ai/actions/runs/43536180671), Ubuntu Python 3.13 job `132265618024`, reports **3 failing new path tests**. An initial `except ValueError` caught the module's own `ScheduleQuarantineRejected(ValueError)` and converted a correctly detected budget overflow into a generic encoding diagnostic. [Repair `f746df26`](https://github.com/Iam-2squared/ark-ai/commit/f746df26b577f525e1ce76820e94e0889360282d) keeps the encoding `try` separate from the budget rejection. No budget, permission or input check was relaxed.

## Package B — privacy-safe Personal Context replay admission

- [Source `d9d16dc3`](https://github.com/Iam-2squared/ark-ai/commit/d9d16dc317e7d1d393531b0fcdccc4399b1a07d6) rejects exact native malformed/NUL/overlong main and journal-sibling paths before `lstat`; pins the native encoder. Inside the caller's SQLite transaction, a SQL-side schema COUNT/DDL-byte aggregate admits only bounded metadata BEFORE Python hydrates private `sqlite_master.sql`. Existing exact schema comparison, `quick_check`, stored request-id/owner digest preflight and no-disclosure/no-dispatch guarantees remain.
- [10 new cases `5382dfb2`](https://github.com/Iam-2squared/ark-ai/commit/5382dfb2f705c03926311ff1cd34f867905bf20b) cover NUL in directory and filename (4), Unicode bytes over-budget (2), replaced native-encoder callback rejected before invocation (1), excessive DDL and excessive schema object count rejected before SQL hydration (2), and normal read-only restart (1).
- **Preventative symmetry repair `fd6813af`** ([commit](https://github.com/Iam-2squared/ark-ai/commit/fd6813af94371f36fc2859f4a878a7369e064b84)): because `OfflineContextReplayRejected` is also a `ValueError`, separate the intentional byte-budget denial from the encoder exception handler as in Package A. This preserves exact budget diagnostics without ever accessing the filesystem first.

## Validation ledger (exact HEAD only)

- **Initial basis `c11d1b6a0aee546e29ff64444d85bbee1fdb895f`:** [CI #43529875840](https://github.com/Iam-2squared/ark-ai/actions/runs/43529875840), **6/6 GREEN** Windows/Ubuntu × Python 3.11–3.13, verified job conclusions. This is prior code.
- **Package A test HEAD `8a35e8ca`:** [CI #43536180671](https://github.com/Iam-2squared/ark-ai/actions/runs/43536180671), Ubuntu 3.13 **FAIL**, three error-message mismatches in new tests (not evidence of permission bypass). Repaired in later `f746df26`; older FAIL remains.
- **Package A repair `f746df26`:** [CI #43536645904](https://github.com/Iam-2squared/ark-ai/actions/runs/43536645904), **IN PROGRESS** at the initial job inspection.
- **Package B test HEAD `5382dfb2`:** [CI #43536574051](https://github.com/Iam-2squared/ark-ai/actions/runs/43536574051), **IN PROGRESS** at the initial job inspection.
- **Latest repaired source HEAD `fd6813af`:** [CI #43536681865](https://github.com/Iam-2squared/ark-ai/actions/runs/43536681865), **QUEUED/IN PROGRESS** at the initial job inspection. The eventual technical report and canonical status commits will have their own distinct exact HEADs.
- **19 tests AUTHORED, not 19 independently confirmed PASS.** No full local pytest/Ruff, local GPU, physical Windows, target GGUF, independent observer attestation, real tool dispatch or trusted-clock verification. Automatic PR CI only; no manual duplicate rerun.

## Important limitations

Lexical `os.fsencode`/NUL budgets and one-transaction `sqlite_master` size checks do NOT prove symlink-proof atomic descriptor custody between preflight and SQLite open, WAL/SHM last-close coherence, independent provenance, durable exactly-once authorization/effects, or cross-store atomicity. Memory COMMIT-UNKNOWN and Planner recovered RUNNING remain manual/UNKNOWN; no automatic replay. PermissionGate's spent tokens remain process-local. Fixture paths and private Personal Context hashes are not printed in diagnostic outputs. Frozen V1/V2/Local UI/Launcher evidence and contracts are unchanged. Draft PRs #5/#8/#9 remain unmerged; UI PR #9 untouched.

## Next plan / 今後の方針

1. Verify **newest exact HEAD** six-job CI; if any failure, obtain its job log, repair the smallest proven defect and work in an independent lane while CI runs.
2. Add bounded metadata preflights for other persisted synthetic ledgers only where concrete unbounded hydration is demonstrated, without relaxing strict hash or receipt checks.
3. Investigate Memory/ActionAudit WAL/SHM final-close races with disposable held-FD probes; retain UNKNOWN/manual quarantine rather than replay.
4. Advance Memory COMMIT-UNKNOWN causal retained witnesses and Planner UNKNOWN/terminal CAS, then connect ToolRegistry/PermissionGate/durable authorization/preaction audit with disconnected Mock Executor only after dependent exact-head GREEN.
5. Continue privacy lifecycle and V3 free-only identity/approval/reproducibility denial contracts; no protected evaluation, GPU spend, UI or Candidate promotion.
