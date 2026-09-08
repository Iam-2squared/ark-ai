> **V2 advance-development branch:** V1 real-model/offline gate is still pending.
> V2 implementation and mock tests are allowed here; **main merge is blocked until
> V1 formally passes**. See [V2 development](docs/v2/README.md). V1 commands below stay unchanged.

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

**Windows CPU-only:** follow [the Windows guide](docs/WINDOWS_SETUP.md). It records
the successfully built Python 3.12 / MSVC x64 / llama-cpp-python 0.3.35 path.
If that runtime is already installed, keep it and update ARK with
`python -m pip install -e . --no-deps`.

On other platforms, activate the virtual environment, then install the local runtime
(a C++ compiler may be required):

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
first-visible-token latency, estimated output speed, peak resident RAM, startup
failures, model hash/size, settings/seed, platform, and runtime metadata.
Nonempty output success is not a semantic quality score or an offline PASS.

See [the roadmap](docs/ROADMAP.md) and [V1 verification](docs/V1_VERIFICATION.md).

For the final target-PC test use [Windows instructions](docs/WINDOWS_SETUP.md) and
[model selection](docs/MODEL_SELECTION.md). V1 is pending target evidence. V2 real-model evaluation and main promotion are locked;
V2 advance development is allowed only on its dedicated Draft PR branch.
