# ARK AI Run936 — READ receipt preaccess, Memory race, COMMIT-UNKNOWN child exit

**Mode:** Non-UI, free-only, disconnected foundations on Draft PR #8; **overall ARK/JARVIS NOT_PASSED**. This technical report is a bounded development log, not a frozen-gate PASS or externally authenticated evidence receipt.

**Exact work-basis:** Run935 checkpoint HEAD `72702885183077f694f16138ca1320c7388537cb`. **Last new test HEAD / report-write basis:** `6d0e6f2c3ea886129f128a3923b5cbd4803e30ec`. A final checkpoint commit SHA cannot be embedded in this file; verify it from GitHub's normal Contents response and PR HEAD after writing.

## NEW changes and validation scope

1. **Source: retained READ preaccess `2f2695690a5e531f0227c704d91b0da1ceb67450`.** In `src/ark/agency/disconnected_registered_read_recheck.py`, imported-original class slot, lookup hook and false-only denial descriptors are captured at module import and verified *before any receipt field is accessed*. Recheck runs at additional callback boundaries. This is process-local tamper detection only, not a secure sandbox, signed receipt, authority, or backend permission.
2. **READ tests `57255eba27712c0b05a5077368b8694bae3ccf52`: 12 cases.** Five substituted receipt field properties, five false-looking authority flag properties, a substituted lookup hook and a normal inert recheck. Tests require changed descriptors to be rejected before the injected getter executes, and no backend calls or token consumption.
3. **Memory cross-process race `30aef49b38be41400f5bd8135bbffcd6e07c28bf`: 2 cases.** Two independently started Python processes observe retained Memory generation before a shared barrier, then compete on the same row or independent rows. The expected same-row result is one COMMITTED and one stale CONFLICT; independent rows may both commit. Cold row+event checks are fixture-only and do not imply external action atomicity.
4. **Observed CI repair `4eb4e434f296b701a7a9c3bb895143b7660f632c`.** Initial READ test CI #44026003302 failed all six environments at `ruff I001` (test import order; before pytest). The subsequent Memory source/test CI #44026134575 inherited that lint failure. Corrected only import ordering, with no production/validator weakening.
5. **Atomic COMMIT-UNKNOWN child exit `6d0e6f2c3ea886129f128a3923b5cbd4803e30ec`: 3 cases.** Actual spawned child creates a synthetic pre-action intent and exits without returning a receipt; cold triage for recorded, unrelated, and unchanged local history must always require manual review and explicitly deny dispatch, automatic replay, trusted custody and external effect proof.

**Total 17 NEW parameterized cases authored** (12+2+3); **not** 17 CI-green assertions. No private data, external GPU, Candidate, paid API, human-approval imitation, protected evaluation, real ToolBackend execution, irreversible action, UI or main merge.

## Verification and known limitations

- Prior exact HEAD `72702885183077f694f16138ca1320c7388537cb`, [CI #44020330603](https://github.com/Iam-2squared/ark-ai/actions/runs/44020330603): **completed, all six Windows/Ubuntu × Python 3.11–3.13 GREEN**; prior-HEAD evidence only.
- First new source CI [#44025927161](https://github.com/Iam-2squared/ark-ai/actions/runs/44025927161) was running when checked.
- New READ test CI [#44026003302](https://github.com/Iam-2squared/ark-ai/actions/runs/44026003302) **FAIL all six** at import-order `ruff I001`, before pytest. Inherited failure [#44026134575](https://github.com/Iam-2squared/ark-ai/actions/runs/44026134575): **FAIL** at the same import-order lint boundary.
- Import-fixed CI [#44026253001](https://github.com/Iam-2squared/ark-ai/actions/runs/44026253001) was **IN PROGRESS**, not validated to GREEN at this report's authoring. Later commits start their own CI automatically; never conflate their SHA or results with the prior successful checkpoint. Existing test assertions might need minimal adaptation if the stronger entry rejection moves an error to an earlier safe boundary. **All-six latest-head GREEN not claimed**.
- GitHub Contents API saves files by separate normal writes. The source and tests are not a single cross-file atomic GitHub transaction; exact source/test/CI attribution is retained above.
- Local subprocess fixture tests are unprivileged, synthetic SQLite; a successful transaction is not a proof of cross-store atomicity, independent retained custody, clock trust, consent, or exactly-once external action.
- No physical Windows real GGUF/offline gate. No protected V2 final-eval opening, V3 training/Candidate promotion, paid GPU or external service, or proof that ARK is JARVIS-complete.

## Next plan / 今後の方針

1. Inspect per-job CI for exact SHA `4eb4e434...` and later HEADs; fix any failing assertions using narrow, semantics-preserving updates through normal GitHub Contents, then verify all six independently.
2. Audit registered READ recheck against remaining reflected descriptor/reentrant-policy boundaries, preserving zero dispatch and typed PermissionGate identity.
3. Extend Memory WAL/SHM last-close and CAS/ABA, owner/namespace integrity, and retained event chain under cross-process races; never silently recover contaminated state.
4. Connect Planner COMMIT-UNKNOWN quarantine to durable occurrence and trusted-clock preaction audit only after exact-head GREEN. Until proven, no WRITE replay or real executor.
5. Advance privacy-safe Personal Context, proactive/observation backend, and free V3 reproduction/path/identity gates on independent lanes. Keep frozen V1/V2/Local UI/Launcher contracts/evidence and Draft PR #5/#9 untouched.
