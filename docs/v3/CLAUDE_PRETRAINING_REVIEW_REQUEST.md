# ARK AI V3 — Claude pre-training independent review request

Please review the concrete pre-training design below as an independent technical reviewer. Do not optimize for agreement. Identify invalid assumptions, hidden leakage, reproducibility gaps and cheaper/safer alternatives. No real training or candidate frozen evaluation has occurred yet.

## Fixed project state

- Runtime target: Windows 11, CPU-only i5-class PC, 16 GiB RAM.
- Current inference model: Qwen3-4B-Instruct-2507 Q4_K_M GGUF through llama.cpp / llama-cpp-python.
- V1 Local Core: OFFICIAL PASS.
- V2 ARK Intelligence: OFFICIAL PASS; fixed 12-case real-model evaluation is 11/12 in two runs, runtime failures 0. Known `math-02` is mathematically correct but fails strict output-format scoring. Fixture/scorer/policy are immutable.
- Local UI v1 and Launcher/Gate Runner are OFFICIAL PASS and do not change V3 learning semantics.
- V3 infrastructure exists only as a Draft PR. It includes provenance/approval schemas, deterministic dataset export/hashing, dedup/conflict/group-split checks, contamination guard, TrainingBackend abstraction with non-model mock, append-only candidate registry, artifact hashing and fail-closed promotion simulation.
- No real training, adapter, candidate weights, candidate V2 result, automatic promotion or current-model replacement exists.

## Existing frozen V3 principles

1. Current and Candidate are isolated.
2. Training never overwrites the current GGUF.
3. V2 frozen cases/targets/scorer-derived examples are forbidden from training/validation.
4. Candidate promotion is separate from V3 pipeline completion and requires human authorization.
5. A rejected real candidate may still demonstrate that the learning/evaluation pipeline works.
6. Exact base/dataset/config/dependency/hardware/export identities must be frozen before real training.
7. After candidate artifact freeze, frozen V2 evaluation has a precommitted opening budget; its results cannot be used for retuning the same experiment.

## Current first-experiment proposal — NOT YET AUTHORIZED

Experiment ID: `v3-format-compliance-001`.
Objective: general instruction/output-format compliance, not memorizing `math-02`.

Current proposal in the repo:
- trainable base: Qwen/Qwen3-4B-Instruct-2507 HF weights; exact revision/hash unresolved
- method proposal: LoRA
- rank 8, alpha 16, dropout 0
- q_proj/v_proj targets
- one epoch
- LR 1e-4
- seed 42
- sequence length 256
- microbatch 1, gradient accumulation 8
- exactly 120 approved train / 30 approved validation examples
- no hyperparameter sweep in the first experiment

These numbers were frozen as an unexecuted precommit proposal, not demonstrated optimums. Dataset bytes, base/tokenizer hashes, dependency lock, hardware identity and exact export recipe remain unresolved.

## Post-review direction currently favored

We currently intend to keep the original Contract intact unless a pre-training amendment is justified, and add a reviewed execution supplement before training.

The supplement would close:
- exact trainable base revision + SHA manifest
- tokenizer/chat-template identity
- actual approved dataset + SHA/provenance/group independence
- semantic/paraphrase contamination audit + human sample review
- exact training environment manifest
- LoRA versus QLoRA decision from measured feasibility rather than preference
- fixed compute/search budget and stopping criteria
- adapter save/merge/export recipe pinned to tool revisions
- paired baseline/candidate GGUF conversion and Q4_K_M quantization procedure
- Development / Validation / Final Frozen evaluation separation
- critical category regression blockers
- privacy/external-compute rules

### Evaluation policy

Development may be reused for debugging/training progress. Validation is independent and may drive stopping/model selection. Final Frozen is sealed before tuning and is used only for final comparison. If a final score influences another training iteration, that suite is no longer called untouched for that lineage.

The historical V2 12-case suite remains immutable and is never training/validation data.

### Quantization policy

Prefer a V3 comparison-only Current baseline regenerated from the same exact trainable base revision with the same converter/quantizer revision/settings as the Candidate. This paired baseline does not replace historical V2 evidence.

Candidate pre-export versus Q4_K_M behavior may be measured on non-frozen validation data. If runtime/backend differs, the delta is not claimed to be pure quantization loss.

### Small-model policy

If a smaller model is used, its only claim is end-to-end toolchain/infrastructure validation. Its learning gain or best hyperparameters do not transfer as evidence to Qwen3-4B.

## Questions requiring your independent judgment

Please answer in this order.

### A. Critical flaws
List any issue that should block real training even if the rest of the plan is implemented.

### B. Existing 120/30 + rank-8 LoRA proposal
Choose one: KEEP, MODIFY, or REPLACE. Explain whether 120/30 is credible for a first pipeline demonstration, whether the format-compliance objective is too narrow, and whether rank 8 / q_proj+v_proj / LR 1e-4 / one epoch is a defensible single-shot starting configuration.

### C. LoRA versus QLoRA
For Qwen3-4B-Instruct-2507, specify what measurements or environment facts should decide this. Do not assume a cloud GPU class without deriving it from precision, sequence length, microbatch, activation/checkpointing and optimizer choices.

### D. Dataset and contamination
Propose the smallest credible dataset design for a first controlled experiment. Address semantic/paraphrase leakage, template-family split leakage, synthetic-data provenance, scorer-aware leakage and independence from the V2 frozen suite.

### E. Evaluation architecture
Recommend Development/Validation/Final Frozen category coverage and sample-size reasoning. Do not pick an arbitrary round number without explaining what uncertainty/coverage it buys.

### F. Quantization/export fairness
Audit the proposed paired-baseline design. Explain how to distinguish training effect, export effect, quantization effect and backend/runtime differences without making unsupported causal claims.

### G. Hardware and cost
Given a 4B model and a personal project with CPU-only 16 GiB local runtime, recommend a minimum-cost training feasibility path. Give ranges and assumptions, not stale provider-specific prices. State when a small-model smoke run is worth doing.

### H. Promotion and catastrophic forgetting
Recommend precommitted blockers for runtime failures and regressions in context, coding, reasoning, JSON/structured output and general instruction following. Separate V3 pipeline-completion criteria from Candidate promotion criteria.

### I. Final recommendation
State exactly what you would freeze before the first real training run, what you would leave adjustable on Development/Validation, and the single next action you would take if you were technical lead.

Please explicitly flag any recommendation that conflicts with the already-frozen Contract rather than silently rewriting it.
