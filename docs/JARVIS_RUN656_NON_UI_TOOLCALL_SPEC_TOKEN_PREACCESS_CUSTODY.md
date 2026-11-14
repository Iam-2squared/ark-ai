# Run656 — Registry and PermissionGate input-descriptor custody (non-UI)

## Scope and basis

- Work-basis PR #8 HEAD: `6fcfa1b1d165e2217af50636181b7cbc09329b3f` (Run655 report commit).
- All changes are on Draft/unmerged `research/jarvis-foundations`; no `main`, PR #5, PR #9, UI/frontend, or frozen contract files changed.
- Source: `4c6ea87cdd89a462174b528f77a8fa522e627df2` (ToolCall); `c567d6fd814708469f09fab48f71112eb722ccd5` (ToolSpec and OneShotAuthorization).
- Tests: `4ea23657f17064bef8380ca223be61b7b6ea6cc4` (ToolCall); `6a12d81320ae3c698510f3486201b84c1ced5811` (ToolSpec/token).
- Compare baseline through last source/test commit: four fast-forward commits, **exactly four paths** (two `src/ark/agency` modules and two added tests).

## Threat addressed

Frozen/slotted dataclass **instances** do not freeze their **class attributes**. A replaced field descriptor or `__getattribute__` hook on a previously created `ToolCall`, `ToolSpec`, or `OneShotAuthorization` may execute hostile Python code **before** ordinary application validation sees the field value. Equality or `request_id` consistency checks performed after that read are insufficient. This is a local in-process adversarial-callback guard, **not** a defense against arbitrary malicious Python with complete process control.

1. **ToolCall:** `registry._require_original_toolcall_contract` now pins `tool`, `capability`, `scope`, `arguments`, and original `__new__`/`__getattribute__`/`__getattr__` class dictionary entries in addition to the existing constructor and computed-digest descriptors. Both `ToolRegistry.resolve/bind` and direct/registered `PermissionGate` call this guard **before** reading ToolCall inputs.
2. **ToolSpec:** `policy._require_original_spec_and_token` pins the three ToolSpec fields, `__init__`, `__post_init__`, and the same lookup/allocation hooks before construction or admission. Registered calls check before creating their internal spec.
3. **OneShotAuthorization:** the same preaccess check pins `token_id`, `request_id`, `expires_at_ms`, constructors and lookup/allocation hooks before reading a token and again after grant-iteration callbacks and under the token-spend lock. Neither this local one-shot token nor the returned `BoundAction` is durable or permission to execute an external WRITE.

## Authored regression cases

- `tests/test_toolcall_slot_original_preaccess_run656.py`: **42 parameterized cases**, covering 6 poisoned field/getter members × 6 registry/direct/registered READ/WRITE entry points plus 6 unchanged-policy controls.
- `tests/test_permission_spec_token_slot_preaccess_run656.py`: **60 parameterized cases**, covering 2 carrier classes × 7 poisoned field/constructor/getter members × 4 READ/WRITE direct/registered paths plus 4 unchanged-policy controls.
- Every test asserts no mock backend execution; mutated local one-shot token must remain unconsumed. Inherited `__new__` class-slot poisoning is **not** performed in the long-lived pytest interpreter to avoid CPython `tp_new` contamination seen in Run651. Its import-original descriptor is checked by production code, but no new subprocess `__new__` regression is claimed here.
- **102 authored cases are not an assertion of 102 CI passes.** No fabricated runtime identity, approval, real hardware, model benchmark, or execution evidence.

## CI evidence and remaining validation

