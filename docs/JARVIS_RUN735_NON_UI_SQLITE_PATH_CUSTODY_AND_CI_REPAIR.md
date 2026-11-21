# Run735 — Non-UI SQLite path-custody across Memory and disconnected authorization evidence

**Scope:** Draft PR #8 `research/jarvis-foundations` only. No UI development, no protected V2 final evaluation, V3 Candidate, real sensor/tool dispatch, external/paid compute, approval, main merge or irreversible recovery. **ARK/JARVIS/V3 remain NOT_PASSED.**

## Exact starting state and CI defect

- **Actual initial work-basis HEAD:** `414e1f3afd82500bf5476b76776fb43aa3852e63` (Run734 technical report; status still Run733 at initial read).
- Frozen main `7a843f17eb96ed13d66f23b58b06406b3002e405`; Draft [PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) `805b377697472268db02650a89c7a94b1c5337c8`; paused Draft [PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`, all left unchanged/unmerged.
- Run733 checkpoint `4f3ab54a7cedec9e2e7ae3dc20cf0072fee52420` was verified **6/6 GREEN** on [CI #42585499234](https://github.com/Iam-2squared/ark-ai/actions/runs/42585499234), but this **does not transfer to Run734/Run735**.
- Run734 report-head [CI #42591929775](https://github.com/Iam-2squared/ark-ai/actions/runs/42591929775) **6/6 FAIL** at Ruff B904; actual Ubuntu job log pointed to `src/ark/agency/audit.py:247`, an exception raised inside `except FileNotFoundError`.
- **Package A / semantics-preserving CI fix:** [`a0c649b9`](https://github.com/Iam-2squared/ark-ai/commit/a0c649b9a7f64332b8039de25e6b001447fa28d1) adds `from None` to the existing fail-closed missing-ancestor denial, without opening any path or weakening the rejection. The follow-up workflow [#42594479491](https://github.com/Iam-2squared/ark-ai/actions/runs/42594479491) was **IN PROGRESS on the recorded review**; no GREEN claim.

## Package B — Memory SQLite custody, create/write/ro

- [Source](https://github.com/Iam-2squared/ark-ai/commit/ac5ef2377b95338f1e57a170e071aca9e611e88d) adds `_require_safe_memory_path` before directory bootstrap, after bootstrap, and ahead of *every* writable and read-only DB open. It refuses non-exact paths/callback-bearing pathlikes, lexical parent traversal, symbolic/nondirectory ancestor, symbolic/nonregular leaf, multiple hardlinks, and vanished databases on normal reopen.
- Existing valid relative and nested local Memory paths remain supported; explicit initialization still owns initial creation, normal operations remain `mode=rw`/read-only and cannot recreate an erased DB. No schema, MemoryRecord, CAS or frozen contract changed.
- [New test file](https://github.com/Iam-2squared/ark-ai/blob/7aea40b0ebe72f28f8e4dee0957cbae5022089fa/tests/test_memory_sqlite_path_custody_run735.py): **12 parameter-expanded cases** with positive create/read/write, symlink parent/leaf, late alias read/write, hardlink, missing source, nonregular paths, `..` and hostile `__fspath__`. Synthetic fixture text only. [Test commit `7aea40b`](https://github.com/Iam-2squared/ark-ai/commit/7aea40b0ebe72f28f8e4dee0957cbae5022089fa); CI [#42594880471](https://github.com/Iam-2squared/ark-ai/actions/runs/42594880471) **IN PROGRESS on recorded review**.

## Package C — disconnected registry-bound occurrence ledger

- [Source `6f04fdb`](https://github.com/Iam-2squared/ark-ai/commit/6f04fdbfadd9a92779a9d2c93d39a6e1eba0dd8e) adds original local path checks to synthetic occurrence store startup/each read/write open, and separately to its read-only count path before resolving a potentially redirected source.
- [New test file `fd4b628`](https://github.com/Iam-2squared/ark-ai/commit/fd4b628046ab7fe80e1489d0d6d726c57ebac678) covers **11 cases**: clean restart/count, valid relative path, ancestor and leaf symbolic redirects, hardlinks, late rename, deleted file, traversal, nonregular parents/leaves, hostile pathlike. [CI #42595129439](https://github.com/Iam-2squared/ark-ai/actions/runs/42595129439) **QUEUED on recorded review**. No fixture token authorization changed; this cannot prove real exactly-once external effects.

## Package D — synthetic occurrence-to-audit link custody

- [Source `649d633`](https://github.com/Iam-2squared/ark-ai/commit/649d633178803ea9b690a152f309546c61bbfbcc) gates the independent synthetic audit-link SQLite file on first creation and each future read/write open, plus applies the occurrence source path preflight before the link review opens the separate reservation ledger directly.
- [New test file `f373951`](https://github.com/Iam-2squared/ark-ai/commit/f3739512f4b70981c97f04f121af68d470031488) covers **11 parameter-expanded synthetic cases** for valid restart, late and initial symlink, hardlink, missing file, path traversal, nonregular targets and hostile pathlike. [CI #42595407375](https://github.com/Iam-2squared/ark-ai/actions/runs/42595407375) **QUEUED on recorded review**. No actual ToolBackend invoked, no audit event or external side effect fabricated.

## Evidence boundaries and open limitations

- Total **34 newly authored parameter-expanded regression cases** across three new test files; **3 separate non-UI production modules hardened**, plus **1 lint-only repair**. At report creation none of the final new cases is attested **6/6 GREEN** by a matching completed CI.
- Every GitHub write used the normal Contents API, preceded by a fresh PR HEAD read. No protected branch merges, force-push, object-level bypass or destructive disk changes. Test-local renamed/linked files are synthetic temporary fixtures only.
- These checks use process-local `lstat`, not atomic descriptor-relative `dirfd` custody; a filesystem owner could change the path between preflight and SQLite open. SQLite `-wal`/`-shm` sidecar custody, independent evidence provenance, trusted clock, actual consent/approval, and crash-safe cross-store atomicity are **not proven**. Hardlink/symlink tests skip where OS support is unavailable.
- V1/V2/Local UI/Launcher frozen contracts/evidence, PR #5 protected training gate and paused UI PR #9 remain untouched.

## Next plan / 今後の方針

1. Obtain completed **exact final HEAD** CI Windows/Ubuntu Python 3.11–3.13. On failure, inspect real job logs and perform the narrowest safe correction; do not reuse earlier GREEN.
2. Design separately verifiable descriptor-relative/no-follow SQLite path opening where supported, with explicit Windows behavior, without claiming this `lstat` preflight as complete provenance.
3. Continue Memory CAS/ABA and manual-only COMMIT-UNKNOWN triage; Planner retained READ manifest and journal restart semantics; trusted-clock audit-before-action and one-shot authorization only through **disconnected/mock** executor while real execution remains blocked.
4. Continue privacy-safe Personal Context/proactive/observation contracts and free-only V3 guards, preserving all frozen evidence and approval gates.

## Actual inherited CI failures and narrow compatibility repair (after initial report)

- [Memory-source/test CI #42594880471](https://github.com/Iam-2squared/ark-ai/actions/runs/42594880471) Ubuntu Python 3.11 was **15 FAIL / 11,672 PASS / 1 SKIP**. All 15 failures were existing removed/moved Memory SQLite fixtures asserting `sqlite3.OperationalError`; the new pre-open missing-file check had instead raised `MemorySchemaError`. They still refused to open/recreate a database; this was a public exception-class regression, **not permission to skip a guard**.
- [Occurrence-source/test CI #42595129439](https://github.com/Iam-2squared/ark-ai/actions/runs/42595129439) Ubuntu Python 3.11 was **18 FAIL / 11,680 PASS / 1 SKIP**: the same 15 Memory cases and 3 existing missing synthetic occurrence ledgers expecting `sqlite3.OperationalError`.
- Normal, non-bypassing fixes restore the **same earlier missing-file exception class** while retaining every path alias and pre-I/O refusal: Memory [`2c44eeb`](https://github.com/Iam-2squared/ark-ai/commit/2c44eeb22df4dcca4a78ac6cc2657bbeba3f3622), its new test [`df46584`](https://github.com/Iam-2squared/ark-ai/commit/df465849481fce57dd3fcdb16655d1a3c9c0c5fc); occurrence [`3aa0884`](https://github.com/Iam-2squared/ark-ai/commit/3aa08842d7748a25c31bcd9e075f8ae022302aab), its new test [`dea3ae7`](https://github.com/Iam-2squared/ark-ai/commit/dea3ae726f89e899ef033b4be408aa79bf5fe4d0).
- The established [audit-link fixtures](https://github.com/Iam-2squared/ark-ai/blob/a294057741d8479da88d78edd4ed9da909a99b5c/tests/test_synthetic_occurrence_audit_link_run374.py) likewise assert `sqlite3.OperationalError` when a link sidecar disappears. Preserve this exact existing contract with [`613240b`](https://github.com/Iam-2squared/ark-ai/commit/613240b4a1cb2e1a718ce4ab3a5f6af2f896dac3) and new-test correction [`a294057`](https://github.com/Iam-2squared/ark-ai/commit/a294057741d8479da88d78edd4ed9da909a99b5c). No fallback creation, symlink acceptance, writable action or replay added.
- At this addendum's preparation, these newer repair heads have **no matching verified six-platform GREEN**. Other existing and new tests remain subject to remote CI; the first relevant job logs, not unexecuted tests, drove changes.
