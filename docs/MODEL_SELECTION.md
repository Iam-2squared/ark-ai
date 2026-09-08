# V1 CPU model selection (2026-09-08)

Decision: **Qwen3-4B-Instruct-2507 Q4_K_M**, with 4096 context, 4 CPU threads,
256 output tokens. This is a practical starting configuration, not a measured optimum.

| Candidate | Role | File / license | Tradeoff |
| --- | --- | --- | --- |
| Qwen3-4B-Instruct-2507 Q4_K_M | Selected | 2.497 GB; Apache-2.0 base | Smaller weight footprint than Q5; non-thinking chat model |
| Same model Q5_K_M | Optional later comparison | 2.890 GB; same base license | Less quantization loss expected; larger file; CPU speed not measured |
| Qwen2.5-3B-Instruct Q4_K_M | Smaller fallback | Official Qwen GGUF; Qwen Research license | 3.09B, Japanese support documented; different license, not Apache-2.0 |

The selected model's original card describes 4.0B parameters, non-thinking output,
multilingual, coding and reasoning capabilities, and a native 262144-token window.
ARK deliberately allocates only 4096 tokens. Manufacturer benchmarks do not establish
Japanese quality or quantized-model throughput on this i5. Both must be measured here.

Q4_K_M weight size leaves room within 16 GB for the OS, KV cache and runtime buffers.
This is a memory-budget inference, not a RAM guarantee. Exact peak RAM, first-token
latency and tokens/sec are pending target-PC evidence. No invented speed estimates
or unmeasured quality scores are used to choose a winner.

## Compatibility and provenance

- [Original model and license](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)
- [Quantizer's model card](https://huggingface.co/bartowski/Qwen_Qwen3-4B-Instruct-2507-GGUF)
- [Exact Q4_K_M file and SHA-256](https://huggingface.co/bartowski/Qwen_Qwen3-4B-Instruct-2507-GGUF/blob/ae44f08e1392f39c0e474af10c3ff8355c8b6688/Qwen_Qwen3-4B-Instruct-2507-Q4_K_M.gguf)
- [Qwen llama.cpp guide](https://qwen.readthedocs.io/en/latest/run_locally/llama.cpp.html)
- [3B fallback card](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF)

Qwen documents Qwen3 support from llama.cpp b5092. The quantizer reports b6096.
Inspection of llama-cpp-python v0.3.35's vendored llama.cpp commit
`4df29be4f4c3673f428170fda944a5b19f743bb8` confirmed the `qwen3` architecture in
[src/llama-arch.cpp](https://github.com/ggml-org/llama.cpp/blob/4df29be4f4c3673f428170fda944a5b19f743bb8/src/llama-arch.cpp).
ARK lets llama-cpp-python use the GGUF chat template. The selected model uses a
ChatML-style system/user/assistant format, without a thinking-mode toggle.
Architecture support and file availability are confirmed; this exact GGUF's successful
load and chat on the user's native Windows build are still pending.
