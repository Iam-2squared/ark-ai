# Run638 — Retention CI recovery, BoundAction result custody, Memory first-hash epoch

Recorded in JST on 2026-11-06. All changes remain on Draft PR #8; no new UI/frontend work, backend dispatch, paid compute, Candidate construction, frozen-contract modification or main merge.

## Exact work-basis and evidence classification

- Invocation work-basis PR #8 HEAD: `5c89a2af9eca8f56fd4aaabdee04ddbf01b83e68` (Run637 checkpoint).
- Run637 exact-head CI [#42060656946](https://github.com/Iam-2squared/ark-ai/actions/runs/42060656946) **FAILED 6/6**. Ubuntu Python 3.11: 10 FAIL, 9,077 PASS, 1 SKIP. Windows Python 3.11: 10 FAIL, 9,018 PASS, 60 SKIP. Failures all show an earlier safe denial `retention inventory authority denial descriptor changed` conflicting with expectations from older tests that expected later item/result checks. No success or PASS can be inferred from that CI.
- First repair commit `fba90fdca9481c6ed98ae915cb9c00392ffb0928`: the six original retention item-epoch cases now use a reentrant row/veto callback to corrupt an actual cached item, without patching a pinned result constructor. This preserves test coverage of post-construction mutation instead of accepting an earlier refusal for every case.
- `1f3057b61be9d7991c59039de6d83d65a7920db2`: constructor-forgery case now explicitly tests earlier refusal and asserts the forged initializer was **not invoked**.
- `364c58d29cf905e3686e805b02e7302ab5319565`: old authority-spoof expectation aligned to the import-original descriptor preaccess refusal.
- The intermediate CI [#42068028130](https://github.com/Iam-2squared/ark-ai/actions/runs/42068028130) and [#42068297557](https://github.com/Iam-2squared/ark-ai/actions/runs/42068297557) **FAILED on Ruff before pytest**: F821 leftover `captured` in the veto hook and E501 a too-long expectation. Preserving fixes were committed as `6781f50873c876cca6309abf58aef24a687dfee4` and `ea3860fb807da1dc5ab2ebd6c21c82cb5f456ca3`. No equivalent manual CI re-dispatch.

## Independent non-UI implementation package 1 — ToolRegistry BoundAction constructor/field custody

- `src/ark/agency/registry.py` source commit `18ee678b3479fa5af2c1996418494f3007f7922c`.
- A slotted frozen `BoundAction` can have `registry_revision`, `call`, `registration`, `bound_action_id`, `__new__`, `__getattribute__` or `__getattr__` replaced reflectively. Checking only `__init__` allowed injected code to run before returned bound IDs/registrations were inspected. The existing guard now pins import-original slots/hooks and rejects changes before reading or constructing the bound receipt, including reentrant revision computation. No backend execution is introduced.
- `tests/test_registry_bound_result_preaccess_run638.py` source/test commit `c93a7952daa5bf222309798b018f88738385d9ae`: **9 authored test cases** across field descriptors, inherited hooks, mid-resolution changes and a normal disconnected bound ID. The temporary inherited-hook test restores the **original class dictionary**, not a synthesized class attribute, to prevent contamination; follow-up test fix commit `0d18eff2efe83f4fcf981978844d9713c6da56bd`.
- Scope: local immutable registration identity only. The registry is not an authentication authority or real ToolBackend permission.

## Independent non-UI implementation package 2 — Memory CAS generation first-hash custody

- `src/ark/memory/cas_generation_review.py` source commit `c2c7fd3c5c51a252ff304fc0687040e92a53ecb0`.
- Previously the first `deterministic_memory_id` call happened before the original scope/path epoch was captured; a reentrant hash callback could substitute an equal-valued owner/namespace string or SQLite path, and the diagnostic could adopt the changed carrier as its baseline. The review now captures the first source identities **before** the identity callback and compares immediately afterwards, before opening private SQLite.
- `tests/test_memory_generation_first_identity_hash_run638.py` commit `a7c5ffda31eb19e8bc54e05cecb9f3fd0e939c72`: **7 authored cases**, covering changed and equal-value clone mutations to owner, namespace and path, plus a baseline advisory-only result. They assert private SQLite is never opened after source drift.
- Memory v1 schema and write/CAS operations unchanged; a local diagnostic hash never authenticates a writer, source or consent and does not authorize data erasure.

## Validation, protected boundaries, and caveats

- **Authored**: 16 new regression cases (9 registry + 7 Memory). Preexisting retention cases were repaired/reworked, not counted as new. Neither 16 authored cases nor any intermediate source commit is a claim of pytest PASS.
- Github Actions on each pushed commit is already launched by the existing PR workflow. The most recent full source/test CI must finish Ubuntu+Windows × Python 3.11–3.13 at its **exact** HEAD before stating GREEN. Local Git checkout, Ruff and pytest were **not available** because `github.com` DNS resolution from this runtime failed.
- PR #5 remains Draft/unmerged, Contract 1 frozen; PR #9 remains Draft/unmerged and entirely untouched. All new UI/FRONTEND development remains paused. Existing V1/V2/Local UI/Launcher evidence and protected V2 final evaluation unopened. No paid/external GPU/API, credentials, real Candidate/weight/adapter, actual backend, device actions, human approval, notification, automatic replay, irreversible erasure, promotion or main merge.
- Storage evidence in separate SQLite files is not atomic across databases or independently authenticated; `UNKNOWN` remains manual-only. ARK/JARVIS/V3 overall **NOT_PASSED**.

## Next plan / 今後の方針

1. Read the actual exact-head CI for the final source/test and latest checkpoint; repair any logged failures via the normal guarded Contents API only, preserving earlier refusal/integrity checks.
2. Once the independent registry and Memory work passes exact-head CI, inspect plan recovery status/terminal propagation and audit-before-action/occurrence replay on mock-only paths, without asserting real-world exactly-once semantics.
3. Continue Memory CAS event lineage, privacy-safe Personal Context, proactive/observation fixture contracts and V3 free-only identity/path/provenance checks. Retain all frozen gates and the UI pause.
