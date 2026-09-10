# V3 first real experiment — execution supplement

Status: **DRAFT / REAL TRAINING BLOCKED**.

This document operationalizes Contract 1 without changing it. Contract 1 remains byte-for-byte frozen and its recorded SHA remains authoritative. No real training, adapter generation, external compute use, candidate frozen evaluation, promotion decision, or main merge is authorized by this supplement.

## Independent review disposition

The Claude pre-training review was considered critically rather than adopted wholesale.

### Accepted
- Prefer an off-device GPU environment for the first 4B real-training path; local Windows CPU remains inference/governance unless a separate feasibility pilot is approved.
- Separate Development/Validation feedback from the final frozen V2 opening.
- Strengthen semantic/paraphrase and template/source-family contamination review.
- Keep pipeline completion distinct from candidate promotion.
- Add category-level regression review beyond the small historical V2 suite.
- Use a paired Q4_K_M comparison baseline regenerated from the exact trainable base with the same converter/quantizer revision where possible.

### Modified
- `CPU training is impossible` is not accepted as a proven fact; it is simply not the approved first 4B route because feasibility/time/memory are unmeasured.
- LoRA is the first-method proposal, not an intrinsic requirement. QLoRA may replace it only if the pinned environment/VRAM feasibility requires that decision before execution.
- Provider/GPU model/prices are not frozen from stale estimates. Exact hardware and cost ceiling are execution identities to be approved before use.
- Validation/domain thresholds must be precommitted with scorer and sample-size rationale; they cannot be adjusted after seeing final results.

### Rejected for experiment 001
- Changing 120 train / 30 validation to 50/20/40 without a Contract amendment.
- Hyperparameter sweeps or 18-run searches: Contract 1 fixes one configuration/no validation-driven sweep for experiment 001.
- Changing q_proj/v_proj or rank/LR after seeing experiment-001 final results while treating the same frozen suite as untouched.
- Calling Candidate pre-export minus historical Current Q4_K_M a pure training effect.
- Replacing the Contract's two fresh Current + two fresh Candidate V2 runs with a single run.

## Experiment 001 fixed semantic design

Unless Contract 1 is explicitly amended before any result exists:
- objective: independent output-format/instruction compliance, not `math-02` memorization;
- dataset: exactly 120 approved train + 30 approved validation examples;
- source/template groups may not cross splits;
- method proposal: LoRA, rank 8, alpha 16, dropout 0, q_proj/v_proj;
- one epoch, LR 1e-4, seed 42, sequence length 256, microbatch 1, gradient accumulation 8;
- one configuration, no hyperparameter sweep;
- V2 cases/targets/scorer-derived material remain forbidden from train/validation.

These settings are a controlled precommit, not claimed optimums.

## Required identities — all must close before training

| Identity | Required evidence | State |
|---|---|---|
| Base model | exact Qwen/Qwen3-4B-Instruct-2507 revision + per-file SHA-256 manifest | UNRESOLVED |
| Tokenizer/template | exact files/revision/SHA + chat-template identity | UNRESOLVED |
| Dataset | canonical 120/30 bytes, SHA, provenance, approvals, group audit | UNRESOLVED |
| Contamination | exact/fuzzy + semantic/paraphrase review method, report, limitations, human attestation | UNRESOLVED |
| Training stack | OS/container, Python, torch, transformers, PEFT, accelerate, CUDA/runtime, optional bitsandbytes | UNRESOLVED |
| Hardware | exact GPU/device, VRAM, driver/runtime, measured smoke feasibility | UNRESOLVED |
| Method | LoRA or justified QLoRA; exact config matching the precommit/approved amendment | UNRESOLVED |
| Budget | explicit monetary ceiling, maximum real runs, timeout/stop policy | UNRESOLVED |
| Training recipe | exact executable entry point/config/code SHA; no ad-hoc notebook-only state | UNRESOLVED |
| Adapter/export | save, reload, merge, HF-to-GGUF and Q4_K_M procedure pinned to revisions | UNRESOLVED |
| Paired baseline | same trainable base + same converter/quantizer revision/settings as Candidate | UNRESOLVED |
| Evaluation | Development/Validation scorer + category blockers; V2 2+2 opening remains sealed | UNRESOLVED |
| Storage/privacy | persistent artifact/log location; no private sessions/personal data; retention rule | UNRESOLVED |

Any UNRESOLVED row blocks real training.

## Dataset and contamination contract implementation

The 120/30 artifact must preserve the existing deterministic dataset builder rules. Add an independent audit report before approval:

1. exact normalized duplicate/conflict/source-reference checks;
2. fuzzy lexical similarity review against the read-only frozen denylist;
3. semantic/paraphrase candidate detection using a separately pinned detector, with threshold calibration recorded as a heuristic rather than proof;
4. manual review of every flagged pair and a documented sample of non-flagged examples;
5. source/template-family group separation across train/validation;
6. provenance/rights/independence attestation for every accepted example;
7. no scorer code, V2 expected-answer-derived template, private chat, personal memory, or unattributed/licensing-unclear text in training payloads.

The semantic detector is an audit tool only and must never expose frozen expected answers or scorer internals to the trainer.

## Evaluation architecture

### Development
Training loss and non-frozen diagnostic material may be used to verify mechanics. Experiment 001 does not use a hyperparameter sweep. Development observations cannot authorize opening V2.

### Validation
The 30 frozen validation examples are independent source/template groups and may be evaluated before V2. Report strict format correctness and category results. Current and Candidate must both be scored with the same validation scorer/runtime contract where technically comparable. Thresholds and category blockers must be fixed before training; no post-result threshold relaxation.

### Historical V2 final regression opening
After Candidate artifact + provenance are frozen, STOP for explicit authorization. Then execute exactly the Contract budget: two fresh-process Current runs and two fresh-process Candidate runs with the immutable V2 suite/scorer/policy and matched runtime/settings/export quantization. Previously passing task -> Candidate FAIL is a promotion blocker. Runtime/memory failure is a blocker. Outcomes cannot guide retuning experiment 001.

## Quantization/export fairness

Primary deployment comparison is paired Q4_K_M vs paired Q4_K_M using:
- same exact trainable base lineage;
- same pinned HF-to-GGUF converter revision;
- same pinned quantizer binary/revision and Q4_K_M settings;
- same ARK runtime/config/scorer.

The historical V2 Current GGUF remains immutable evidence and is not replaced by the paired comparison baseline.

Candidate pre-export vs Candidate Q4_K_M may be measured on non-V2 validation material. If precision, runtime, backend, prompt rendering, tokenizer, or generation settings differ, report the observed delta as confounded; do not label it pure quantization loss.

## Completion versus promotion

### V3 pipeline completion
May PASS even when the real Candidate is rejected, but only if the approved independent dataset, real controlled training, real Candidate artifact, export/compatibility verification, paired evaluation, V2 regression review, reproducibility evidence, human review, tests and CI are complete.

### Candidate promotion eligibility
Requires all stricter Contract conditions: complete provenance/no contamination suspicion, zero runtime/memory failures, no previously passing V2 task regression, at least one previously failing task improvement, repeat consistency, and no uncontrolled comparison differences. `PROMOTION_ELIGIBLE` never replaces human authorization.

## Training authorization boundary

Before the first real training command, all identity rows above must be resolved, this supplement must receive an independent review disposition, and an immutable execution snapshot/hash must be recorded. Crossing that boundary requires explicit user authorization because it creates real weights/adapters and may incur external-compute cost.
