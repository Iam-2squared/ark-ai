# V3 Learning & Evaluation — pre-training closure

V1/V2 remain OFFICIAL PASS. Local UI v1 and Launcher/Gate Runner are also frozen on main.
V3 is **NOT_PASSED** and PR #5 stays Draft/unmerged. Contract 1 remains byte-for-byte frozen.

Core documents:
- [Frozen Contract 1](CONTRACT.md)
- [Training feasibility audit](FEASIBILITY.md)
- [Blocked first-experiment precommit](FIRST_EXPERIMENT.md)
- [Independent-review integration](PRETRAINING_REVIEW.md)
- [Experiment-001 execution supplement](EXECUTION_SUPPLEMENT.md)
- [Fail-closed execution snapshot template](EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json)
- [Pre-paid-compute gate](PRE_PAID_COMPUTE_GATE.md)
- [Hugging Face identity review](HF_IDENTITY_REVIEW.md)

## Implemented infrastructure

- LearningCandidate schema with explicit human/rights/independence provenance checks.
- Deterministic canonical dataset bytes/SHA, normalized-input deduplication, conflict rejection
  and grouped train/validation separation.
- Read-only frozen-evaluation screening plus deterministic human-review queue generation.
  Lexical checks are heuristics, not proof; human independence review remains mandatory.
- Dataset freeze now retains the exact reviewed queue and canonical reviewer-decision artifact.
  Their hashes are chained into the contamination report and create-only evidence manifest.
- Offline `ark-v3-identity` capture for already-materialized HF base/tokenizer bytes, chat-template
  probe, V3 runtime source tree, and pinned llama.cpp converter/quantizer files. It does not
  download models or contact external services.
- Strict experiment-001 execution-snapshot validation, runtime code-tree identity, measured
  environment/hardware checks, numeric safety checks and wall-clock timeout enforcement.
- Separate preflight and full-training authorization scopes plus a hash-addressed authorization
  packet; preflight evidence is bound to the immutable execution core before full training.
- Local-files-only HF/PEFT LoRA implementation for the frozen 120/30 recipe. Heavy model work
  remains unreachable until all snapshot/evidence/authorization gates pass.
- Preflight performs mechanics-only load/forward/backward/optimizer validation and saves no
  Candidate. Full training remains exactly one separately authorized Candidate run.
- Candidate/export lineage manifests and a deterministic paired Current/Candidate Q4_K_M export
  plan using pinned tool identities.
- Validation-only paired comparison that cannot open historical V2 or authorize promotion.
- Create-only run directory, append-only candidate registry snapshots with hash chain, lineage
  and artifact-hash validation.
- Frozen promotion-policy simulation only; real promotion still requires a later human decision.

## Pre-training design closure

The execution supplement fixes, without amending Contract 1:
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

External identities are deliberately not fabricated. The remaining concrete evidence before any
external compute is the immutable HF revision plus materialized base/tokenizer hashes and
chat-template probe, the real human-approved 120/30 dataset and contamination decisions, exact
Linux/Python/torch/transformers/PEFT/accelerate/CUDA pins, exact llama.cpp revision/converter/
quantizer identities, approved GPU/device/VRAM/driver, user-approved JPY ceiling and timeout,
provider-side billing/cost-cap evidence, and GREEN CI on the final preflight-authorizable head.

## Validation

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest
ark-v3-dataset --help
ark-v3-identity --help
ark-v3-auth-packet --help
ark-v3-run --help
```

No command by itself authorizes external compute, V2 opening, promotion, or Current replacement.
The identity and dataset commands are offline/create-only. Training remains fail-closed unless the
required execution identities and explicit authorization state are present.

## Hard stops

Stop before external compute/spending, real training or adapter/weight generation, first Candidate
V2 evaluation, real promotion decision, Contract changes or main merge. Before real training,
populate and independently review the execution snapshot, prove non-Candidate preflight
feasibility, freeze all exact identities, then obtain explicit user authorization.
