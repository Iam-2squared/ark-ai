# ARK AI — Run737 / 2026-11-09 JST — NON-UI SQLite CI repair, detached epoch/file codec custody

**Work status:** isolated free-only Draft PR #8 groundwork; ARK/JARVIS/V3 **NOT_PASSED**. This report records authored changes, *not* a final-head six-matrix PASS, human review, trusted clock, or real-PC proof.

**Administrative observation:** 2026-11-09 20:44:20 Asia/Tokyo/JST (not trusted target clock). **Before report write HEAD:** `cc845e2d0ebc9e3eefdc92dcb38f6d475cee7534`.

## Work packages (normal GitHub Contents API, reversible)

1. **Inherited CI log diagnosis and narrow POSIX test correction** — In exact prior Run736 checkpoint CI [#42604941917](https://github.com/Iam-2squared/ark-ai/actions/runs/42604941917), **Ubuntu Python 3.11/3.12/3.13 FAIL**, **Windows 3.11/3.12/3.13 GREEN**. Ubuntu 3.11/3.13 logs show 3 failed, 11,767 passed, 1 skipped, all 3 in `test_sqlite_sidecar_open_descriptor_epoch_run736.py`. Global `os.stat` patching removed the stat function identity from `os.supports_dir_fd`; the protected code correctly rejected unsupported descriptor inspection *before* the desired reentrant metadata test, so test regex expected `open descriptor changed` but actually received `safe descriptor-relative review unsupported`. The synthetic test now calls the real `_supported()` first, then bypasses only that already-confirmed capability preflight while injecting the OS-level stat callback. Production `_supported()`, path-denial policy and descriptor recheck are unchanged. Fix commit `6eb89b74cb15ba4b2d52ea6538059cad99a8dd0b`.
2. **Detached multi-store epoch codec identity (19 tests)** — Source commit `a06e8dd35652722f28c02108a8e34ccc76db2e33` binds original `hashlib.sha256`, `json.dumps`, regex validators, canonical digest domain, store count and signed-integer limit. Checks run before metadata access, at JSON/hash boundaries, and in capture/review paths. Test commit `e78ded38cfd4c131c61ef40bb005def8fe0a2146` adds 18 dependency-substitution rejection cases (capture/review) and 1 unmodified no-authority control. These are **authored**, pending exact-head CI.
3. **Detached file seal private-byte digest identity (13 tests)** — Source commit `cc491551884aaf72661ebc535cbe7b46a55994d8` binds original SHA-256, domain, hex matcher and byte/path ceilings before ancestor traversal, file reading and retained review; it does **not** affect intentionally injected OS `read` or metadata diagnostic callbacks in legacy tests. Test commit `cc845e2d0ebc9e3eefdc92dcb38f6d475cee7534` adds 12 capture/review rejection cases plus 1 stable non-authorizing control.

### CI evidence (HEAD-specific)

- Previous [Run736 checkpoint CI #42604941917](https://github.com/Iam-2squared/ark-ai/actions/runs/42604941917): **3/6 GREEN (Windows), 3/6 FAIL (Ubuntu)**. Direct failure logs inspected, not inferred from other commits.
- CI for fix head `6eb89b7`: [#42610728792](https://github.com/Iam-2squared/ark-ai/actions/runs/42610728792) was **IN PROGRESS** when examined.
- CI for epoch-test head `e78ded3`: [#42610953318](https://github.com/Iam-2squared/ark-ai/actions/runs/42610953318) was **QUEUED** when examined.
- CI for latest source/test head `cc845e2`: [#42611157440](https://github.com/Iam-2squared/ark-ai/actions/runs/42611157440) was **QUEUED** when examined. Report/checkpoint pushes create their own distinct HEAD-specific CI; no duplicate workflow manually dispatched. No local full pytest available in this environment: outbound GitHub DNS/git access from the container was unavailable. **Final HEAD 6/6 GREEN is unproven.**

## Isolated SQLite custody design: remaining bounded risk and next experiment

- `disconnected_sqlite_sidecar_custody` is POSIX *synthetic file-metadata inventory*, not an SQLite transaction. Directory FDs are opened with `O_DIRECTORY|O_NOFOLLOW`; source and journal/WAL/SHM entries are inspected via `dir_fd`, checked against named paths, and rechecked against held file descriptors. This detects many mid-sweep retargets and data-size/mtime/ctime changes but **not** a rename/relink after final verification, hardlink/path alias introduced by an attacker with sufficient filesystem access, hostile modification outside metadata resolution, or a coherent SQLite WAL snapshot.
- **Do not connect a SQLite database by pathname after detached preflight and claim it is descriptor-bound.** Python's `sqlite3.connect(path)` opens a new path/handle, so the inventory does not pin the actual file(s) SQLite will use. No unreviewed custom VFS, OS-level privilege change, sandbox or file-handle based connection will be introduced under a PASS label.
- Next free-only experiment: fake/temporary synthetic adapter that checks source ancestry and sidecar lifecycle before/after a *disconnected mock* transaction, explicitly denies external tool dispatch and distinguishes races from atomic snapshot claims. POSIX descriptor-relative and Windows reparse/hardlink handling need separate platform fixtures and exact-head CI. Preserve existing missing-DB `sqlite3.OperationalError` contract and forbid automatic database recreation or COMMIT-UNKNOWN replay.

## Frozen / free-only boundaries

- `main` `7a843f17eb96ed13d66f23b58b06406b3002e405`; Draft [PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) `805b377697472268db02650a89c7a94b1c5337c8` and stopped Draft UI [PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) `3b49048dd70eebcb6268299b9ecef4e301bbc0fd` remain untouched. Frozen V1/V2/Local UI/Launcher contracts/evidence unchanged. No new credentials, paid/external GPU/API, Candidate generation, protected V2 evaluation, real tool/sensor action, main merge, raw Git bypass or force push.
- This work pins in-process helper identities only; malicious code in the same interpreter or compromise of the host is **not** stopped. Synthetic hashes do not establish consent, provenance, custody of independently held witnesses, trusted clock, exactly-once effects or cross-database transaction consistency.

## Next plan / 今後の方針

1. Verify exact new CI jobs and actual failing logs; fix narrowly, with no changes to frozen contracts or safe-denial semantics.
2. Progress Memory CAS/ABA and manual COMMIT-UNKNOWN, Planner persisted read evidence and terminal recovery; add cross-platform synthetic race fixtures for descriptor custody only.
3. If lower-layer exact-head tests are GREEN, separately review immutable ToolRegistry / exact PermissionGate / occurrence / audit-before-action with a disconnected mock executor. Never execute real WRITE.
4. Continue privacy-safe Personal Context, proactive and observation backend work and free-only V3 guard reviews. Never resume stopped UI development implicitly.
