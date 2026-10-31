# First controlled experiment precommit — BLOCKED / NOT EXECUTABLE

Contract: [CONTRACT.md](CONTRACT.md), frozen before implementation at
`f1139b151bd1dd372b9d032612c1c4bffc9bb4b8`.
Experiment ID: `v3-format-compliance-001`. No training or candidate results exist.

## Planned fixed design

- Objective: general instruction/output-format compliance, not memorizing math-02.
- Base: Qwen/Qwen3-4B-Instruct-2507 trainable HF weights. Revision/hash: UNRESOLVED.
- Method proposal: LoRA, rank 8, alpha 16, dropout 0, q_proj/v_proj only,
  one epoch, learning rate 0.0001, seed 42, sequence length 256, microbatch 1,
  gradient accumulation 8. These are unexecuted design settings, not proven optimal.
- Data: exactly 120 approved train / 30 approved validation examples, independent
  source/template groups. No real examples are supplied by the test fixtures.
  Targets may cover number, YES/NO, JSON, fraction, symbol and restricted code outputs;
  no V2 question, distinctive answer or scorer-derived example is admitted.
- Validation: one configuration, no hyperparameter sweep. Inspect training loss,
  held-out validation behavior and failures without opening the V2 candidate gate.
- Dataset bytes/SHA, base files/SHA, tokenizer, dependency lock, hardware identity,
  exact export command/source revision: UNRESOLVED; real execution remains blocked.
- Candidate output: a NEW isolated run directory, with separate adapter and export
  paths. Never overwrite `models/Qwen_Qwen3-4B-Instruct-2507-Q4_K_M.gguf`.
- Rollback: original GGUF/config remain unchanged. Keep every candidate/rejected
  artifact and provenance manifest; no automatic replacement, cleanup or deletion.
- Reproducibility: capture config/code/dataset/base/artifact SHA, seed, dependencies,
  hardware, start/end, steps, epochs, trainable parameters, losses, wall time,
  peak RAM/VRAM and failures. Bitwise identity is not promised across hardware.

## Frozen evaluation budget

After an artifact is frozen, STOP for permission before the first candidate V2 opening.
Exactly two fresh-process current runs and two candidate runs, same frozen V2 suite,
scorer/policy/runtime/settings/export quantization. These are future runs, not four
runs claimed to exist. Preserve the original V2 baseline unchanged as historical evidence.
Do not use results for subsequent tuning. Any opening failure is recorded; another
candidate or retries require a new precommit and explicit approval.

Current/candidate identity intentionally differs; all other comparison conditions
must agree. Eligible only if repeated outcomes agree, no runtime/memory failures,
no task regressions, at least one improvement, complete provenance and no contamination
suspicion. Eligibility does not authorize promotion. Real decision is another STOP.

## Execution authorization record

Status: **PENDING HUMAN REVIEW / REQUIRED IDENTITIES UNRESOLVED**.
This document freezes an experiment design, not permission to run it. Complete the
missing identities and executable recipe in a reviewed supplement before training.
Changing Contract 1 itself requires stopping and user direction, not silent edits.
