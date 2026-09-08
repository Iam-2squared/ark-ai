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

The schema reserves model identity, quantization, runtime, performance and failures,
but this advance branch neither measures nor compares real models. Connecting an actual
GGUF evaluation is V2-J, after V1 PASS. Schema is separate from V1 benchmark schema 2.
There is no automatic claim of V1 or V2 completion from this report.

## Regression rules

Same schema/contract/suite/hash/scorer/measurement kind and complete unique task IDs
are required. Corrupted summaries, missing cases and mock model metrics are rejected.
The comparator reports task regressions/improvements and metadata differences.
A regression or any remaining candidate fixture failure returns a nonzero exit code.
A successful comparison is only a fixture regression check. Model-quality delta is null.
Changes of policy/implementation/model metadata are visible, not silently hidden.
Changing the scorer hash requires a new compatible baseline; changing the suite is not
an improvement over the old suite. Mixed mock/real reports are rejected.

For future real measurements, preserve suite/scorer and capture exact GGUF SHA,
quantization, settings, runtime, sampling seed, target hardware, template token counts
and repeated measurements. Do not optimize these public development tasks and then
claim general intelligence gains. Broader held-out evaluation belongs in a later phase.
