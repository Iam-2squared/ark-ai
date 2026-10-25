# ARK disconnected Memory CAS, four-store recovery and proactive return fences — Run424

**Safety:** reversible synthetic-only changes in `research/jarvis-foundations`, Draft PR #8. This document is engineering rationale, **not** verified CI evidence, signed time, human authorization, backend outcome proof, or an autonomous-dispatch gate. No frozen V1/V2/Local UI/Launcher contract/evaluation is altered.

## A. Memory v1 pre-COMMIT identity and no-row semantics

Source: `src/ark/memory/sqlite_store.py` at commit `d942cd1c15a32ba3f906e73167b5e237424806dd`. Tests: `tests/test_memory_delete_purge_precommit_carriers_run424.py` at commit `d2d1f5c021f9f6619066aa743d93c50d8ffa89e2` (**11 parametrized cases**).

- The Memory v1 SQLite schema, row/event atomicity and existing CAS revision predicates remain unchanged.
- A caller-owned frozen `MemoryScope` is **reflectively mutable**. A reentrant SQL trace callback can replace its owner/namespace `str` with an equal-text but different carrier after the initial checks. Previously `delete` and `purge_expired` could reach SQLite COMMIT, and only then reject the new carrier. For an absent DELETE row, the method could return `False` after a caller scope change.
- These paths now bind original owner/namespace carriers across clock, SELECT, hydrated-row processing, per-row purge, audit INSERT and before-COMMIT checks. The missing-row DELETE path also verifies its source/owner/namespace before returning `False`.
- Tests inject equal-text carrier substitutions during SELECT and audit INSERT; they assert exception **and durable rollback** of deleted rows/events. A separate missing-row negative test checks no clean `False`; an unmodified fixture checks exactly-once local event persistence.
- These guarantees concern local SQLite transactions only. They are not human privacy erasure authority, distributed locks, or external exactly-once outcomes.

## B. Four independently committed SQLite stores: suffix loss

Test: `tests/test_recovery_four_store_tail_loss_run424.py` at commit `6bb06b4244a2ebf1ce79314b74c7a4aac70722ed` (**4 parametrized cases**).

- Two distinct WRITE steps are left after synthetic crash-after-audit-link, without invoking their mock backends.
- The caller retains the independent initial Planner, Occurrence, ActionAudit and AuditLink witnesses.
- A disposable clone of each SQLite store loses only its **last** row, with the first row still present and correctly formatted.
- Recovery must reject all four partial-tail-loss variants with retained evidence and preserve the original source fixtures. Even a coherent local prefix is not sufficient external authorization; no WRITE replay or external effect is allowed.

## C. Proactive Scheduler × Startup final result construction

Source: `src/ark/proactive_startup_fence_review.py` at commit `9f02fc25a33ebb277a4fc020b518c8e7c3b48b63`. Tests: `tests/test_proactive_startup_final_constructor_run424.py` at commit `a0dee9d8b1a3d2f2da20f5488f58d40a883ffc7a` (**11 parametrized cases**).

- A final `SyntheticProactiveStartupReview` constructor is another reentrant boundary; it cannot be assumed safe merely because readiness and trigger evidence were independently checked before construction.
- After constructing the inert result, verify input/source carriers again; check the original startup snapshot integrity; compare returned trigger, readiness, history and clock-field carriers to their exact pre-constructor values; reject forged returned witnesses.
- Negative tests mutate individual result fields, original Policy/Receipt/SQLite source, nested Startup component, and earlier independent reviewer receipts during the constructor. The stable fixture remains **non-authorizing**, with no notification or ToolBackend dispatch.

## D. PermissionGate exact stored carriers before WRITE token spend

Source: `src/ark/agency/policy.py` at commit `9d186d6f8c7315e54ea064798863daff0e21cec8`. Tests: `tests/test_permission_original_write_carriers_run424.py` at commit `1dfa43695565c25dd45f2bcb225eef916462e065` (**30 parametrized cases**).

- Direct `authorize` and registry-bound `authorize_registered` now preserve exact original stored scalar carriers for ToolSpec, ToolCall and OneShotAuthorization throughout grant iteration, registry callback and under-lock token admission.
- Equal-text replacement of a ToolCall name/capability/scope, ToolSpec name/capability, or raw token ID/request/expiry cannot be substituted while keeping mere equal values. The process-local token remains unspent when a pre-spend callback changes any such original carrier.
- `ToolCall.request_id` is **computed** from a deterministic digest. Its **value**, not the identity of each freshly generated string, is verified; this preserves existing behavior and avoids identity false positives for a computed property.
- Tests explicitly exercise generator exhaustion and lock-contention callback phases, both direct and registry-bound checks, plus stable permission evaluation. The synthetic backend is never invoked.
- A consumed in-process token is **not** durable authorized consent across restarts; actual dispatch stays disabled.

## Evidence status and boundaries

These changes comprise four independent work packages and **56 new parametrized pytest cases (11 + 4 + 11 + 30)**. The prior Run423 source baseline had 2619 passed / 1 skipped on Ubuntu Python 3.13. **Do not declare Run424 GREEN without examining exact-HEAD CI jobs.** The canonical `docs/PROJECT_STATUS.md` contains definitive verified CI metadata and the checkpoint basis.

Still missing: real authenticated human issuer/consent, trusted signed clock, real backend attestation, atomic cross-SQLite snapshot, external exactly-once execution, physical/sensor access and a trained Candidate. UNKNOWN/RUNNING and reserved PENDING WRITE remain non-replayable without independent external outcome verification. No paid services, external compute/GPU, protected V2 final evaluation, frozen-schema changes, promotion, main merge, new credentials or destructive operations.