- Prechange Run655 exact-head [CI #42181202454](https://github.com/Iam-2squared/ark-ai/actions/runs/42181202454) was **SUCCESS** for the six-job Ubuntu/Windows × Python 3.11–3.13 matrix.
- [Source ToolCall CI #42182969918](https://github.com/Iam-2squared/ark-ai/actions/runs/42182969918), [ToolCall tests CI #42183178168](https://github.com/Iam-2squared/ark-ai/actions/runs/42183178168), [policy source CI #42183329192](https://github.com/Iam-2squared/ark-ai/actions/runs/42183329192), and [policy tests CI #42183442131](https://github.com/Iam-2squared/ark-ai/actions/runs/42183442131) were **IN PROGRESS** at the initial evidence read. Actual final conclusions require a later exact-run six-job check; do not infer PASS from authored assertions.
- On CI failure, inspect the precise failed job and fix only the demonstrated issue through normal Contents API. Do not weaken preaccess rejection and do not manually create duplicate workflow runs.

## Independent offline transcript privacy lane

After the registry/policy CI pipelines began, development moved to an
**independent non-UI module** that processes only caller-supplied, detached
text/audio metadata. `src/ark/offline_transcript_binding.py` now refuses
reflectively replaced `AudioMetadataClaim`, `TranscriptSegmentClaim`, or
`TranscriptBindingPreview` field slots, constructors and attribute hooks
**before** reading transcript text or digest/owner metadata. The same guard
runs after text-hash callback boundaries and before preview creation/getters.

- Source commit `efba870a729e2c2ee62c2666aa3e5ed28e302e35`.
- New `tests/test_offline_transcript_carrier_preaccess_run656.py`, commit
  `6d2418e36d3c41ff36833bf54e9abbbebb5ffef5`: **29 authored cases**
  (25 preinstalled field/constructor/getter tampering; 3 reentrant
  text-hash phase tampering; 1 unchanged deterministic safety control).
- `TranscriptBindingPreview` remains deny-only. No transcript plaintext in
  repr/output, real microphone/ASR, consent, identity or action authority.
  Inherited `__new__` replacement was not introduced into shared pytest.
- [Transcript source CI #42183953304](https://github.com/Iam-2squared/ark-ai/actions/runs/42183953304)
  and [transcript tests CI #42184057331](https://github.com/Iam-2squared/ark-ai/actions/runs/42184057331)
  were **QUEUED** at the initial inspection, not claimed GREEN.

**Invocation aggregate:** three coherent non-UI source+test packages,
**131 authored new parameterized cases** (42 ToolCall + 60 policy carriers +
29 private transcript), and seven source/test/report commits before this
report append. The entire comparison from Run655 baseline to transcript test
commit touches seven paths: three non-UI source files, three new test files,
and this report; no frozen, V3, UI or main paths. Final CI outcomes must be
read at exact source/test/checkpoint HEAD before declaring all-six GREEN.

## Actual CI-detected transcript regressions and repair

Subsequent runs identified two **test-only** issues; neither requires
weakening the new source safety guard:

1. [Transcript source CI #42183953304](https://github.com/Iam-2squared/ark-ai/actions/runs/42183953304)
   Ubuntu Python 3.11: **9,673 PASS, 1 FAIL, 1 SKIP**.
   The legacy `test_false_denial_callback_cannot_change_result_fingerprint`
   expected a *post-read* `transcript preview changed` message, whereas
   the strengthened guard correctly refused a replaced
   `__getattribute__` **before any private read** with
   `transcript carrier definition changed`. Commit
   `2bee70b83dbe3ef184e9fd0cd319a8b62f2992f6` asserts the
   earlier rejection, confirms the forged callback is never called,
   and restores the inherited class hook without a persistent own slot.
2. [Transcript new-test CI #42184057331](https://github.com/Iam-2squared/ark-ai/actions/runs/42184057331)
   reported Ruff **I001** across the matrix due only to import order.
   Commit `dcf10e3779d950a966923158647f7ab7c4745853` changes
   `import hashlib` before `from contextlib import contextmanager`.
   No test assertions, digest semantics or source guards were changed.

The corrected source/tests commit above has
[CI #42184500589](https://github.com/Iam-2squared/ark-ai/actions/runs/42184500589)
**QUEUED** at initial inspection. Do **not** report corrected latest
all-six GREEN until exact jobs actually finish. Intermediate failed CI
runs remain part of immutable evidence.

## Preserved hard stops

No paid API/service, external GPU, Candidate generation, model-weight mutation, protected V2 evaluation opening, V3 promotion or training, new secrets/account connection, physical-PC action, real ToolBackend dispatch, camera/microphone, irreversible operation, main merge, or UI work. PR #5 remains Draft/unmerged under its existing protected gate; PR #9 remains Draft/unmerged and untouched. Overall JARVIS completion remains **NOT_PASSED**.

## Next independent non-UI work

Verify exact-head CI; if green, extend adversarial **grant-iterator reentrancy** and post-lock class-custody verification using disconnected fixtures. Continue durable Memory event/recovery and Planner/occurrence/audit-before-action integration on independent code paths without extrapolating in-memory PermissionGate state into restart-safe authorization.
