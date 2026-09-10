# V3 Experiment 001 — Pre-Paid-Compute Gate

Status: **IMPLEMENTATION ADVANCED / NO EXTERNAL COMPUTE / NO SPEND / NO REAL TRAINING**.

This gate defines the furthest point the project may reach without purchasing or starting external GPU compute. It does not authorize cloud resources, adapters, Candidate weights, V2 opening, promotion, or main merge.

## Completed before paid/external compute

- Current main integrated into V3 branch; Contract 1 unchanged.
- Experiment-001 semantics frozen: 120 train / 30 validation, one LoRA configuration, one epoch, one full Candidate, no sweep.
- First-run implementation details now precommitted before results: AdamW (`adamw_torch` semantics), constant schedule, BF16, no gradient checkpointing, deterministic SHA-ordered training sequence from seed 42, max sequence length 256, microbatch 1, accumulation 8.
- Fail-closed execution snapshot validator checks exact 40-hex code/tool revisions, SHA-256 identity fields, 120/30 counts, LoRA settings, paired-Q4 requirement, privacy flags, positive cost/time ceilings and exact authorization-state shape.
- Preflight authorization and full Candidate-training authorization are separate. A preflight approval can never imply permission for full training.
- The preflight report SHA is correctly treated as an output: it may remain unresolved before/preflight and becomes mandatory for full-training authorization.
- Offline dataset tooling can generate a deterministic human-review queue and freeze canonical dataset/provenance/contamination evidence only after the exact 120/30 set and required human decisions close.
- Contamination evidence stores opaque protected identifiers/hashes rather than V2 expected-answer text.
- Local identity tooling can hash a materialized HF base/tokenizer snapshot, chat-template probe and pinned llama.cpp converter/quantizer bytes without downloading anything.
- Authorization packet tooling can generate a deterministic, hash-addressed preflight-only approval packet from a fully populated but still-unapproved snapshot.
- Concrete HF/PEFT LoRA runtime code exists behind the authorization gate. Heavy dependencies are dynamically imported only after gate validation; model/tokenizer loading is `local_files_only=True`; unresolved/unapproved snapshots cannot reach model loading or output creation.
- Non-Candidate preflight implementation performs one forward/backward optimizer step and records device/VRAM/wall-time mechanics without saving Candidate weights.
- Full-run implementation is fixed to 120 deterministic microbatches / 15 optimizer steps and writes only to a new Candidate directory after full-training authorization. CI cannot reach it.
- Candidate/export lineage manifests and Validation-only paired Current/Candidate comparison are implemented without changing historical V2 scorer/policy.
- PR #5 remains Draft; no merge/promotion path is enabled.

## Still required before the first external-compute preflight

These are evidence/input blockers, not design questions:

1. Exact immutable Hugging Face revision for `Qwen/Qwen3-4B-Instruct-2507`, plus materialized file hashes and tokenizer/chat-template probe hash.
2. Real experiment-001 120/30 examples with traceable provenance/rights, source/template-family separation, mandatory human approval and completed contamination-review decisions.
3. Exact Linux/container + Python/torch/transformers/PEFT/accelerate/CUDA version pins verified against the concrete runtime implementation.
4. Exact llama.cpp commit plus converter and quantizer byte identities.
5. Proposed GPU/device/VRAM/driver, maximum JPY ceiling and wall-clock timeout. These may be proposed in the snapshot but remain unapproved until the user explicitly accepts the preflight packet.
6. Latest branch tests/CI GREEN. A queued workflow is not a PASS.

## Preflight-only authorization packet

Immediately before any external GPU action, generate and present the `ark-v3-auth-packet` output. It contains the execution-snapshot hash, base/tokenizer identities, dataset/provenance/contamination hashes, code SHA, exact method/environment, proposed device, cost/time ceiling, export identities and explicit hard stops.

Approval scope must be exactly:

`EXTERNAL_COMPUTE_PLUS_NON_CANDIDATE_PREFLIGHT_ONLY`

The authorized preflight must keep `real_training_authorized=false`, `v2_opening_authorized=false`, `promotion_authorized=false`. It may load the frozen base and perform one optimizer step for feasibility, but it may not save an adapter/Candidate or open Validation/V2.

## Second STOP before full Candidate training

After successful preflight, record and hash the preflight evidence, populate `hardware.preflight_report_sha256`, independently verify the final execution snapshot, and present a second explicit authorization request for the single full Candidate training run. A successful preflight never grants this permission automatically.

Even after full training, historical V2 opening and Candidate promotion remain later independent hard stops.
