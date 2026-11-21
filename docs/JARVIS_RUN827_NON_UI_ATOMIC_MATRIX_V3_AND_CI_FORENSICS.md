# ARK AI Run827 — non-UI atomic storage, WRITE quarantine carrier custody, free-only V3 validators

## Scope and exact development basis

- Initial inspected branch HEAD: `11a262e9e763c7cac58d58498cb44c756b8658ea` (two preexisting, independent Run827 Memory diagnostic commits already on the branch before this invocation).
- Branch: `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), not main.
- Last executable/test HEAD for **this** package set: `a1a67429b427e0c35263a7a7c1e527a528761aa5`. This documentation does not change runtime semantics.
- Relative to the initial work-basis, **six normal GitHub Contents API commits** from this invocation (3 initial packages with a focused test repair); no force push, bypass, UI, frozen contract, or #5/#9 changes.
- **36 authored regression cases** at last executable/test HEAD: Atomic SQLite 11, WRITE matrix 21 (reduced from initial 24 due to a CPython test-isolation hazard), V3 4. Authored tests are NOT a claim that final HEAD passed CI.

## Work package A — inert atomic intent/pre-action audit SQLite corruption

- [Tests `62a00c33`](https://github.com/Iam-2squared/ark-ai/commit/62a00c336b7ce238bebdf859cb6ccb6b100fef62) add 11 disposable SQLite cases to `tests/test_atomic_preaction_storage_custody_run827.py`.
- Poison text storage with BLOBs or replace valid-grammar identity/digest values in `intents` or `preaction_audit`. Require `inspect()` and `reserve()` refusal with no new row, no half-audit, and retained-witness mismatch on restart.
- These fixtures do not access user databases, consent issuers or live tools. A same-file locally observed digest cannot independently authenticate authorization, a crashed writer or an external effect.
- [Initial package CI #43305454490](https://github.com/Iam-2squared/ark-ai/actions/runs/43305454490): Ubuntu 3/3 GREEN; Windows still running on the last inspected job list. No inference about later HEADs.

## Work package B — disconnected WRITE quarantine original carrier preaccess

- [Source `fdeca412`](https://github.com/Iam-2squared/ark-ai/commit/fdeca412a8048070068eb5f20dd1de61305337fb) pins original class/slot/constructor/getter identities for `SyntheticWriteStoreObservation`, `SyntheticQuarantineFinding`, and `SyntheticQuarantineMatrix`, before reading a forged observation or invoking its callback. Existing False-only authority denial still applies. Source file: `src/ark/agency/synthetic_write_quarantine_matrix_review.py`.
- [Original test `dc0a6821`](https://github.com/Iam-2squared/ark-ai/commit/dc0a6821091dc28ac822bc39ccef6745788362ae) tested 24 variants. **Real CI detected a test-fixture isolation error:** `__new__` monkeypatch then deletion on a live slotted dataclass leaves CPython's class `tp_new` slot changed. Subsequent unrelated constructions failed with `TypeError: object.__new__() takes exactly one argument`; older matrix tests also failed because of this poisoning. This is a shared-process test defect, not a reason to weaken WRITE quarantine checks.
- [Minimal test-only repair `a1a67429`](https://github.com/Iam-2squared/ark-ai/commit/a1a67429b427e0c35263a7a7c1e527a528761aa5) drops three in-process `__new__` mutation cases, retains the runtime `__new__` identity guard, and keeps 21 safely isolated cases: 11 original fields, nine other class hooks, and one baseline fail-closed outcome. No WRITE release, replay or ToolBackend dispatch.
- [Pre-fix test CI #43305904064](https://github.com/Iam-2squared/ark-ai/actions/runs/43305904064): Ubuntu 3/3 **FAIL** with the above stack trace and failures in older tests; [repair exact-head CI #43306963944](https://github.com/Iam-2squared/ark-ai/actions/runs/43306963944) was running/queued at the last inspected job list. **Do not label repaired HEAD GREEN until all six job conclusions are verified.**

## Work package C — synthetic V3 helper identity, free-only

- [Source `24098abe`](https://github.com/Iam-2squared/ark-ai/commit/24098abec5da0d1bf1436d129b114688f8c9d793) pins original `_numeric`, `_device`, `_digest` helper callbacks inside the detached V3 `_protocol()` check before reading supplied synthetic preflight evidence.
- [Tests `58edb2ff`](https://github.com/Iam-2squared/ark-ai/commit/58edb2ffcc8ea15e49e444ad638665e2475be6ae) add three fail-before-call fault injections plus one nominal denial-only review. They do **not** invoke a CUDA runtime, GPU, Candidate, paid service, protected V2 evaluation, training or automatic promotion.
- The packet is a local untrusted crossbind, not independently authenticated runtime provenance, consent or spending authorization. The V3 protocol on Draft PR #5 is **unchanged**.

## CI, verified history and unresolved investigation

- Prior Run826 exact checkpoint [#43295767903](https://github.com/Iam-2squared/ark-ai/actions/runs/43295767903): GREEN all six Windows/Ubuntu × Python 3.11/3.12/3.13.
- Preexisting Run827 Memory diagnostic test HEAD `11a262e9` [#43303668516](https://github.com/Iam-2squared/ark-ai/actions/runs/43303668516): GREEN all six jobs, inspected individually.
- Atomic tests [#43305454490](https://github.com/Iam-2squared/ark-ai/actions/runs/43305454490): 3 Ubuntu GREEN, Windows pending at last review; later matrix source/tests or V3 commits require their own exact-HEAD proof.
- Initial WRITE tests [#43305904064](https://github.com/Iam-2squared/ark-ai/actions/runs/43305904064): confirmed Ubuntu FAIL from unsafe *test* `__new__` monkeypatch. Repaired source semantics are unchanged, repaired test outcomes pending.
- [#43306208788](https://github.com/Iam-2squared/ark-ai/actions/runs/43306208788) was in progress at last read, pre-repair and **not** proof of repaired result. [Repair CI #43306963944](https://github.com/Iam-2squared/ark-ai/actions/runs/43306963944) queued/in progress. No manually duplicated workflow runs.
- Historical [#43252974470](https://github.com/Iam-2squared/ark-ai/actions/runs/43252974470), Ubuntu 3.12 job `131303524907`: 1 real intermittent failure out of 14,338 passing/1 skipped in a separate-owner, two-process Memory create test. Log shows a `MemorySchemaError` for sidecar file kind/link count but **not** its detailed suffix/metadata, because that failing revision predates bounded sidecar diagnostics. Root cause unresolved. No alias/symlink/orphan guard relaxation, unsafe retry, or fabricated reproduction.

## Unchanged boundaries and Next plan / 今後の方針

- All V1/V2/Local UI/Launcher frozen contracts/evidence remain unchanged. Draft PR #5 (protected Candidate/prepaid gate) and paused Draft PR #9 (Next Generation UI) are untouched; all #5/#8/#9 remain Draft/unmerged at initial inspection. No UI source/tests/integration, real execution, action replay, new credentials/accounts, protected evaluation, external GPU, paid API, training, destructive change or main merge.
- Next: verify all six **exact** repaired-HEAD CI jobs; if FAIL inspect real logs and apply the smallest fix, switching to an independent non-UI lane while CI runs. Use disposable independent-process WAL/CAS phase comparisons to isolate the earlier sidecar refusal without safety bypass. Continue coherent Memory CAS/ABA/COMMIT-UNKNOWN, Planner durable UNKNOWN terminal propagation, immutable registry/permission/audit-before-action **disconnected** integration and privacy/scheduler/offline observation guards after lower-layer exact-head evidence.
- **Overall ARK/JARVIS: NOT_PASSED**. A locally matching ledger or digest is never authorization, authenticated consent, trusted clock, external completion or a PASS decision.
