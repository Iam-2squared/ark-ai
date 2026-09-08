# Evaluation contract v1

The new author-created suite `ark-v2-foundation-1` contains 12 fixed development cases.
It was committed before implementation. Its raw UTF-8 bytes are pinned both in
`data/suite.sha256` and `suite.py`. Cases must not be rewritten to improve a score.
A different suite needs a new ID/hash and is not directly comparable.
This is not an untouched holdout; the scripted fixture intentionally knows its answers.

## Scoring

- Numeric: NFKC normalization, whitespace trim, exact rational comparison of a signed
  integer, decimal or fraction. Explanatory text, multiple answers, NaN and zero
  denominators fail. No approximate tolerance or substring matching.
- Exact: NFKC, case folding, trim; exact match. Extra punctuation/prose fails by contract.
- JSON: parse JSON, reject duplicate keys, compare the complete typed JSON structure.
  Code fences or extra keys fail.
- Coding: parse one function (optionally one Python fence) with one return expression.
  Integer/bool constants, parameter names, + - * // %, one comparison, unary signs/not
  and conditional expressions are supported. No calls, attributes, imports, loops,
  comprehensions, decorators, defaults, exponentiation or arbitrary statements.
  Every branch is validated before interpreting any test, even unreachable branches.
  Limit source to 4096 bytes, AST to 80 nodes, nesting to 24 and magnitude to 10^12.
  Each vector checks both value and return type. Unsupported Python is rejected rather
  than executed. This is a small isolated language interpreter, not a Python security
  sandbox or a score for arbitrary generated applications.

Prompts alone are passed to Intelligence; expected answers/test vectors reach only
scoring. Setup turns use normal generation and become part of the current conversation.
Each new task resets history. No generated answer becomes a new training example.

## JSON result schema 1

| Field | Meaning |
| --- | --- |
| suite_id / suite_sha256 | Exact frozen task set |
| scorer_version / scorer_sha256 | Rule version and implementation fingerprint |
| policy_version / policy_sha256 | Answer policy identity |
| implementation_sha256 | Intelligence and runner/backend source fingerprint |
| configuration | Explicit capabilities, context limit, generation controls/seed |
| model_identity | Name, quantization and weight hash slots; mock has no weights |
| runtime | Python/platform; no llama.cpp loaded by mock |
| cases | ID, original prompts, response, scoring contract, failure reason |
| infrastructure_turns | Requests, visible responses, timings and estimated context accounting |
| domains | Fixture counts/rates; real model rates null |
| model_metrics | Actual model first-token/speed/RAM/token/utilization slots; all null in mock |
| infrastructure_failure_count | Failed generation or scorer cases |
| infrastructure_peak_ram_mib | Python fixture process memory, not model footprint |
| main_merge / v1_gate / v2_gate | Pending/blocked, never promoted by a fixture run |

Schema 1 remains mock-only. V1 official PASS is a separately reviewed historical fact,
not a result of running a fixture. No report automatically grants V2 completion.

## Real result schema 2 (after V1 evidence freeze)

Explicit `--backend llama-cpp --config config.toml` uses the SAME suite and scorers.
This V2 schema is separate from the V1 benchmark schema with the same number.
Record GGUF basename/family/parameter size/quantization/bytes/SHA-256, complete
configuration, runtime package versions, platform/CPU, capability provenance,
system instructions and source fingerprints. No weight download or remote API.
`cases` contain setup prompts, original prompt, response, frozen scoring contract,
boolean `model_passed`, failure reason, scoring details, generation turns and latency.
JSON behavior is the existing conversation-02 case, not an extra score-adjusted task.

`model_failures` counts incorrect or failed cases; `runtime_failure_count` separately
counts startup/generation errors. Startup failures are saved with no cases and
NOT_MEASURED. A completed suite is MEASURED_PENDING_REVIEW, never V2 PASS.
Exit 1 indicates runtime/memory failure; exit 0 means execution completed, NOT that
all answers passed. Low scores remain in the baseline and must not be hidden.

Per-case `model_metrics` describe the last answer; `turns` preserves all setup and
answer timings. First-token latency is time to first visible streamed text.
`tokens_per_second_estimate` includes prefill; `completion_tokens_estimate` is
retokenized visible output. Exact prompt/completion token fields remain null.
Prompt counts/context utilization use the documented UTF-8/framing heuristic,
not exact runtime template accounting. Peak RAM is the process-lifetime native
resident high-water mark, captured once per report. Model load and total wall time
are separate (total includes weight hashing). Unknown values remain null.
Physical offline state is user-attested only. Results require human review.

## Regression rules

Same schema/contract/suite/hash/scorer/measurement kind and complete unique task IDs
are required. Corrupted summaries, missing cases and mock model metrics are rejected.
The comparator reports task regressions/improvements and metadata differences.
A regression or any remaining candidate fixture failure returns a nonzero exit code.
A successful mock comparison is only a fixture regression check. Model-quality delta is null.
Changes of policy/implementation/model metadata are visible, not silently hidden.
Changing the scorer hash requires a new compatible baseline; changing the suite is not
an improvement over the old suite. Mixed mock/real reports are rejected.

Real comparisons additionally re-score stored answers against the frozen scorer and
validate complete unique IDs, task contracts, counts and rates. Mixed mock/real
and startup-failure baselines are rejected. Real comparisons return domain score
deltas and task regressions; differing runtime/model/configuration is marked as an
uncontrolled comparison, not evidence that the code change caused a difference.
Runtime/memory failures or regressions yield nonzero exit. An unchanged low baseline
may compare cleanly; this still does not grant PASS or authorize merge.

For real measurements, preserve suite/scorer and capture exact GGUF SHA,
quantization, settings, runtime, sampling seed, target hardware, template token counts
where available, and repeated measurements. Do not optimize these public development tasks and then
claim general intelligence gains. Broader held-out evaluation belongs in a later phase.
