# V1 Final Evidence — OFFICIAL PASS

Target test date: 2026-09-09 JST (original timestamps are UTC on September 8).
Reviewed against `docs/V1_VERIFICATION.md` at tested main
`afd819152ec6228e0fbd8409eaf538b27589868a` (checkout reported by the user;
the benchmark does not independently attest the code commit).
This evidence-only change does not modify the tested runtime. Its merge commit
is the V1 evidence freeze point; identify it in Git history, not a self-referential SHA.

## Decision and provenance

**V1 Local Core: OFFICIAL PASS.** The two original real-model benchmarks, two
test-only conversation logs, and the user's explicit physical-offline/reset/exit
attestation satisfy the existing V1 contract. This is a reviewed target-PC result,
not a claim that CI ran a GGUF model or independently verified network isolation.
The review becomes the main-branch status when its PR passes CI and merges.

| Gate | Evidence | Review |
| --- | --- | --- |
| Real GGUF load | Both JSONs: startup true, test_backend false, matching weight SHA/size | PASS |
| Japanese | Coherent Japanese self-introductions in both logs and benchmarks | PASS, semantic review |
| Multi-turn | All four records recall 青いりんご correctly | PASS, semantic review |
| Reset and exit | User observed `Conversation reset.`, subsequent new conversation and clean exit in both sessions | PASS, user attestation |
| Physical offline cold start | User disconnected network before starting a new ARK process; offline log precedes both benchmarks | PASS, user attestation |
| Repeat benchmark | Same suite, model and configuration; both runs 6/6 nonempty responses, zero failures | PASS |
| Durable evidence | Four originals, hashes below, hardware, configuration and this review | PASS |

The V1 logger stores user/assistant messages only: `/reset`, `/exit`, process start
and physical network state are not independently logged. The post-reset response
alone does not prove history erasure. These checks use the explicit user report,
supported by existing reset unit tests, without pretending they are automatic proof.
No crashes or console errors were reported for these successful test sessions.

Original JSON `semantic_review: pending` and `v1_final_gate: pending_human_review`
remain unchanged; this separate review resolves them. `offline_verified_automatically`
remains false. Infrastructure success is not a general reasoning/coding quality score.
Original run 2 recalls the full sentence `先ほどの合言葉は「青いりんご」です。`;
the earlier chat summary shortened this to the passphrase. Originals take precedence.

## Target and model

Windows 11 (10.0.26200), Intel64 Family 6 Model 142 Stepping 10 GenuineIntel,
Core i5 8th-generation class, 16 GiB RAM (user reported), CPU-only.
Python 3.12.10; llama-cpp-python 0.3.35 CPU native build; ARK 0.1.0.
Qwen3-4B-Instruct-2507, 4.0B, Q4_K_M:
`Qwen_Qwen3-4B-Instruct-2507-Q4_K_M.gguf`, 2,497,280,736 bytes.
Weight SHA-256: `2fde00ce69dd4899c70d020845e2638353015bba0fdf161b3eb965f2bca4464e`.
Both originals include configuration: context 4096, threads 4, max output 256,
temperature 0.2, top-p 0.95, seed 42 and the system prompt.

| Run | Load seconds | Wall seconds | Peak process RAM MiB | Failures |
| --- | ---: | ---: | ---: | ---: |
| 1 | 4.380554900002608 | 44.80005820000224 | 4760.28125 | 0 |
| 2 | 4.986577199997555 | 49.75957709999784 | 4760.9921875 | 0 |

Per-case first-token latency and speed are in the originals. Visible-output token
counts are retokenization estimates; speed includes prefill, not pure decoding
throughput. RAM is native process lifetime peak resident memory, not model weight
size or whole-machine RAM. No unsupported performance extrapolation is made.

## Immutable originals

Byte-for-byte copies; Git newline conversion is disabled for this directory.
Only designated test conversations are included, not general private chat logs.

| Stored file | Uploaded filename | SHA-256 |
| --- | --- | --- |
| raw/v1-offline-1.json | 98481882-0857-49a3-8a51-7af8d07efa3f.json | 721648a10fd3fbe80fffa0c8f8f2c40819197f02620dadd0d2b292fde28d6a82 |
| raw/v1-offline-2.json | b66cf508-b856-45ab-b3e0-67f9a6a5ed3d.json | 6eb9828a71839beb1ac5c015ae57a981a4b1148da2025c10ea6a18043df3a96a |
| raw/online-session.jsonl | 1628a344-5844-413a-8eaa-263a0870dcc8.jsonl | 71adcf024de0d06324f0773de9aea82635ba72aa59cc78dd1d37b0252772f588 |
| raw/offline-session.jsonl | 3bc4b00e-7d76-4735-897b-2450254c7697.jsonl | 512e823a11621f9f6b6378f43a57300f06e6853322680c25af3a59aa2e934b60 |

V2 integration may proceed after this freeze merges. V2 real-model measurements
are still NOT MEASURED; PR #3 must remain draft/unmerged until its own real-model
baseline and V1 regression checks are reviewed. V3–V10 remain out of scope.
