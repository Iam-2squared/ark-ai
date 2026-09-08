# V2 Real-Model Baseline — reviewed PASS

Target date: 2026-09-09 JST. Tested code: `21f5dbd4efed1a2ee39f47dc0653a1e978f03e29`.
V1 prerequisite freeze: `7e46a4529879243b4a5bd52bb6575d11c1ec0183`, already in this branch.
This evidence/documentation/test-only change does not alter runtime, policy, suite or
scorers. V2 OFFICIAL PASS takes effect on main after final-head green CI and PR #3
merge. That merge commit is the V2 freeze point; Git history supplies its SHA.

## Original evidence and resolved blocker

Six originals are preserved byte-for-byte under `raw/`; SHA-256 and upload-name
mapping are in `manifest.json`. Original pending-review/merge-blocked flags remain
untouched: this separate review resolves their milestone status.

The initial upload duplicated run 1. Corrected attachments now provide run 2 with
a different SHA, timestamp, request IDs, latency, load time, wall time and peak RAM.
Each run contains 15 generation requests; the two ID sets are disjoint. The first
run ends before the second starts. The uploaded comparison exactly matches a
fresh comparison of these distinct reports. The prior blocker is resolved; duplicate
uploads are not counted as extra experiments. Reattached original V1 offline runs
match the already-frozen V1 hashes and are not new V2 measurements.

## Fixed scoring review

| Domain | Run 1 | Run 2 |
| --- | --- | --- |
| Conversation (Japanese format and JSON) | 2/2 | 2/2 |
| Context (recall and corrected project name) | 2/2 | 2/2 |
| Math | 2/3 | 2/3 |
| Reasoning | 2/2 | 2/2 |
| Coding (restricted AST tests) | 3/3 | 3/3 |
| Total | 11/12 | 11/12 |
| Runtime failures | 0 | 0 |

Both FAILs are `math-02`. Prompt: `Compute 3/4 + 1/8. Return only a fraction or decimal.`
Expected numeric value: `7/8`. Both actual answers: `3/4 + 1/8 = 7/8`.
Frozen reason: `invalid_answer: ValueError: expected only an integer, decimal or fraction`.
The arithmetic is correct; the output violates the numeric-only format contract.
**FAIL is retained.** No answer extraction, partial credit, fixture edits, scorer
relaxation or policy tuning. This known instruction-following limitation does not
prevent the existing infrastructure/baseline completion gate from passing. The
contract does not require a perfect model score. This is a small public development
suite, not general intelligence or held-out performance evidence.

All 24 outcomes and coding test details were re-scored against the frozen suite.
Context requests were checked against system policy, ordered setup turns and
generation controls. Scoring answers are not injected into model requests.
Comparison: compatible, controlled metadata, no regressions or improvements,
zero domain deltas, zero runtime failures. Repetition under the same model/settings
does not establish that a code change improves model quality.

## Model, configuration and measurements

Windows 11 10.0.26200, Intel64 Family 6 Model 142 Stepping 10 GenuineIntel,
16 GiB RAM (user reported), CPU-only, Python 3.12.10, llama-cpp-python 0.3.35,
ARK 0.1.0. Qwen3-4B-Instruct-2507, 4.0B, Q4_K_M, 2,497,280,736 bytes.
Weight SHA: `2fde00ce69dd4899c70d020845e2638353015bba0fdf161b3eb965f2bca4464e`.
Context 4096, threads 4, max output 256, temperature 0.2, top-p 0.95, seed 42.

| Measurement | Run 1 | Run 2 |
| --- | --- | --- |
| Start UTC | 2026-09-08T22:37:53.029445+00:00 | 2026-09-08T22:38:58.155084+00:00 |
| Model load seconds | 4.390740599992569 | 3.8509533000033116 |
| Total wall seconds | 59.12420109999948 | 55.401736200001324 |
| Peak resident RAM MiB | 4786.2890625 | 4785.7421875 |

Per-case first-token latency and visible-output token estimates remain in originals.
Speed includes prefill. Exact token counts remain null; context utilization is the
UTF-8/framing heuristic, not native template tokenization. RAM is process-lifetime
peak resident memory. These short conversations do not test maximum context capacity.
Physical network disconnection remains user-attested, never automatically verified.

Suite/scorer/policy/model fingerprints agree across both runs and frozen code.
Implementation source fingerprints differ from Git LF bytes only because existing
`models.py` and `config.py` used CRLF on Windows. Applying only that newline transform
reproduces reported `d517645ff8f097ca0db2a9a45cf779dc36ba3db03e04b2d54382085c59f107a4`;
the Git LF variant is `8503966793dcc7509eda48880bd20853a998d287a892ffdcb6f4eadb2bddf79d`.
No semantic source change is needed to explain this. Source fingerprints and user
checkout provenance are not signed process attestations.

## Conversation and V1 regression

V2 session: coherent Japanese; correct 青いりんご recall; explicit history-reset event;
post-reset 未指定; exit event. PASS for observed behavior. V1 session: coherent Japanese,
correct recall, new-conversation response. V1 logger does not record reset/exit;
those controls use the user's reported test procedure and existing unit coverage,
not an inference solely from the final answer.

V1-on-V2 benchmark: real backend, correct weights/settings, startup true, 6/6
successful responses, zero failures, semantic Japanese/recall PASS. Load 3.6266469 s,
wall 36.3023451 s, peak RAM 4760.828125 MiB. No critical V1 regression is evident.
V1 runtime files remain unchanged. Backend abstraction, error handling, logging and
context/reset mechanics also retain deterministic CI coverage; CI does not run Qwen.

Only designated test conversations are published. V3 and later remain locked.
