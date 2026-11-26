# ARK AI Run632 — Planner CI recovery and non-UI original receipt custody

**Scope:** isolated Draft PR #8 only, not merged, NOT JARVIS PASS.
No UI/frontend work, real ToolBackend, external effects, Candidate creation,
GPU/cloud compute, paid service, protected V2 evaluation, or new credential.

## Exact basis and saved work

- Invocation work-basis PR #8 HEAD: `46e3e02214c1bbf3db1472bb9d0f75ccdf67b4c5`
  (Run631 work). Branch: `research/jarvis-foundations`.
- **CI diagnosis and Planner legacy correction**, commit
  `bf9ce5ca004f889ccdaec71d44319c54cbf208b0`: prior
  [CI #42015663182](https://github.com/Iam-2squared/ark-ai/actions/runs/42015663182)
  observed a formerly-valid test that patched `SyntheticPlanRecovery.__getattribute__`.
  Its append argument `retained=baseline.tail` was evaluated *inside*
  that forged-getter context, causing a side-effecting `tail` read before
  the production call. The test now pins `retained_tail` before patching.
  Both parametrized recover/append cases continue to require early refusal
  and zero malicious getter execution, without changing source semantics.
  [CI #42016677437](https://github.com/Iam-2squared/ark-ai/actions/runs/42016677437)
  was previously observed GREEN for Ubuntu 3.11–3.13 and Windows 3.11;
  Windows 3.12/3.13 remained IN PROGRESS, NOT yet 6/6 GREEN at that observation.
- **Action Audit exact receipt class slots and lookup hooks**:
  source commit `decc3458872e4de84f3fe14eda56e886e5a750bb`, tests commit
  `bdc804ab3e20ffd890076366608722f87007163b`.
  `src/ark/agency/audit.py` pins import-original eight slotted receipt
  descriptors plus `__new__`, `__getattribute__`, `__getattr__`
  before SQLite receipt hydration or construction; rechecks
  the post-COMMIT branch with an explicit phase diagnostic.
  `tests/test_action_audit_receipt_slot_original_run632.py` adds **12**
  parametrized regression cases for preinstalled forged properties/hooks,
  clock-time substitution and read-schema callback mutation. A late
  post-COMMIT refusal does not prove rollback.
- **Disconnected/mock-only final receipt**:
  source commit `5ebb06e1b94a3cd200aaa1c86d21e448d75ccd3c`, tests
  `f2d3ed0cc98863e97fa54df900d60bfebb47d2bb`. Original final
  `SyntheticMockCycleReceipt` fields and class getter hooks now reject
  substituted executable descriptors without invoking them. Added **7**
  parametrized cases spanning preflight and postterminal callback, plus
  ordinary non-authorizing fixture. Initial
  [CI #42017837962](https://github.com/Iam-2squared/ark-ai/actions/runs/42017837962)
  FAILED at Ruff I001 for a test import block, NOT a behavioral PASS.
  Minimal import-only fix `868b8d1fa8d1fa49a193b6951d6dfa08f4273f2e`
  starts corrected [CI #42018024624](https://github.com/Iam-2squared/ark-ai/actions/runs/42018024624);
  status was IN PROGRESS at last checked snapshot.
- **Memory generation-fenced CAS token**:
  source commit `6be734289d5c8c2f9a59be81fada9bdf23a36bff`,
  tests `849570a61080da7b9e6b1cb215dbbb7f5655e5f5`.
  Import-original six slotted `MemoryGenerationCASToken` fields
  and three class lookup/constructor hooks are verified before
  `_token_fields()` accesses caller-retained evidence.
  `tests/test_memory_generation_token_slots_run632.py` adds **13**
  cases: forged descriptors on observe/update, a synthetic clock callback,
  and clean local CAS update. No replay, consent inference, or real tool effect.
  Source-only [CI #42018281257](https://github.com/Iam-2squared/ark-ai/actions/runs/42018281257)
  was IN PROGRESS; exact source/test
  [CI #42018369612](https://github.com/Iam-2squared/ark-ai/actions/runs/42018369612)
  was QUEUED at last observed read.

**Package accounting:** 4 coherent work packages, **32 new
parametrized test cases AUTHORED (12+7+13)**, two Planner legacy cases fixed,
plus one mock-import Ruff repair. Test authorship is NOT local pytest PASS.
The execution environment has no verified local clone/pytest/Ruff result;
only GitHub Actions evidence may establish platform GREEN. Tests run on free
repository CI only and were triggered automatically by ordinary Contents writes;
no duplicate manual workflows, ref rewrites or force push.

## Safety and remaining engineering gaps

All new local receipts, SHA evidence, synthetic clocks and multi-SQLite
comparisons remain **untrusted, non-authorizing evidence**. The disconnected
mock cycle does NOT invoke its registered backend. Post-COMMIT uncertainty
remains manual-only: NEVER automatic retry/replay, never assume cross-store
atomicity. Existing Memory v1 schema, frozen V1/V2/Local UI/Launcher evidence
and the V3 Contract 1 gate remain unchanged; PR #5/#8/#9 all Draft/unmerged,
PR #9 UI work PAUSED. No payment, external GPU/API, actual Candidate,
real reviewer consent, protected evaluation, physical PC, new credentials,
irreversible cleanup, or approval-required main merge.

**Next plan / 今後の方針:** (1) Verify complete Windows + Ubuntu CI
for the corrected exact source/test heads; repair only genuine logged failures
via the normal guarded GitHub Contents path. (2) Once the earlier Planner
path is GREEN, close the distinct `_checked_snapshot()` post-`_snapshot`
callback/field-read guard gap with exact focused fixture tests (do not
invalidate in-flight CI on the same path). (3) Deepen coherent Memory
row/event/CAS/expiry diagnostics and privacy lifecycle without unverified
authorization. (4) Only after dependency exact-head GREEN, advance
immutable ToolRegistry/PermissionGate, audit-before-*mock*-action and
restart recovery; preserve all frozen contracts and free-only V3 gates.

**Overall status: ARK / JARVIS / V3 NOT_PASSED.**
