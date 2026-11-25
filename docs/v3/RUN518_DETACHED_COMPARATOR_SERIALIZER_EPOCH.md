# Run518 — validation-only comparator callback after-serialization custody

**Scope:** deterministic, in-memory synthetic V3 paired validation only.
No model, HF remote revision, paid/external GPU, Candidate generation, V2
final evaluation opening, promotion, training approval or execution grant.

## Exact implementation

- Source `src/ark/learning/detached_comparison_recheck.py`
  update `df088a7db18eb62cf122c5df086fe3b7987f0ab9`
  (blob `59c824dd4287998ec15b52c04a7a1784afb20fb6`).
- New `tests/v3/test_detached_comparison_serializer_epoch_run518.py`
  commit `173ac6ac0033aa8ff06165b11fe0525c6134c833`.
- **7 authored pytest cases**: five mutations of the callback's actual
  comparison tree while serializing the independently rederived expected
  tree (protected-V2 flag, promotion label, failure count, category count,
  regression list); one mutation *after* actual serialization; and one stable
  no-authority control.

Earlier the verifier checked the callback's actual dict against independently
recomputed expected semantics, then serialized **only the expected tree** to
match caller-retained bytes/hash. A reentrant serializer could mutate the
already-inspected callback tree, after the initial comparison check, without
invalidating that expected-byte check. The new read-only guard serializes
the **actual callback result too**, requires it to match the same independently
retained canonical bytes, and rechecks exact JSON shapes and no-promotion /
no-protected-V2-opening flags after both serializer callbacks. The caller's
existing 30-case, exact-type and text/byte budgets remain in force.

The two SHA-256 and shape comparisons are **consistency checks**, not proof of
model identity, source data provenance, external custody, human consent,
protected evaluation opening, training or model improvement. There is no
Candidate adapter or actual weight generation.

## CI / current gate

- PR #5 source/test exact HEAD `173ac6ac0033aa8ff06165b11fe0525c6134c833`:
  [CI run 41266374008](https://github.com/Iam-2squared/ark-ai/actions/runs/41266374008)
  **6/6 GREEN** on Ubuntu/Windows Python 3.11–3.13.
- Earlier source-only HEAD `df088a7db18eb62cf122c5df086fe3b7987f0ab9`:
  [CI 41266353643](https://github.com/Iam-2squared/ark-ai/actions/runs/41266353643)
  SUCCESS, but does not alone cover the new tests.
- Independent local pytest/Ruff, real model comparison, actual human-approved
  data/contamination review, local HF weight hashes and GPU/driver attestations:
  **NOT PERFORMED**.

PR #5 remains **Draft/unmerged, V3 NOT_PASSED**, with frozen Experiment 001
contract and V1/V2/Local UI/Launcher evidence untouched. The immutable HF
revision and file hashes, approved dataset, pinned runtime and explicit
spend/compute controls are unresolved. Future work may expand detached
reproducibility checks only, never cross the paid or protected gate without
explicit authorization.
