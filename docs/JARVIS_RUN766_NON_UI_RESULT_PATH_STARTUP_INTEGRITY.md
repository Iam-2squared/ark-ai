# Run766 — non-UI deny-only result and local path ingress hardening

## Scope and exact basis

- Repository: `Iam-2squared/ark-ai`; branch `research/jarvis-foundations`; [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). Initial basis: `57854f4a6aea0e97819b18a09b89b368ad638a98` (Run765 checkpoint).
- Before changes, [CI #42821518950](https://github.com/Iam-2squared/ark-ai/actions/runs/42821518950) on the initial exact HEAD completed **6/6 GREEN**, Windows and Ubuntu across Python 3.11/3.12/3.13. This is **not** evidence for Run766 additions.
- All writes used normal GitHub Contents API with a newly re-read PR HEAD, with no raw Git object bypass, force push, main merge, protected evaluation, paid compute, external call or genuine ToolBackend dispatch.

## A — Atomic-binding result class authority pinning

- Source commit `b78c1b2a34440125843fe60e8fc8c6ee4d439d08`: `src/ark/agency/disconnected_atomic_binding_snapshot_review.py`.
- Test commit `d0faf79541f30f4eb5d5ca8dccf66a1d6750b258`, correction `03bad81df215fc2af839237271669a5b7c25ef83`: `tests/test_atomic_binding_result_definition_guard_run766.py`, **18 parameterized cases**.
- Guard pins the import-original `AtomicBindingSnapshotReview` result class, all three slotted data-field definitions, seven denial/diagnostic properties, and four constructor/getattribute hooks. It verifies these before the private SQLite snapshot and before/after result construction. A property returning `False` is still executable substituted code and must not become the security baseline.
- Tests substitute each class member (14 cases), the output-class alias (one case), and confirm none of the three local states grants dispatch, automatic replay, proof of external effects or independent custody (three cases). The test restores the exact original class dictionary even for inherited dunder methods, preventing cross-test contamination.
- The reviewer remains **read-only and deny-only**; matching local action/occurrence/request bytes cannot prove human consent, trusted clock or independent custody.

## B — Privacy revocation ledger exact local Path ingress

- Source commit `214ca1fe6705b134ae1553ef774092dab50037bb`: `src/ark/personal_context_revocation_review.py`.
- Test commit `5aa723e887e3e7a6be957edc592a821ff4604787`, correction `081a46cfe587441106b2f9b6e0e18018b2e02689`: `tests/test_privacy_revocation_exact_path_run766.py`, **4 cases**.
- The constructor and internal preflight now require the actual platform `Path` type, not an accepted subclass with executable `parents`, `resolve` or `is_symlink` callbacks; source identity check also rejects an internally retargeted subclass. Existing ordinary `Path` behavior and opt-in `require_existing=True` create-forbidden recovery are unchanged.
- Tests deny subclassed source paths before filesystem getters and before creating a veto store; an existing ledger retargeted to a subclass cannot proceed with a valid private scope.
- Neither this path guard nor the retained local revocation digest proves filesystem ownership or prevents coordinated valid-file substitution; independent retained witness is still required.

## C — Proactive startup exact-path preaccess fence

- Source commit `8896eb32731a5d93b86cd92cf3dfe6093e81d57a`: `src/ark/proactive_startup_fence_review.py`.
- Test commit `82cf8f2ace5e344719b34c5ce4da395ab3da4b6a`: `tests/test_proactive_startup_exact_path_run766.py`, **3 cases**.
- Before receipt, policy or readiness fields are accessed, an exact local platform `Path` is required for the prepared-trigger fixture. A dynamically subclassed path, a string, or a null source is fail-closed. This is an opt-in diagnostic entrypoint; actual scheduler, notification, model and ToolBackend actions remain absent.
- These checks are local preaccess fencing, not authenticated writer/caller identity, independent custody or an atomic cross-store startup gate.

## Evidence, unresolved boundaries and next actions

- **New work:** 3 isolated source packages, 3 new test files, **25 new parameterized cases** in total; no UI/frontend, frozen V1/V2/Local UI/Launcher contract, Draft PR #5 or #9 mutation.
- Source package CI references: [A source #42827397979](https://github.com/Iam-2squared/ark-ai/actions/runs/42827397979), [B source #42827635871](https://github.com/Iam-2squared/ark-ai/actions/runs/42827635871), [C source #42828364973](https://github.com/Iam-2squared/ark-ai/actions/runs/42828364973). Final test HEAD [CI #42828467567](https://github.com/Iam-2squared/ark-ai/actions/runs/42828467567) **QUEUED** at last inspection. **Run766 exact final HEAD 6/6 GREEN not yet verified.** Do not promote intermediate/older CI to that claim.
- V3 passive audit of PR #5 `805b377697472268db02650a89c7a94b1c5337c8` confirmed `offline_readiness_inventory.py`, `offline_readiness_transition.py`, and `runtime_guard.py` are separate from the open JARVIS foundation branch and do not authorize spending/training from plausible strings or local snapshots. This was **read-only** and is not a V3 PASS.
- Blockers remain: Memory/Planner/reservation/audit/revocation/proactive stores are not one authenticated transaction; unknown external WRITE effects cannot be automatically retried. No verified human authority, independent custody, external exactly-once effect or real-PC GGUF gate. V3 model/tokenizer/runtime exact bytes, rights-cleared approved dataset, provider/cost ceilings and user review remain unresolved.
- Next: validate full exact-head six-job CI and fix only real failures; verify recovery against untrusted source carriers and retained privacy witnesses; continue Memory CAS/ABA and Planner cold recovery; only then consider mock-only audited orchestration. All real irreversible WRITE actions remain quarantined.

## CI failure diagnosis and semantics-preserving test isolation correction

- [CI #42827635871](https://github.com/Iam-2squared/ark-ai/actions/runs/42827635871), Ubuntu jobs on an intermediate HEAD after the first descriptor-test addition, and [CI #42827802758](https://github.com/Iam-2squared/ark-ai/actions/runs/42827802758), subsequent intermediate HEAD, exposed `TypeError: object.__new__() takes exactly one argument` in both new and pre-existing atomic-binding tests. Logs showed 12 test failures with 12,594+ other tests passing on Ubuntu 3.11 for the first failing intermediate SHA.
- Root cause confirmed by a local standalone Python slotted-dataclass reproduction: installing a property over `__new__` can leave the interpreter's class construction slot poisoned **even after restoring its prior class dictionary**. Merely adding `delattr` in `03bad81...` was insufficient for this special method. This was a test-harness mutation leak, not evidence that synthetic atomic matching grants authority.
- Normal Contents correction `2e846beb80f73d4368b80d59f6980acabe951179` moves the single `__new__` substitution regression into an isolated child Python interpreter, retaining a denial assertion. In-process field/property/other-hook cases still restore the exact original class dictionary in `finally`. The stated total remains **18 atomic tests / 25 Run766 new cases**. No production source condition was weakened.
- This fix has **not** yet obtained complete exact-HEAD CI GREEN evidence at the time of recording. The failed intermediate CI cannot be reinterpreted as success; verify the full six-platform/versions after the checkpoint write and diagnose any new failure independently.
