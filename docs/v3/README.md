# V3 Learning & Evaluation — infrastructure only

V1/V2 remain OFFICIAL PASS. V3 is NOT_PASSED and its PR stays Draft/unmerged.
[Frozen contract](CONTRACT.md) / [training feasibility](FEASIBILITY.md) /
[blocked first-experiment precommit](FIRST_EXPERIMENT.md).

## Implemented

- LearningCandidate schema, explicit human/rights/independence provenance checks.
- Deterministic canonical dataset bytes/SHA, rejected reasons/counts, normalized
  input deduplication, conflict rejection and grouped train/validation separation.
- Read-only frozen-evaluation screening. Lexical checks are heuristics, not proof;
  human independence review remains mandatory. Short common labels alone do not
  identify leakage. Denylist and scoring code are not included in training payloads.
- TrainingBackend/Config/Run/Artifact boundaries. Mock outputs a NON-MODEL receipt.
  Real backend stops before any weight generation or resource use.
- Create-only run directory, append-only candidate registry snapshots with hash chain,
  lineage and artifact hash validation. This is local integrity checking, not a secure
  multi-user database; an attacker controlling all records can rewrite the entire chain.
- Frozen promotion-policy simulation: real evidence immediately stops. No candidate
  frozen-evaluation invocation and no real promotion decision are implemented here.

The future real evaluation harness reuses V2 reports and comparison, but needs a
reviewed lineage-aware adapter: the current V2 comparator treats model identity changes
as uncontrolled. Do not pretend a same-model self-comparison tests a trained candidate.
The simulation tests the policy without opening V2 questions to a candidate model.

## Validation

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest
```

No CLI triggers real training, downloads weights, contacts cloud APIs, changes current
model configuration or promotes artifacts. No added runtime dependencies.
Tests contain synthetic approval fields for interface simulation, not real approved
training examples. V1/V2 original-evidence tests and mock comparison remain in CI.
CI tests have already-observed V2 fixtures; that is not a new candidate evaluation opening.

## Still incomplete / explicit stops

Real dataset approval and hashes, base weights pinning, training hardware selection,
exact training/export recipe, real trainer, candidate export, real comparison and
human review are incomplete. V3 cannot PASS on this infrastructure alone.
Stop before real training, external compute, model/adapter generation, first candidate
evaluation, real promotion decision, main merge, or changing the frozen contract.
No V4–V10 work is included.
