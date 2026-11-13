# ARK AI Run850 — coherent Memory digest custody and SQLite WAL last-close evidence

## Scope and baseline

**Initial work-basis HEAD:** `f515503d8064b362a282b28219b80e913e9bb0f9` on `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). Prior exact-head [CI #43446857496](https://github.com/Iam-2squared/ark-ai/actions/runs/43446857496) was **GREEN 6/6** on Ubuntu/Windows Python 3.11–3.13; it does **not** certify Run850 changes. PR #5 protected Draft and PR #9 paused UI Draft remained unmerged at prework observation. All source/test work is non-UI, offline, disposable and reversible.

## New coherent work packages

### 1. Memory retained-coherent WAL snapshot digest dependencies

[Source commit `37a562a3`](https://github.com/Iam-2squared/ark-ai/commit/37a562a30a738257055b6581fce41328f78a062d) pins the import-time identity of `hashlib`, `hashlib.sha256`, `json`, `json.dumps` and the reconciliation domain `_RESULT_DOMAIN` within the existing `_require_original_result_carrier()` preflight. This preflight is exercised before any user/private SQLite snapshot, and through the existing `stable()` checks after reentrant row and digest callbacks. Previously only the result-carrier slots/getters were pinned here, leaving a substituted digest callback available during local private review.

[Test file `7c59ffe9`](https://github.com/Iam-2squared/ark-ai/commit/7c59ffe954d998c6f144084e2500f161c6b0fbcf) authored **8 disposable regression cases**: four entry-time substitutions rejected before `_connect_readonly`; three mutations during `_record`, alignment hash and event-prefix hash callbacks; one valid cross-owner append that remains denial-only and read-only. No user data, consent, writer authentication, cross-store transaction, automatic retry or action authority is introduced.

Run850 [CI #43455343810](https://github.com/Iam-2squared/ark-ai/actions/runs/43455343810) **FAIL 6/6** at Ruff I001 on the new test's import block, before pytest. [Corrective test-only commit `5c696e86`](https://github.com/Iam-2squared/ark-ai/commit/5c696e860ab3cbe05da9e6b5a2bb37bf31a92d94) sorts/group imports with unchanged test semantics. The correction's full CI result was **unverified at this report's initial assembly**. Prior source-only run [#43455223310](https://github.com/Iam-2squared/ark-ai/actions/runs/43455223310) also cannot prove 8 new tests.

### 2. SQLite held-WAL keeper versus final-close sidecar custody

[Test commit `364d4fb3`](https://github.com/Iam-2squared/ark-ai/commit/364d4fb34cbd16e435e103a63eba49e73fd9b8e0) adds **5 isolated regressions** to directly exercise `disconnected_sqlite_sidecar_custody`: keeper-held stable `-wal/-shm` metadata; SQLite's last-close unlink of an already open `-shm` descriptor and mandatory rejection of that zero-link descriptor; closing the keeper between two `_capture_once` passes; and rejection of symbolic/hard-linked sidecars. Unsupported POSIX/SQLite fixture facilities explicitly **SKIP** instead of claiming an observed unlink. All files reside in `tmp_path`; no user database, external action, write retry or relaxed alias guard.

A final SQLite close can legitimately remove a `-shm` name while another process retains a descriptor. **It does not imply that a zero-link FD should be accepted as safe**. The direct causal link to earlier Memory/ActionAudit CI failures remains unproven. This experiment is not proof of cross-process atomicity, trusted provenance, or future path custody.

## Independent integration-boundary audit

Read-only inspection of `src/ark/agency/policy.py` confirms that `PermissionGate` maintains `_consumed_tokens` behind a **process-local lock**. `disconnected_atomic_preaction_ledger.py` offers a separate digest-only SQLite intent plus audit transaction, and `disconnected_atomic_registry_bridge.py` creates only inert WRITE claims. No evidence from this run proves a single restart-safe, permission-bound, audit-before-action, exactly-once execution path across those stores. **Integration of a real executor therefore remains blocked** until a tested durable protocol, clock/consent authority and crash recovery exists.

## Evidence restrictions and next steps

Latest source+test repair HEAD prior to this report: `5c696e860ab3cbe05da9e6b5a2bb37bf31a92d94`. New tests **authored 13, not 13 proven PASS**; no physical-PC, GGUF, external GPU, paid API or local full repository pytest executed. No frozen V1/V2/Local UI/Launcher contract changed. PR #5 protected V3 gate remains closed, PR #9 UI is untouched Draft, and no PR is merged.

1. Confirm final exact-HEAD CI six-job matrix; fix real failures through normal GitHub Contents API only. Do not conflate the old Ruff failure with functional failures.
2. Isolate Windows/Ubuntu Memory/ActionAudit WAL last-connection races and preserve no-follow, single-link and no-automatic-uncertain-retry policy.
3. Advance Memory COMMIT-UNKNOWN manual quarantine, coherent highwater/CAS/expiry and Planner persistent UNKNOWN propagation.
4. Build a **separate, inert** restart-safe permission/occurrence/audit join only after prerequisite exact-head GREEN. No real dispatch.
5. Continue privacy-safe context, proactive and observation back-end tests, free-only V3 identity/reproducibility and licensing guard review; UI remains paused.
