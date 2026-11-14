# Run655 — Non-UI concurrent audit-link, startup fan-in, and Memory WAL event-phase coverage

**Scope:** Draft PR #8, local-first disconnected/mock regression coverage only. Initial audited work-basis HEAD: `13ac19bc24b0ae4010e605f0fd9a857f205ba368` (Run654 source/report before its checkpoint). All source/contract freezes and UI pause remain intact. No network backend, physical PC, paid compute, credentials, model training, V2 protected evaluation, Candidate, real permission or account action.

## 1. Concurrent synthetic pre-action audit-link claims

- New `tests/test_synthetic_link_cross_handle_races_run655.py` contains **3 authored regression cases** across two independently opened SQLite writer connections (via the link store's ordinary transaction-per-call path).
- Same occurrence + same pre-action audit event, launched from a two-party barrier: exactly **one** link may commit; losing writer must receive `SyntheticAuditLinkRejected`. A fresh store must verify one contiguous row, and receipt authority/outcome/replay properties remain False.
- Two distinct occurrence reservations and two distinct pre-action audit events launched concurrently: both may append, with contiguous sequence IDs and a valid retained witness, without claiming real execution.
- Distinct reservations competing to claim the **same audit_event_id**: only one sidecar link may commit. This tests the unique audit-subject constraint independently from unique occurrence enforcement.
- Synthetic databases are separate and their aggregate writes are **not** cross-database atomic. A successful link identifies no authentic user/issuer and proves no external exactly-once operation.

The initial file commit `c5da978571efaee28e37b8ac655a591cdfbfbb76` triggered [CI #42180033628](https://github.com/Iam-2squared/ark-ai/actions/runs/42180033628), **6/6 FAIL at Ruff F401** because of an unused `pytest` import. The only correction was to remove that import via the normal contents path in `fedc002e139717f9dd828d98900eeed08f9b989d`. Corrected [CI #42180201309](https://github.com/Iam-2squared/ark-ai/actions/runs/42180201309) had **4/6 GREEN, 0 FAIL, 2 IN PROGRESS** when this report was drafted. No original source safety check was changed.

## 2. Startup readiness dependency fan-in

- `tests/test_startup_core_dependency_fanin_run655.py` contributes **4 authored cases**: Memory BLOCKED and Audit BLOCKED alternatives (two parameterizations), input-order-independent graph identity, and forged READY on a cached dependent result.
- Artificial Memory/Planner/Registry/Permission/Audit/WRITE/Personal Context/Observation/Proactive/recovery probe dependencies are asserted. Memory or Audit BLOCKED must propagate to WRITE and recovery; unrelated Permission state remains unaffected. A separate Observation DEGRADED can remain diagnostic without granting notifications, sensors or tool dispatch.
- A reflected cached write-executor READY cannot be reused after the graph's original blocked source, including via `state()` or `root_blockers()`. No real startup probe is performed.
- Saved via normal `create_file` commit `ba3f5c43d762aeff25d7b20afc6260c492d0fd20`; [CI #42180543503](https://github.com/Iam-2squared/ark-ai/actions/runs/42180543503) had **3/6 GREEN, 0 FAIL, 3 IN PROGRESS** at report drafting.

## 3. Coherent Memory event-phase WAL audit

- `tests/test_memory_event_hash_phase_wal_interleave_run655.py` contributes **3 authored cases**, each on disposable SQLite with two independent `SQLiteMemoryStore` handles.
- A writer commits a new other-owner row, a same-key UPDATE, or DELETE then CREATE **after the first event digest callback**, later than the earlier row-scan interleaving tests. The in-progress read-only audit must return the prior coherent row+event fingerprint. A subsequent fresh audit must observe the newly committed event tail and correct row count, without suggesting deletion/erasure proof, writer attribution, user consent, or execution authority.
- The test's one-shot monkeypatch is confined to the test's `_charge` callback; neither a global Python allocation slot nor production SQLite source is patched. No real user data is touched.
- Saved as `bda0b7dd051a2ff45fab8c7dabaf842b9b5f17e1`; [CI #42180675682](https://github.com/Iam-2squared/ark-ai/actions/runs/42180675682) had **2/6 GREEN, 0 FAIL, 4 IN PROGRESS** at report drafting.

## Pending verification and next engineering work

**10 authored regression cases across three packages; this is not a measured PASS count.** The full six-environment matrix on the final exact source/test HEAD is **NOT YET VERIFIED GREEN**. Ubuntu jobs already passing on predecessor HEADs do not certify later HEADs. This environment could not clone GitHub directly due DNS resolution failure, so no local full pytest/target-PC GGUF result is claimed.

After the corrected latest test tree has full exact-head GREEN, consider a separate security package for `SyntheticAuditLinkReceipt`: its exported factory and class-level receipt field/denial hooks are currently checked **after** link COMMIT, so a substituted Python result constructor may execute before rejection. A pre-construction import-original descriptor guard could fail earlier, but the existing `test_audit_link_receipt_commit_custody_run415.py` explicitly expects an already-committed link when its exported factory is replaced. A safer behavior change must be accompanied by a reviewed adjustment of those test expectations and distinct post-COMMIT-callback tests; do not weaken the durable-result ambiguity rule or declare external exactly-once semantics.

Never bypass a rejected normal GitHub source/test write. Continue free-only Memory integrity and Planner/PermissionGate/audit-before-action mocked integration under established evidence gates. Keep PR #5 and PR #9 Draft/unmerged and frozen, all new UI work paused, main unmodified, and JARVIS/V3 **NOT_PASSED**.
