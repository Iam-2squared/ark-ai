# ARK AI — Run606, non-UI report-class custody / pregetter checks

Scope: Draft PR #8, `research/jarvis-foundations`. Invocation work-basis:
`0ff4e70c7e10efd52f51074196d53563a358a6de` (Run605 checkpoint).
All changes are reversible, local/mock-only and outside frozen contracts.
`PR #5` V3 remains Draft/blocked; `PR #9` remains Draft and UI PAUSED.

## Work packages saved

1. **Restore CI lint only:** [CI #41829663371](https://github.com/Iam-2squared/ark-ai/actions/runs/41829663371)
   failed all six jobs in Ruff before pytest. The actual Ubuntu Python 3.12
   log showed four E501 overlength regex assertions across
   `tests/test_due_witness_commit_custody_run485.py` and
   `tests/test_due_witness_readonly_authority_run491.py`.
   Commits `5bae66d0c593f6d7212a63875bec464015f1310e` and
   `aeeed7ffdf572ebbb18d90b6d3d59d4b4b9c3a2f`
   reformatted those assertions without changing their regex or security policy.
2. **Memory ambiguous-COMMIT manual review:** source
   `490e8e8f2da4570e88bed9eeeed7917a640ed381`, tests
   `e36464988af41664eb9c1bb84b7ef5b0df44eb16`
   (**3 authored cases**). Bind `MemoryCASOutcomeReview` to its import-original
   class before input/DB inspection; checking only the original four/five
   denial descriptors is insufficient when a counterfeit class copies them
   and supplies a side-effecting constructor. Test preinstalled and
   first-snapshot substitution, and normal local-only unchanged result.
3. **Mixed READ/WRITE restart fence:** source
   `c05fa372e1f40f021f71f4b112c875ba72647542`, tests
   `05853b76e0c5b5bee875e1cef5ffe508ada89778`
   (**10 authored cases**). Validate original `OfflineRecoveryFence` class and
   all four denial descriptors *before any getter*, before construction and
   after each getter. Preinstalled and digest-callback forged False-valued
   getters are never invoked; anonymous replacement constructors are
   rejected. Previously expected delayed diagnostic messages were adjusted
   in legacy tests by commits `257c644aa0852927d4759525c1a96ac47ee9e145`
   and `033ef65c6459f649151fb2a15248513cfea0cb26`, preserving the
   exact rejection conditions and UNKNOWN WRITE quarantine.
4. **Local privacy veto review:** source
   `0e99cc820db4530ec2301fb915f28d2673337c71`, tests
   `2f2244ce6130ac6c349b36e9ecf1c52ac3ea1d27`
   (**8 authored cases**). Pin the original result class and static
   descriptors before SQLite reads, after inspection and before construction,
   and after each denial getter. A copied-descriptor fake class cannot
   construct a synthetic consent-review result. No real personal data,
   deletion or external disclosure takes place.

**New authored test cases: 21**, not independently run local PASS.
Tests use synthetic/disposable SQLite fixtures or in-memory claims.
The remote GitHub CI jobs are the validation authority for exact HEAD.
The source code is not a real ToolBackend, an authenticated human consent
source, an independent auditor, a trusted clock or a cross-store transaction.

## Known CI evidence and remaining limits

- Previous validated Run604 HEAD:
  [CI #41817710975](https://github.com/Iam-2squared/ark-ai/actions/runs/41817710975)
  6/6 GREEN at `7a0952089414d19d75a8269dc5e239425465790d`,
  **not** current HEAD.
- Run605 checkpoint
  [CI #41829663371](https://github.com/Iam-2squared/ark-ai/actions/runs/41829663371)
  6/6 FAIL due Ruff E501, diagnosed from an actual failed job log.
- Source/test/legacy-test and privacy checkpoints have new CI triggered
  by GitHub commits; terminal GREEN/FAIL verdicts must be checked per exact
  commit and not inferred from preceding branch runs. Do not launch
  equivalent manual reruns. No local GGUF/physical PC verification.

## Next plan / 今後の方針

1. Read exact latest-HEAD CI for all Ubuntu/Windows Python 3.11–3.13 jobs.
   If FAIL, inspect offending jobs and repair only the precise cause.
2. Continue durable Memory CAS COMMIT-UNKNOWN/manual reconciliation and
   row/event coherency after an exact-head source/test GREEN gate.
3. Test Planner UNKNOWN WRITE recovery, immutable ToolRegistry, PermissionGate,
   trusted-clock-dependent audit-before-*mock*-action and occurrence replay
   protection without enabling real backend execution.
4. Advance privacy-aware Personal Context/observation/proactive snapshots and
   free-only V3 identity/path/reproducibility review on independent lanes.
   Preserve frozen V1/V2/Local UI/Launcher evidence, Contract 1,
   protected V2 final gate and PR #5/#9 Draft status. No paid compute,
   new secrets, irreversible operations, protected evaluation or main merge.

JARVIS/ARK/V3 overall completion: **NOT_PASSED**.
