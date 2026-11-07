# ARK JARVIS foundations — Run416: fail-closed synthetic custody

**Scope:** disconnected, local-first security reviews and regression fixtures only.
**Basis:** Run415 checkpoint `3d432f31c717680c156784a332c864994b47f196` (CI #1041 / 40175442656 eventually SUCCESS all six after earlier job inspection).
**Target:** Draft/unmerged PR #8 `research/jarvis-foundations`.
No real backend, private-context model consumption, network, camera, microphone, notifications, user identity verification, or training is enabled.

## Package 1 — Proactive preparation (10 parametrized regression cases)

- Source `src/ark/proactive_synthetic_review.py`: `8b752d7b81876fec141e9178efd919db6effa1d9`, Ruff-only correction `171ed45e1085298b8c2b366f36c961d033d75134`.
- Fixture `tests/test_proactive_commit_policy_custody_run416.py`: `c165ec5af8e0e68bc4ab93dde0f8a472b7503cd7`.
- Four immutable string policy fields are bounded to 512 characters. Snapshot exact policy-field carriers before validation, hash and SQLite callbacks; refuse value-identical replacement. The trigger remains *prepared*, never dispatched.
- After a successful SQLite COMMIT, revalidate the policy, retained history and returned receipt. Any late denial **preserves the durable marker** and does not authorize retry. Receipt factory tampering does not erase a committed observation.
- The input clock remains unauthenticated, the SQLite marker is not a notification permission, and no real scheduler is started.

## Package 2 — Synthetic clock chain (7 parametrized cases)

- Source `src/ark/agency/synthetic_clock_sequence_review.py`: `1d5fad97ede447e83e9848f7087ab2665b541eaf`.
- Fixture `tests/test_synthetic_clock_chain_custody_run416.py`: `d9f4d014cea6d3171a2c9f947f49625212906142`.
- Snapshot the previous locally computed witness link immediately before event hashing. A reentrant digest or witness-construction callback cannot rewrite the previous chain link without rejection. Require canonical digest shape.
- Retained prefix validation remains read-only; trusted-clock, dispatch, and replay-authorized flags remain false.

## Package 3 — Direct privacy revocation (8 parametrized cases)

- Source `src/ark/personal_context_revocation_review.py`: `3e2b3c88a7381e7b98f3993c5ac50a467b0bb35d`.
- Fixture `tests/test_privacy_direct_scope_custody_run416.py`: `2d6e14cf42f0442b26322e77a738bebfa7b3a8a5`.
- Both direct `revoke` and `assert_not_revoked` preserve exact owner/namespace string objects, refusing equal-content substitutions during digest or schema callback.
- Revocation remains an append-only synthetic veto without actual consent, deletion, data export or cross-store atomic privacy guarantee.

## Package 4 — Memory event history (8 parametrized cases)

- Source `src/ark/memory/synthetic_event_continuity_review.py`: `e9da03dce7deda9ca41d6f2976249a917a1f2f42`.
- Fixture `tests/test_memory_event_scope_chain_custody_run416.py`: `7bc1f85010eced646b55694720aeb360ba969041`.
- Pin exact Memory owner/namespace and source Path *before* scope/genesis hash callbacks; retain caller-supplied witness carriers *before* shape validation, recheck after read-only connection acquisition.
- Reject reflected edits to a previous synthetic event chain link during hashing. Existing Memory v1 SQL schema and durability semantics remain unchanged.

## Package 5 — Registry identifier resource bounds (7 parametrized cases)

- Source `src/ark/agency/registry.py`: `1a8331268896a210a446d07a336a6dfe2ed1ae15`.
- Fixture `tests/test_registry_identifier_budget_run416.py`: `de5dfc6e49e31cc77d4ea6cafd36b359f6e25074`.
- Individual tool-registration name, capability and backend ID fields are bounded to 256 characters *before* deterministic registry-revision materialization, rejecting large caller-controlled text. The exact 256-character boundary and ordinary disconnected binding are regression-tested.
- The frozen ToolRegistry reference vectors and registry identity hashing algorithm are unchanged. No ToolBackend is executed, no authority is granted.

## Evidence / correction record

The last independently confirmed baseline is Run415 checkpoint CI **#1041 / 40175442656 SUCCESS six of six**. Runs **#1042–#1049** were observed **FAILED at Ruff B905** because the newly added proactive `zip()` expressions lacked an explicit `strict=`; no pytest result can be inferred for those heads. The correction adds `strict=True` to both calls without weakening scope-custody validation. **#1050 / 40176449113 FAILED** with Ruff PASS and 2,340 passed / 2 failed on Ubuntu Python 3.13. Both failures came from *new test fixtures* that expected SQLite duplicate-detection before the already-established one-millisecond interval check. The test-only correction `5f17a9dc87b8f94b1e167a0d767119223b5b5a0a` advances the second occurrence's synthetic clock to 200 ms, preserving the duplicate key and all rejection semantics. Subsequent #1051/#1052 and later exact-head jobs must be checked independently. Keep failures in history; do not restart equivalent workflows.

**Expected suite arithmetic only:** 2,309 previously verified tests + 40 new parametrized cases = 2,349 tests. This is **not** a claim that 2,349 have passed, nor evidence of all-platform GREEN. Exact test counts and CI runs must be reported separately after measurement.

## Frozen and hard safety boundaries

Frozen V1/V2/Local UI/Launcher and V3 Contract 1 evidence are untouched. Memory v1 and ActionAudit v1 schemas are unchanged. PR #5 stays Draft/unmerged/NOT_PASSED; PR #8 stays Draft/unmerged; main remains untouched. No real Candidate, local or external paid compute, protected evaluation opening, main merge, irreversible operation, credential/account connection or physical hardware action is authorized.

The remaining core blockers are real issuer/consent, authenticated trusted clock, external backend outcome receipts, atomic multi-SQLite snapshots, restart-safe real authorization, reliable external exactly-once effects, and end-to-end live readiness. The local digest witnesses are synthetic diagnostics, **not** security attestations.

## Next technical queue

1. Verify exact-head Ruff and all six OS/Python CI jobs; fix any failing fixture without weakening rejection semantics.
2. Exercise Planner/Occurrence/ActionAudit/Link retained-PENDING and UNKNOWN WRITE under independent history loss and concurrent commits, with no automatic replay.
3. Strengthen Memory CAS/expiry/read-snapshot fences, privacy retention and Context veto races.
4. Advance disconnected issuer/clock, observation fixture, startup and proactive scheduler contracts; continue V3 free-only identity and provenance closure separately.
