# ARK AI — Run747 non-UI due-prefix and synthetic clock preaccess custody

**Report recorded at:** 2026-11-10 05:20:34 JST (host administrative timestamp, not trusted ARK time).
**Repository/branch:** `Iam-2squared/ark-ai` / `research/jarvis-foundations`; Draft PR #8, unmerged.
**Latest verified source/test HEAD before this report:** `e0c8b46cd51372270b04fff8cf7745e644252e87`.
**Initial work basis:** `b143dc7ea56e8891eedc75225e50e6de08145903`, re-read from PR metadata.
**Scope:** free-only, purely disconnected/mock back-end contracts; no UI, actual scheduler notification, true trusted clock, ToolBackend dispatch, Candidate, V2 evaluation, protected gate opening, or paid service.

## Package A — synthetic due-prefix preaccess carrier fence

Source `src/ark/agency/disconnected_due_prefix_review.py` commit `35b70b00989fb52b5ccfaa75f179712dd681ac9f`; test module `tests/test_due_prefix_preaccess_carrier_run747.py` commit `2b1889c199969441d6d424152b687b6b4e85509e`.

A frozen/slotted dataclass does not make its class-level member descriptors immutable. A substituted `count`, `status`, `__init__` or `__getattribute__` could run code before the existing denial flags' passive value checks. The prefix reviewer now statically pins exact result and retained witness fields, their executable hooks, and the original due ledger/witness class bindings **before any retained witness scalar or SQLite source access**. Ten parameterized authored regression cases cover field replacements, constructor/getattribute hooks and class rebinding with zero substituted-callback execution. The retained prefix validation remains read-only, transaction-scoped, nonauthorizing; it does not prove independent historical custody or race-free filesystem identity.

## Package B — synthetic clock local digest-helper identity

Source `src/ark/agency/synthetic_clock_sequence_review.py` commit `b8dea926416904e6be2cbb7b577ae800111b6c57`; test module `tests/test_clock_digest_helper_preaccess_run747.py` commit `e0c8b46cd51372270b04fff8cf7745e644252e87`.

Prior protocol already pinned `hashlib.sha256`, `json.dumps`, genesis, original carrier fields and denial properties, but not the module-local `_hash` function reference. Now a replacement helper is rejected at the *first* protocol check, before caller iterator access; rebindings during `iter()` and `next()` are also rejected before the helper is called. Four authored regression cases cover initial substitution, both iterator mutation boundaries, and original non-authorizing healthy output. This is **not** signed trusted time, external clock verification, authenticated hardware evidence or action authorization.

**Legacy compatibility review:** `tests/test_synthetic_clock_digest_identity_run713.py` includes a callback-injection test that expects a replacement `_hash` to execute once before rejection. This older expectation is incompatible with the deliberate earlier preaccess fence. Treat any ensuing failure as test-expectation drift, not permission to relax the production fence; verify the actual CI log, then change only the fixture to expect *zero* hostile callback invocations.

## Independent free-only V3 gate read

Read-only review of frozen PR #5 sources `docs/v3/PRE_PAID_COMPUTE_GATE.md` (blob `14dad49017f1f69428bb6334ee46cf902bd11316`), `docs/v3/CONTRACT.md` (`b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`) and `docs/v3/HF_IDENTITY_REVIEW.md` (`76145f86d9ec81bedabd9d4dadc711d64a789cc5`). Immutable HF revision and materialized tokenizer/weight identities, exact 120/30 human-reviewed licensed dataset/provenance, runtime and converter pins, bounded approved hardware/time/JPY authorization remain unresolved. Preflight-only authorization is separate from full Candidate authorization, and neither may be inferred from CI green, mock fixtures, or this report. PR #5 remains Draft/unmerged; no frozen contract was changed.

## CI and limitations at report creation

At first Run747 snapshot, Run746 latest upstream HEAD `b143dc7ea56e8891eedc75225e50e6de08145903` CI #42689751966 was QUEUED. Two earlier Ubuntu Python 3.11/3.12 jobs under older Run746 revisions were FAIL with 12 legacy retention diagnostic expectation mismatches; that is *not* direct evidence about the new due-prefix or clock changes. Automatic commit CI IDs observed: source A #42691129695, tests A #42691268489, source B #42691431810, tests B #42691513748, all QUEUED at their first read. No exact-head 6/6 GREEN, regression PASS, local full pytest or target-PC GGUF result is claimed at this stage. New commits after this report require their own exact-HEAD evidence.

Unresolved: separate retained witness authentication; SQLite WAL/sidecar and Windows reparse/handle custody; TOCTOU; trusted clock provenance; immutable ToolRegistry registry binding; user consent; audit-before-action and cross-store crash-safe exactly-once. No unsupported identity, runtime, spend, human decision or physical evidence is asserted.

## Next plan / 今後の方針

1. Reconcile exact newest CI and inspect true failures, including the expected legacy clock callback fixture; repair tests only when semantics unchanged and document the actual result.
2. Advance independent Memory CAS/ABA/expiry and COMMIT-UNKNOWN manual-only reconciliation, and exact Planner persisted READ/terminal restart.
3. Preserve free-only V3 approval/identity/provenance blockers and privacy-safe Personal Context; keep all real effects and UI stopped.
