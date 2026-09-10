# V3 Experiment 001 — Pre-Paid-Compute Gate

Status: **NO EXTERNAL COMPUTE / NO SPEND / NO REAL TRAINING**.

This gate defines the furthest point the project may reach without purchasing or starting external GPU compute. It does not authorize downloads, cloud resources, adapters, candidate weights, V2 opening, promotion, or main merge.

## Must be complete before any paid/external compute

- Current main integrated into V3 branch; Contract 1 unchanged.
- Experiment-001 semantics frozen: 120/30, one LoRA config, one epoch, one full Candidate, no sweep.
- Execution supplement independently reviewed and all design policies closed.
- Fail-closed execution snapshot validator implemented and tested.
- Repository-owned real trainer/preflight entry point implemented but incapable of running unless the populated snapshot passes validation and explicit authorization flags are true.
- Dataset builder/auditor can produce canonical 120/30 bytes, manifest, provenance report and contamination-review queue without V2 expected answers entering trainer-visible material.
- Lineage-aware validation adapter implemented for paired Current/Candidate artifacts without modifying historical V2 scorer/policy.
- Export plan requires immutable base/adapter/merged/GGUF hashes and a paired Q4_K_M baseline.
- Exact external identities that can be resolved without starting compute are populated: HF revision/file hashes, tokenizer/template identity, package/container pins, llama.cpp converter/quantizer revision.
- Actual GPU/provider/VRAM/driver, monetary ceiling and timeout are proposed but remain unapproved until the user explicitly accepts them.

## Final STOP

Immediately before any action that may incur external-compute cost or create a real adapter/Candidate, present a concise authorization packet containing:

1. populated execution-snapshot SHA-256;
2. base/tokenizer manifest SHA-256;
3. dataset + contamination-report SHA-256;
4. exact training code/config SHA;
5. proposed provider/device/VRAM and environment identity;
6. maximum monetary ceiling and wall-clock timeout;
7. preflight command and evidence outputs expected;
8. statement that preflight is non-Candidate and opens neither Validation nor V2;
9. statement that a successful preflight still requires a separate explicit authorization before the one full Candidate training run if the prior authorization was preflight-only.

Until the user explicitly authorizes that packet, all real/external authorization fields remain false.
