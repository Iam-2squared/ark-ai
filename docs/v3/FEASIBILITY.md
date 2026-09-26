# Training feasibility audit — 2026-09-09 JST

**No real training approved or executed.** The target's successful Q4_K_M inference
does not establish training feasibility. Current GGUF stays unchanged.

## Primary-source findings

- [Qwen model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507):
  4.0B Qwen3 causal model, Apache-2.0, Transformers/safetensors route. Training base
  should be this unquantized model revision, not the existing inference GGUF. Exact
  revision, file digests and tokenizer/template must be frozen before execution.
- [PEFT quantization guide](https://huggingface.co/docs/peft/en/developer_guides/quantization):
  QLoRA combines quantized loading with trainable adapters; this is not training
  the existing GGUF file. Hardware/backend support must be checked for the selected
  stack. No claim is made that Windows CPU-only QLoRA works on this target.
- [PEFT LoRA documentation](https://huggingface.co/docs/peft/en/package_reference/lora):
  LoRA provides configurable adapter training. It is the proposed small-experiment
  method, with frozen base parameters and a separately versioned adapter.
- [llama.cpp conversion source](https://github.com/ggml-org/llama.cpp/blob/master/convert_lora_to_gguf.py):
  a LoRA conversion route exists. Its existence is not proof of compatibility with
  this exact Qwen/export/runtime combination. Conversion must use a pinned commit
  and be verified before evaluating a candidate. An alternative is merge adapter
  into a separate base copy, convert HF weights to GGUF, quantize Q4_K_M.

## Resource reasoning (estimates, not measured requirements)

4 billion two-byte parameters alone occupy about 8 GB decimal / 7.45 GiB. Four-byte
parameters alone occupy about 16 GB / 14.90 GiB. Gradients, optimizer states,
activations and OS memory are additional. Full fine-tuning on a 16 GiB CPU-only PC
is therefore not an approved route. LoRA reduces trainable state but still needs
base weights and activation memory; CPU wall time and peak memory are NOT_MEASURED.
Do not infer feasibility from the 2.50 GB GGUF or its approximately 4.7 GiB inference RAM.

Proposed real experiment: BF16 LoRA on a separately approved GPU environment,
or a separately approved CPU feasibility pilot if the user wants to investigate it.
No provider, spending, account setup, hardware purchase, job submission or transfer
is authorized here. GPU memory requirements depend on sequence length, optimizer,
batching and checkpointing; they must be measured before selecting paid capacity.

A conservative scratch-storage planning allowance for separate source weights,
merged weights, intermediate GGUF and Q4 output is 40–60 GB, **not a measured minimum**.
Adapter size, download size and training duration stay pending pinned files and a
hardware smoke test. We cannot provide a reliable time estimate for the i5 target.

## Real execution blockers

1. Human choice/authorization of training hardware; exact versions and capacity.
2. Exact base/tokenizer revisions and SHA manifest; no weights downloaded yet.
3. Actual independently authored/reviewed 120/30 dataset and frozen artifact hash.
4. Pinned training/export dependency lock, exact executable recipe and verified export.
5. Final training precommit review and explicit permission to cross the training stop.

Dataset/registry/mock verification needs no accelerator or new runtime dependency.
The implemented real backend intentionally raises StopRequired. Do not add an unlock
flag to bypass these missing execution prerequisites.
