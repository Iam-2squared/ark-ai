# ARK AI — Run605 non-UI static trust-boundary review

**2026-11-04 JST.** Three independent non-UI source/test packages on Draft PR #8 (`research/jarvis-foundations`), plus minimal legacy-test expectation repairs. No real tool execution, notification, paid compute, protected evaluation, external disclosure, UI change or main merge.

## 1. Durable due-slot witness: fail before counterfeit getters

- Source `src/ark/agency/disconnected_due_reservation.py`, commit `3b379086d02e83ebd4cea7966a6a7523c2ac6190`.
- New tests `tests/test_due_witness_original_denials_run605.py`, commit `48df3c459a8e9d85c168a76233c97229418f9fab` — **11 authored parameter-expanded cases**, not 11 local pytest PASS.
- The original `independent_custody_proven` class descriptor is pinned at module import. Constructor, retained witness check and post-COMMIT witness check all reject descriptor replacement before a False-looking getter can execute. Reentrant getter/class changes are rejected after callback boundaries.
- Pre-reservation rejection leaves zero new rows. A counterfeit introduced by the synthetic receipt constructor after a successful COMMIT yields **UNKNOWN for external effects**, never an assertion of rollback or permission to automatically retry. SQLite digests and caller-retained snapshots do not prove independent custody, trusted clock or human authorization.

## 2. Registry: structural checking without dynamic protocol callbacks

- Source `src/ark/agency/registry.py`, commit `f326e5c20862f90a9743dc1337a9c978988e5a25`.
- New tests `tests/test_registry_static_protocol_run605.py`, commit `bcd78f90233cfb484fabeb3312b2055d4d915e01` — **6 authored cases**.
- Registration previously ran `isinstance(backend, ToolBackend)` after an `inspect.getattr_static` check. On Python 3.11 a runtime-checkable Protocol may perform a dynamic `execute` attribute lookup, invoking a backend-supplied `__getattribute__` despite the earlier static check. The Protocol only requires `execute`; its static-callable presence is already validated, so the redundant runtime check is removed.
- Tests require that registering, resolving, binding and revision checking never look up `execute` dynamically or call the backend; static noncallables still fail, and reflected interface changes still fail by descriptor identity.

## 3. Privacy erasure: fail between each inert property callback

- Source `src/ark/privacy_erasure_evidence_review.py`, commit `ede07e5b0be280fc6d38737c12c35f8165055f04`.
- New tests `tests/test_privacy_erasure_per_getter_guard_run605.py`, commit `d8e2ff558f75b0c78b205e1d6a4ed0c8efa2e3eb` — **6 authored cases**.
- Original descriptors are now checked before and after **each** deny-only property access. The synthetic result carrier and original observations are revalidated between getters. A hostile `__getattribute__` returning False cannot install an executable later getter without detection first.
- Optimistic SQLite/WAL/backup statements are *not* forensic deletion proof. No actual erasure, cleanup or external transmission occurs.

## CI discovery and limited repair

- The **prior Run604 checkpoint HEAD** `7a0952089414d19d75a8269dc5e239425465790d` completed **six Windows/Linux jobs GREEN** on [CI #41817710975](https://github.com/Iam-2squared/ark-ai/actions/runs/41817710975).
- First due-witness test HEAD `48df3c459a8e9d85c168a76233c97229418f9fab` [CI #41828373506](https://github.com/Iam-2squared/ark-ai/actions/runs/41828373506): Ubuntu Python 3.12 **8058 PASS / 1 SKIP / 4 FAIL**, with four old tests requiring later rejection messages instead of the new earlier static refusal. This is a genuine **FAIL**, not GREEN.
- The failure was inspected in actual Ubuntu 3.12 job logs; three existing test files were updated to accept **either of the two specific fail-closed denial stages**, not arbitrary errors: `tests/test_due_retained_authority_recheck_run492.py` (`f48342cf4bf19d13ab50dc75c9dbdeb115b7a583`); `tests/test_due_witness_commit_custody_run485.py` (`a058abf7528e828bd502eae68af15daceaff2c1c`); `tests/test_due_witness_readonly_authority_run491.py` (`ac069938fc66165fe530c28d2c7dcc2c66f4107d`). No production safety condition was relaxed.
- [CI #41828666089](https://github.com/Iam-2squared/ark-ai/actions/runs/41828666089) and [CI #41828898480](https://github.com/Iam-2squared/ark-ai/actions/runs/41828898480) are intermediate heads, predating the three corrections. Do not label the final fixed HEAD GREEN until **its own** six jobs complete.
- **Total new cases authored: 23** (11 + 6 + 6), not independently executed local PASS totals. This invocation did not run the user's physical PC or a real GGUF model.

## Frozen and authorization boundaries

Memory Contract blob `b6e93821ecd69270a7634aceb20775dc36e9953c`, Planner Contract `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`, V3 PR #5 Contract `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23` were re-read and are unchanged. V1/V2/Local UI/Launcher evidence is untouched. PR #5 remains Draft/unmerged and its protected V2 evaluation closed; PR #9 remains Draft/unmerged and UI development paused.

No paid or potentially billable external GPU/API/service, real Candidate, protected V2 opening, automatic promotion, credentials, live ToolBackend, camera/microphone, private external disclosure, destructive operation or main merge. ARK/JARVIS/V3 remain **NOT_PASSED**.

**Next plan / 今後の方針:** (1) inspect the *newest exact-head* CI including Windows 3.11/3.12/3.13; minimal repair only for proven failures; (2) Memory CAS post-COMMIT ambiguous result/manual-only reconciliation; (3) Planner mixed FAILED/BLOCKED/unknown RUNNING restart and registry-bound audit-before-*mock*-action; (4) privacy revocation, proactive/observation fixture provenance and V3 free-only reproducibility guards, without UI work.
