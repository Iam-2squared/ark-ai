# V3 Learning & Evaluation — pre-training closure

V1/V2 remain OFFICIAL PASS. Local UI v1 and Launcher/Gate Runner are also frozen on main. V3 is **NOT_PASSED** and PR #5 stays Draft/unmerged.

Core documents:
- [Frozen Contract 1](CONTRACT.md)
- [Training feasibility audit](FEASIBILITY.md)
- [Blocked first-experiment precommit](FIRST_EXPERIMENT.md)
- [Independent-review integration](PRETRAINING_REVIEW.md)
- [Experiment-001 execution supplement](EXECUTION_SUPPLEMENT.md)
- [Fail-closed execution snapshot template](EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json)

## Implemented infrastructure

- LearningCandidate schema with explicit human/rights/independence provenance checks.
- Deterministic canonical dataset bytes/SHA, rejected reasons/counts, normalized input deduplication, conflict rejection and grouped train/validation separation.
- Read-only frozen-evaluation screening. Lexical checks are heuristics, not proof; human independence review remains mandatory.
- TrainingBackend/Config/Run/Artifact boundaries. Mock outputs a NON-MODEL receipt. Real backend stops before weight generation or resource use.
- Create-only run directory, append-only candidate registry snapshots with hash chain, lineage and artifact hash validation.
- Frozen promotion-policy simulation: real evidence immediately stops. No real candidate frozen-evaluation invocation or real promotion decision is implemented.

## Pre-training design closure

The execution supplement now fixes, without amending Contract 1:
- experiment-001 120/30 single-config semantics;
- exact evidence required for base/tokenizer identity;
- dataset provenance and contamination audit protocol;
- off-device-GPU-first feasibility/preflight policy;
- LoRA decision boundary and no silent QLoRA substitution;
- one-full-Candidate-run budget semantics;
- repository-owned reproducible training recipe requirements;
- adapter/merge/export/paired-Q4 lineage;
- Validation versus historical V2 final-opening separation;
- category/runtime regression blockers;
- privacy, storage and evidence-retention rules.

External identities are deliberately not fabricated. Exact HF revision/file hashes, actual 120/30 dataset hash, GPU/environment versions, monetary/time ceiling, executable real trainer/evaluator, and pinned llama.cpp export identities remain pending evidence.

## Validation

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest
```

No CLI currently authorizes real training, downloads weights, contacts cloud APIs, changes Current model configuration or promotes artifacts. V1/V2 original-evidence tests and mock comparison remain in CI.

## Hard stops

Stop before external compute/spending, real training or adapter/weight generation, first Candidate V2 evaluation, real promotion decision, Contract changes or main merge. Before real training, populate and independently review the execution snapshot, prove non-Candidate preflight feasibility, freeze all exact identities, then obtain explicit user authorization.
