# V2 Intelligence Contract (contract version 1)

V2 advance development is authorized on `research/v2-ark-intelligence` only.
Base: V1 PR #2, main commit afd819152ec6228e0fbd8409eaf538b27589868a.
V1 passed with original evidence frozen in main commit
`7e46a4529879243b4a5bd52bb6575d11c1ec0183` (PR #4). That main is merged into this branch.
The previously locked local runtime adapter is now explicitly opt-in. Draft PR stays
draft: no auto-merge or main promotion before reviewed V2 real-model evidence.
This gate transition does not change contract version 1, the fixed suite or scorers.

## Responsibilities

- Input: a nonempty user message and explicit task mode; not arbitrary role injection.
- Policy: stable ARK system instruction plus concise/explanation/coding/structured mode.
  Ask for answers and useful explanations, never private chain-of-thought.
- Context: current in-memory conversation only; ordered complete user/assistant turns.
  System instruction and newest user input are preserved. Reserve output budget plus
  a safety margin. Remove oldest complete turns until the request fits. Reject a current
  input that cannot fit on its own. Do not split messages or summarize silently.
- Capability: explicit immutable metadata supplied independently of the backend:
  configured context capacity, chat support, languages/coding evidence provenance and
  supported generation controls. Do not infer capability from model names.
- Request: unique ID, ordered messages, generation controls and budget accounting.
- Backend: existing ModelBackend protocol performs generation; no context/policy ownership.
- Response: visible text, request ID, dropped-turn count and measured/estimated metadata.
  Only successful nonempty generation commits state. Errors leave history unchanged.
- Reset: empty current conversation; keep configuration/policy. No disk memory or retrieval.

Token counting is replaceable. The dependency-free default counts UTF-8 bytes plus
32 framing units/message and 16 request units. This is a conservative heuristic, not
an exact template tokenizer or universal upper bound. Label it as an estimate; native
context-overflow errors remain possible and must preserve state. The final real-model
context gate must verify the runtime/template on the target PC.

V1 CLI/Core remain the default and unchanged. `ark-v2` and `ark-eval` default to mock.
`--backend llama-cpp --config config.toml` explicitly connects the local runtime
after the V1 evidence freeze. No model-name routing, cloud API or automatic download
is added. Real capability metadata comes from configuration and adapter support,
not inferred model intelligence. See [target-PC steps](REAL_MODEL.md).

## Evaluation boundary

Freeze the new V2 suite before implementation. Keep suite bytes and SHA-256 stable;
future problem changes require a new suite ID and explicit comparison incompatibility.
Expected answers and test vectors go only to scorers, never the generation request.
The scripted mock is a public infrastructure fixture with known answers, not AI evidence.

Math: strict numeric answer normalization (Unicode NFKC, signed integer/decimal/fraction).
Reasoning/conversation/context: explicit normalized exact or JSON-object rules.
Coding: three small pure integer functions, tested by a bounded AST expression interpreter.
No exec/eval, subprocess execution of generated Python, imports, attributes, loops or
function calls. This tests a restricted language subset, not arbitrary Python correctness.

Result contract: suite/scorer/policy versions, suite hash, runtime/model/quantization
metadata, configuration, prompts/responses, per-case outcome/reason/latency, context
accounting, failures and domain rates. Mock model-performance and hardware-performance
fields are null/NOT_MEASURED; fixture/scorer checks live under infrastructure results.
Real-model PASS and overall V2 PASS are never inferred from mock success.

Regression: compare only compatible schema/suite/scorer and complete unique task IDs.
Reject mixed mock/real reports. Separate fixture regressions from measured model
regressions, report metadata differences, and reject missing/inconsistent evidence.
