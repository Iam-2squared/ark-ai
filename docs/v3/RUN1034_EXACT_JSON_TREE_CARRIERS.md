# Run1034 — exact JSON carriers at the V3 execution-snapshot boundary

## Finding

The V3 execution validator accepted an exact top-level dictionary but used `isinstance` for nested sections and string fields. An in-memory dictionary/list/string subclass could therefore execute caller-defined methods during policy comparison or section access. In particular, a `str` subclass could override equality and impersonate the frozen experiment identifier.

The file loader returns ordinary JSON primitives, but `validate_experiment_001` is also a public in-memory boundary and must not rely on callers having used that loader.

## Change

- Validate the complete input as an exact built-in JSON tree before section access or policy comparison.
- Reject nested dict/list/string/numeric subclasses, non-finite floats, invalid UTF-8 strings/keys, excessive nesting and shared mutable containers.
- Require exact nested section dictionaries and exact built-in text carriers for digest, commit and runtime identity checks.
- Add regressions proving hostile equality, mapping and list callbacks are rejected before execution, plus shared-container alias rejection.

The frozen experiment values, authorization scopes, run counts, dataset sizes, V3 Contract 1 and pre-paid-compute gate are unchanged. This is carrier validation only.

## Evidence and limits

Synthetic in-memory snapshots only. No model/tokenizer load, converter, quantizer, subprocess, GPU, training, Candidate, protected V2 evaluation, paid service, external compute, credential, promotion, or main merge is invoked. PR #5 remains Draft/unmerged. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.

**Work basis:** gated Draft PR #5 exact HEAD `29c6bc2f64a6f7a5c6960a1d109c719aa023ed7c`.
**Source/test branch:** `research/v3-exact-json-tree-run1034`.
