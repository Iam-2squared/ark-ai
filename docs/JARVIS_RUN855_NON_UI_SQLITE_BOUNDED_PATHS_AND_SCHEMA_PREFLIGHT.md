# ARK AI Run855 — Non-UI SQLite input admission and schema pre-hydration

**Work-basis HEAD:** `fa542d8fa2a62b9417f273c987a38d94b4c8663b`; its exact-HEAD [CI #43497087891](https://github.com/Iam-2squared/ark-ai/actions/runs/43497087891) was independently observed GREEN 6/6 (Windows/Ubuntu, Python 3.11–3.13). This is NOT validation of Run855 changes.

## Package A — primary Memory and ActionAudit SQLite path admission

- Memory source [`e6df799e`](https://github.com/Iam-2squared/ark-ai/commit/e6df799e8cc240299a39cfaad40241ea4b3fc755) and ActionAudit source [`bbe5a04c`](https://github.com/Iam-2squared/ark-ai/commit/bbe5a04c6920151b1bd9462fade2da6f1d4452b2): reject NUL, root/database-less paths and overlong raw or normalized paths BEFORE calling `lstat`, `mkdir`, SQLite connection or a caller clock. The 4096-character local fixture budget includes eight characters of `-journal` headroom; no directory cleanup/overwrite, contract schema or event semantics changed.
- [9 authored disposable regression cases `14a81d1d`](https://github.com/Iam-2squared/ark-ai/commit/14a81d1d429939e187b53ece633b2d3dd1da13b9) cover invalid Memory/Audit path pairs (8 combinations), unchanged empty fixture directories, and a valid Memory+Audit constructor pair. They do NOT claim atomic `openat` custody or race freedom. The tests avoid `Path.exists()` on oversized names.

## Package B — query-only detached schema SQL admission

- [Source `ac4dd03e`](https://github.com/Iam-2squared/ark-ai/commit/ac4dd03e9eb8fe6995f88190308b84ec8834b434) adds an in-transaction SQLite COUNT and DDL-byte preflight before Python retrieves SQLite schema SQL. Both object-count and DDL-byte budgets must pass before `SELECT type,name,tbl_name,sql...`. Exact JSON serialization size, digest, single-main database, query-only and double-snapshot verification remain unchanged and mandatory.
- The new preflight query is pinned to its import-time identity; substituted query strings are rejected before accessing SQLite. This is process-local contract integrity, **not** hostile-code isolation or independently authenticated schema provenance.
- [4 authored regression cases `58631c75`](https://github.com/Iam-2squared/ark-ai/commit/58631c75d0828356bb2e4af6b29f822631748cf9) cover 129-object schema, >65 KiB DDL, preflight query substitution, a normal query-only deny-only seal. SQL trace on each rejected fixture checks that the Python DDL SELECT was never executed. A separate ephemeral SQLite-only check observed the expected byte-length count for a 66 KiB synthetic DDL; that check did not run the ARK test suite.

## Independent WAL/SHM review and remaining gaps

Reviewed `scripts/diagnose_ark_store_wal_last_close.py` and its `tests/test_ark_store_wal_last_close_run847.py` companion. The diagnostic creates only disposable actual ARK Memory/ActionAudit SQLite schemas, pins a read-only SHM descriptor, coordinates a separate reader process, observes link count before/after last close, and then cold-reads committed fixtures. It does not turn an unlinked SHM into attested evidence, avoid pathname replacement after a preflight, prove a live operator's identity, or authorize a rejected COMMIT to be retried. These are still open research problems.

## Evidence and gates

- **New packages:** 2; **new authored regression cases:** 13 total. Not asserted PASS until exact-HEAD CI completes.
- **Latest test HEAD at report authoring:** `58631c75d0828356bb2e4af6b29f822631748cf9`, [automatic CI #43504215558](https://github.com/Iam-2squared/ark-ai/actions/runs/43504215558): **QUEUED** at report prewrite observation (conclusion none). No manually triggered duplicate CI.
- Frozen V1/V2/Local UI/Launcher contracts and evidence untouched. PR #5 retained Draft/unmerged, PR #9 retained Draft/unmerged/untouched, and no frontend changes. No real action, Candidate, model weights, paid service, external compute, protected evaluation, credentials, physical-PC access or main merge.
- `PermissionGate` tokens remain process-local; exactly-once durable external effect remains NOT PASSED. Neither this schema preflight nor WAL diagnostic is a trusted clock, consent or manual-review grant.

**Prioritized next:** establish exact-HEAD six-job CI; minimally fix any specific FAIL without relaxing denials; continue SQLite WAL/SHM open/close race analysis on disposable DBs; improve coherent Memory COMMIT-UNKNOWN manual triage and Planner durable UNKNOWN isolation; then assemble registry-bound, exact-type, audited disconnected mock execution only with GREEN lower-level evidence.
