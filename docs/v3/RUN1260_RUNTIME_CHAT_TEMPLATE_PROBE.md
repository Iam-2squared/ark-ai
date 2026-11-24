# Run1260 — verify the loaded tokenizer against the reviewed chat-template probe

## Exact basis

- Parent: Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent work-basis HEAD: `505b3d0e4af55cd67e4bf0d26e5462cfff999815`.
- Isolated branch: `research/run1260-v3-runtime-chat-template-probe`.
- Scope: free-only local validation code and synthetic tests; no frozen Contract 1 or execution-snapshot schema changes.

## Change

The runtime now loads the local tokenizer first, renders a fixed two-message probe with `apply_chat_template(tokenize=False, add_generation_prompt=False)`, and requires exact UTF-8 byte equality with the separately reviewed probe file whose SHA-256 is already bound in the execution snapshot. The probe file is bounded to 64 KiB and its local file identity is checked before and after the read. The actual verified digest, rather than an echoed snapshot value, is carried into non-Candidate preflight evidence. A mismatch fails before loading model weights.

The new tests use a fake tokenizer and temporary local files only. They cover a matching render, a mismatching render, and a probe-file replacement between identity checks. They do not import torch/transformers, load weights, execute an optimizer, create a Candidate, or use a GPU.

## Evidence boundary

This closes only the gap between the reviewed rendered-probe bytes and the loaded tokenizer's deterministic rendering of the fixed probe messages. It does not close hash-then-use races for the full base/tokenizer tree, provide immutable filesystem staging, authenticate the Hub revision, prove hostile-writer-resistant descriptor custody, or create an execution receipt.

No training, external compute, paid service, Candidate/weight generation, protected V2 evaluation, promotion, credential/account connection, physical hardware action, frozen-contract change, UI work, or main merge. PR #5 remains Draft/unmerged and all authorization gates remain closed. ARK/JARVIS remains NOT_PASSED.
