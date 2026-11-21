# Run1035 — exact native path carriers for V3 identity capture

## Scope and exact work basis

- Parent: gated Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent HEAD: `a3c4e7aea4f754a07c74e93c620ce30a65679504`.
- Source: `src/ark/learning/identity.py`.
- Regression: `tests/v3/test_identity_exact_path_carriers_run1035.py`.
- This is a free validation-only guard. It does not invoke identity capture on real model/tool bytes, preflight, training, export, Candidate generation, or any GPU/backend.

## Finding

The identity helpers accepted values annotated as `Path` but normalized them with `Path(value)`. That conversion may invoke a caller-defined `__fspath__` on a custom PathLike or pathlib subclass before the identity code inspects the target. The callback can execute caller code or redirect the selected path before the local byte-identity checks begin.

## Change

Require the exact platform-native concrete `Path` type at each public identity input boundary, before filesystem access or path normalization. The same guard is retained at the snapshot enumeration boundary. Ordinary `Path` values from the CLI and internal callers remain supported.

Adversarial synthetic tests verify custom PathLike and pathlib-subclass `__fspath__` callbacks are not invoked for file, directory, code-tree, HF snapshot, probe, or tool identity inputs.

## Limits

This blocks callback-capable path carriers at the Python API boundary. It does not provide dirfd-based atomic traversal, defeat a hostile OS writer, authenticate a Hugging Face revision, or establish independent custody. Existing symlink/reparse and before/after epoch checks remain unchanged. V3 Contract 1, dataset/provenance evidence, and the protected evaluation gate remain unchanged.

## Validation

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. PR #5 remains OPEN/DRAFT/UNMERGED and no paid compute, paid API, subscription, purchase, credential, preflight, Candidate, protected V2 evaluation, promotion, or main merge is authorized.
