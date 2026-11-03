# V3 Experiment 001 — Hugging Face identity review

Status: **PARTIAL VERIFIED METADATA / IMMUTABLE REVISION STILL BLOCKED**

Verified through the connected Hugging Face repository inspector on 2026-09-11 JST:

- Repository/model ID: `Qwen/Qwen3-4B-Instruct-2507`
- Author: Qwen
- Task: text-generation
- Library: transformers
- Model class: AutoModelForCausalLM
- Architecture tag: qwen3
- Parameter metadata: 4022.5M
- Repository license metadata: Apache-2.0
- Weight-format tag: safetensors

This evidence is sufficient to confirm that the intended upstream repository/model family exists and matches the V3 design target. It is **not** sufficient to freeze the execution identity.

The connected inspector does not expose, in the returned repository-details payload, the immutable 40-hex Hub commit revision or per-file bytes/hashes required by `build_hf_snapshot_identity`. Therefore the execution snapshot fields for base revision, base file-manifest SHA, tokenizer file-manifest SHA and chat-template probe SHA remain unresolved. They must be derived from a materialized snapshot pinned to an immutable revision before any external GPU/preflight authorization.

No mutable `main` reference may be substituted. No hash is inferred from model metadata. No model download, external compute, adapter generation, Validation opening or V2 opening occurred during this review.
