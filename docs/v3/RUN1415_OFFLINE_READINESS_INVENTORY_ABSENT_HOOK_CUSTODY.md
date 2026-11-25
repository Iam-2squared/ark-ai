# Run1415 — V3 passive readiness inventory absent-hook custody

## Exact basis

- Parent: gated Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent work-basis HEAD: `2c3501930baff61f04b25e7e02c00b0241a426e7`.
- Child branch: `research/run1415-v3-readiness-inventory-absent-hook-20261125`.
- Source: `src/ark/learning/offline_readiness_inventory.py`.
- Regression test: `tests/v3/test_offline_readiness_inventory_absent_hook_custody_run1415.py`.

## Finding and correction

The passive V3 readiness inventory stored `__new__`, `__getattribute__` and `__getattr__` hook values with `vars(type).get(name)`. For a missing hook this records `None`, so an explicit `None` class member was indistinguishable from true namespace absence. The result carrier's type/field/hook vectors were also not retained in one validator epoch.

The correction introduces a unique absence sentinel and one import-time epoch covering the exact result type, field/hook/pinned-name vectors, original descriptor/denial vectors and sentinel. The validator checks epoch and alias identity before reading the class namespace, then requires non-membership for absent hooks and exact descriptor identity for present members.

## Regression coverage

- Explicit `None` and exact-sentinel installation for each absent class hook.
- Sentinel rebinding, equal-valued vector replacement and epoch replacement.
- Joint replacement of the public/private result type aliases.
- All special class-slot mutation probes run in an isolated subprocess.

## Free-only and evidence boundaries

This module remains a passive placeholder inventory over a synthetic execution snapshot. It does not authorize preflight, external compute, real training, protected V2 evaluation, export, Candidate generation or promotion. No preflight, training, model load, tokenizer load, GPU query or external service was invoked. Dataset/provenance/contamination policy, Contract 1, execution snapshot schema and all frozen contracts are unchanged.

No paid/external compute/service, credentials/account connection, hardware action, destructive operation, main write/merge or UI/frontend work occurred. PR #5 remains Draft/unmerged; PR #8/#9 remain Draft/unmerged and PR #9 remains untouched.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff result, V3 PASS, training success or Candidate evidence is claimed.