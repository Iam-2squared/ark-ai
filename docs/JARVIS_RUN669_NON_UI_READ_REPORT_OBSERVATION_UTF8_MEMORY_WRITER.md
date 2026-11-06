# ARK AI — Run669 non-UI core development evidence

**Status:** Draft PR #8, free-only, disconnected/no dispatch; all changes on `research/jarvis-foundations`. Initial work-basis HEAD: `47b60e191762e15ebb61cccf521dd22d55bae261` (inherited exact HEAD [CI #42285312819](https://github.com/Iam-2squared/ark-ai/actions/runs/42285312819) **GREEN 6/6**). **No current exact-HEAD PASS claim.** Overall ARK/JARVIS/V3 `NOT_PASSED`.

## New work, exact commits and scope

1. **Detached READ journal recovery report custody** — `d9655f9e03f7a0df1921dad22f4aecc63b195d15` in `src/ark/agency/disconnected_read_recovery_journal_bridge.py`. Before retained evidence access, after callbacks and before/after report construction, verify import-original `ReadRecoveryJournalReview` class, field slot descriptors, constructor, lookup hooks and false-only denial properties. This prevents an injectable result constructor/getter from executing through a nominally inert recovery diagnostic. No change to journal v1, receipt/provenance gate, or external dispatch. Repair `bf450bf00259691d78bfa1bbf224b6ffa7cfc239` preserves the inherited fail-closed diagnostic substring `carrier changed`, while retaining the new `authority definition` explanation. This is a **message-only** adjustment, not a relaxed check.
2. **Observation identifier byte budget** — `ce028d5abefcd5e063acdc90db8ec156be372369` in `src/ark/observations.py`. Reject metadata identifiers over **1024 UTF-8 bytes**, not 1024 Unicode code points, after strict UTF-8 validation. This covers `source_id`, `adapter_id`, and `privacy_scope`, without reading hardware, retaining media bytes, or claiming source consent.
3. **Memory independent-writer COMMIT-UNKNOWN regression** — `a393c6f5d96ae43b63081576fe38db93ea00f00c`, `tests/test_memory_outcome_disjoint_writer_epoch_run669.py`: **6 authored cases** (three other-writer scope variations × unchanged vs independently matching target update). Target-row review should not confuse disjoint global event updates with target history, nor attribute matching bytes to a caller. No automatic retry or authorization.
4. **Observation UTF-8 regression** — `216b8cd859f356a7e0edffba369adffa453073bc`, `tests/test_observation_utf8_identifier_budget_run669.py`: **9 authored cases** including 1023/1026 and 1024/1028-byte labels across three fields and strict rejection of invalid surrogate identifiers.
5. **READ report constructor/slot regressions** — `6ee7e4d35e71cf83f3c59e9fb87f7c2ea3d4d063`, `tests/test_read_recovery_report_custody_run669.py`: **5 authored cases**, including original valid empty history plus class initializer, output slot, attribute lookup and nonauthorization property tamper. Injected callbacks must not execute.

**Diff verified** initial basis → `bf450bf00259691d78bfa1bbf224b6ffa7cfc239`: exactly six commits ahead, five non-UI source/test paths (two modified source modules, three added tests); no frozen source, UI, data or contract paths. **20 new authored parameterized cases** total; their exact latest-HEAD all-PASS has not yet been established.

## Remote CI evidence and correction

- `d9655f9...` [#42291698867](https://github.com/Iam-2squared/ark-ai/actions/runs/42291698867): Ubuntu 3/3 **FAIL** in inherited test `test_detached_read_recovery_preinstalled_denials_run552.py`, four cases expecting text `carrier changed`; real CI failure, no semantic gate failure observed in those cases. Never relabel as GREEN.
- `ce028d5...` [#42291763390](https://github.com/Iam-2squared/ark-ai/actions/runs/42291763390): Ubuntu early **FAIL** with same four inherited diagnostic expectations. An Ubuntu Python 3.13 log retained `9949 PASS, 4 FAIL, 1 SKIP`.
- `a393c6f...` [#42291923923](https://github.com/Iam-2squared/ark-ai/actions/runs/42291923923): Ubuntu Python 3.11 `9955 PASS, 4 FAIL, 1 SKIP`; same prior message expectation, **not** independent attribution of all six new tests across platforms.
- `216b8cd...` [#42292087726](https://github.com/Iam-2squared/ark-ai/actions/runs/42292087726) and `6ee7e4d...` [#42292213597](https://github.com/Iam-2squared/ark-ai/actions/runs/42292213597): most jobs **IN PROGRESS/QUEUED** on sampling; do not infer outcomes.
- Latest message-only source correction `bf450bf...`: [#42292349033](https://github.com/Iam-2squared/ark-ai/actions/runs/42292349033) **QUEUED** on sampling; latest full six-job GREEN still **UNVERIFIED**. No redundant manual Actions dispatch. Additional status/checkpoint commits may trigger their own workflow runs; report separately.

## Non-authorization and frozen gates

This is not a trust boundary against malicious Python sharing the process, a real actor identity, trusted clock, authenticated approval, persisted cross-store atomicity, tamperproof immutable witness, validated external result, or exactly-once WRITE. All fixture data and SQLite writers are synthetic/local. No live ToolBackend, microphone/camera/screen capture, notifications, payment, external compute or account connection.

`main` and frozen V1/V2/Local UI/Launcher evidence/contracts remain unchanged. PR #5 (`research/v3-learning-evaluation`) remains Draft/unmerged with protected V2 final evaluation, real Candidate, weights, training and promotion gates closed. PR #9 (`ui/next-generation-command-center-20261103`) remains Draft/unmerged and **untouched**; all new UI work is **PAUSED**. Do not merge main, start paid/external GPU or invoke real tool actions.

## Next plan / 今後の方針

1. Inspect the six exact latest-HEAD Ubuntu/Windows CI jobs; correct genuine failures using normal GitHub Contents changes only, preserving fail-closed behavior and existing error contracts.
2. Expand Memory COMMIT-UNKNOWN/expiry/ABA two-handle coherent snapshot and no-attribution invariants. Keep manual triage only, never automatic retry.
3. Join Planner recovered SUCCEEDED only with independently reviewed result receipts; continue ToolRegistry/PermissionGate, audit-before-action, durable authorization and disconnected mock evidence at GREEN lower-level exact heads.
4. Advance privacy-scoped Personal Context revocation, proactive restart quarantine, observation adapters and free-only V3 identity/licensing/path guards independently. Keep real V2 evaluation/Candidate, UI and main merge closed.
