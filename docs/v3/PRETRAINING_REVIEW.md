# V3 pre-training review integration

Status: **PRE-TRAINING / NO REAL TRAINING AUTHORIZED**.

This supplement records the post-infrastructure technical review before any real weights, adapters, candidate evaluation, or frozen V2 opening. It does not replace or silently amend `CONTRACT.md`.

## Current facts

- V1 and V2 are OFFICIAL PASS; V2 fixed suite/scorer/policy remain immutable.
- Local UI v1 and Launcher/Gate Runner were completed later on main and are outside V3 learning semantics.
- V3 PR #5 still contains no real trainer execution, adapter, candidate weights, or candidate V2 result.
- First experiment `v3-format-compliance-001` remains blocked until exact execution identities are frozen.

## Independent-review decision matrix

### ACCEPT

- Keep Current and Candidate artifacts strictly separated.
- Keep automatic promotion forbidden; `PROMOTION_ELIGIBLE` remains only a human-reviewed recommendation.
- Keep V2 frozen cases out of training and validation data.
- Separate development/training feedback from final frozen evaluation.
- Strengthen semantic/paraphrase contamination review beyond exact normalized duplicate checks.
- Measure candidate pre-export versus deployed Q4_K_M behavior separately where technically comparable; do not call cross-backend differences pure quantization loss.
- Add category-level regression monitoring so format compliance cannot hide damage to context, coding, structured output, reasoning, or runtime stability.
- Treat a small-model run, if used, only as infrastructure/toolchain validation; it is not evidence that 4B learning efficacy or hyperparameters transfer.

### MODIFY

- An extended V3 evaluation set is useful, but `50 questions` is not a fixed requirement. Size must follow scorer reliability, category coverage and an explicit sampling rationale.
- LoRA is a leading first-method candidate, but LoRA versus QLoRA must be decided from the pinned training stack, precision, sequence length, GPU memory and export path rather than preference alone.
- Dataset sizes such as 5k/20k and fixed epoch counts are examples, not requirements. The first experiment should remain the smallest credible controlled demonstration unless a reviewed amendment justifies expansion.
- GPU class, provider, duration and cost are feasibility outputs, not Completion Contract constants.
- Hyperparameter search must use Development/Validation only. Final frozen V2 outcomes may never guide tuning.

### REJECT

- Do not open a final frozen suite, inspect its score, then continue tuning the same candidate lineage while still calling the suite untouched.
- Do not compare candidate pre-quantization precision directly against the historical Current Q4_K_M and label the difference a learning gain.
- Do not assume a small model's best rank/LR transfers to Qwen3-4B.
- Do not train the existing inference GGUF. Training lineage begins from exact trainable Qwen HF weights/tokenizer revision.
- Do not auto-adopt synthetic data, private chat logs, personal memory, benchmark-derived examples or scorer-aware examples.

## Required pre-training closures

Before crossing the existing training STOP, freeze a reviewed execution supplement containing all of the following:

1. Exact Qwen3-4B-Instruct-2507 trainable base revision and file SHA manifest.
2. Exact tokenizer/chat-template identity.
3. Approved dataset bytes, provenance, train/validation split, group independence and SHA-256.
4. Semantic-contamination audit method, limitations and human review record.
5. Training stack manifest: OS, Python, torch, transformers, PEFT, accelerate, CUDA/runtime, optional bitsandbytes, GPU, seed.
6. Method decision (LoRA/QLoRA), exact target modules and hyperparameters, with rationale.
7. Maximum training/search budget and stopping criteria fixed before results.
8. Adapter save/merge/export recipe pinned to exact tool revisions.
9. V3 paired baseline/candidate conversion and Q4_K_M quantization procedure; historical V2 artifact remains immutable.
10. Development/Validation evaluation architecture and critical-category regression blockers.
11. Final frozen evaluation opening policy that forbids score-guided retuning.
12. Storage, privacy and external-compute handling; no personal data in the first experiment.

## Quantization parity policy

Prefer a V3 comparison-only baseline regenerated from the same exact trainable base revision using the same converter/quantizer revision and settings as the Candidate. This new paired baseline never replaces the historical V2 frozen GGUF. If exact parity cannot be reproduced, record the confound and weaken claims rather than hiding it.

For the Candidate, a pre-export versus Q4_K_M delta may be measured on non-frozen validation material when the runtimes are comparable. If runtime/backend differs, record the observed delta without attributing it solely to quantization.

## Evaluation architecture

- **Development:** debugging, training progress and any precommitted model-selection signal; reusable and never final evidence.
- **Validation:** independent groups, overfitting/stopping and regression monitoring; not training examples.
- **Final Frozen:** sealed before training/tuning, opened only for the precommitted final comparison. If its result influences another training iteration, that suite is no longer untouched for that lineage.
- **Historical V2 12-case suite:** immutable baseline evidence and final regression reference; never training/validation material.

Categories to cover before choosing suite size: strict output format, conversation, context, correction/update handling, math, reasoning, coding, JSON/structured output, uncertainty/missing information, and longer multi-turn behavior where feasible.

## Branch integration note

V3 currently diverges from main because Local UI v1 and Launcher/Gate Runner were merged after V3 branched from the V2 freeze. Before any executable training work, main must be integrated into the V3 branch without altering V1/V2/Local UI/Usability freezes or V3 learning semantics. Any merge conflict affecting V3 contract, evaluation, config semantics or runtime is a STOP for review.

## Next independent review

Before authorizing real training, send the concrete execution supplement—not generic roadmap text—to an independent reviewer (Claude requested by the project owner). Ask the reviewer to challenge base identity, dataset independence, LoRA/QLoRA choice, hardware feasibility, export/quantization parity, evaluation leakage and promotion logic. Review feedback must be classified ACCEPT/MODIFY/REJECT before the supplement is frozen.
