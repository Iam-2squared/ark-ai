# ARK AI

Local-first personal AI research project. ARK runs a local GGUF model through an
exchangeable backend; no OpenAI or Anthropic API is required.

## Current milestone

**V1 — Local Core**

Goal: run ARK locally without an external LLM API, chat through a CLI, log sessions, and execute a reproducible basic benchmark.

### V1 Gate

- [x] Local inference adapter
- [x] Exchangeable model backend
- [x] CLI chat with multi-turn state and reset
- [x] Structured JSONL logging
- [x] Reproducible basic benchmark infrastructure
- [x] Unit tests and CI
- [x] Setup and verification documentation
- [ ] Offline verification on target PC

The final unchecked item requires a real GGUF model on the target computer. CI uses a
deterministic offline test backend and never downloads model weights.

## Quick start

Requires Python 3.11 or newer.

```bash
git clone https://github.com/Iam-2squared/ark-ai.git
cd ark-ai
python -m venv .venv
```

Activate the virtual environment, then install ARK with its local runtime:

```bash
python -m pip install -e '.[local]'
```

Copy `config.example.toml` to `config.toml`, point `model.path` at a local,
chat-compatible GGUF file, then run:

```bash
ark --config config.toml
```

Commands inside chat: `/reset`, `/exit`.

## Development and benchmark

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest
ark-bench --config tests/fixtures/echo.toml
```

Benchmark JSON is written under `benchmark-results/` and includes per-prompt latency,
first-token latency, completion speed, peak process RAM, success/error state, model
identity, platform, and runtime metadata.

See [the roadmap](docs/ROADMAP.md) and [V1 verification](docs/V1_VERIFICATION.md).
