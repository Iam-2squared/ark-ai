> V1 and V2: **OFFICIAL PASS** upon the reviewed PR #3 merge.
> [V2 real-model baseline](evidence/v2/REVIEW.md): 11/12 in each of two runs;
> math-02 remains FAIL. [V2 usage](docs/v2/REAL_MODEL.md). V3+ stays locked.

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
- [x] Offline verification on target PC — [reviewed original evidence](evidence/v1/REVIEW.md)

V1 is **OFFICIAL PASS** based on reviewed target-PC evidence. CI uses a
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

## Local UI v1 — target-PC gate pending

Use ARK V2 from a browser with the existing GGUF and configuration:

```powershell
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
.\.venv\Scripts\ark-ui.exe --config config.toml
```

Open **http://127.0.0.1:8765**. The model loads once, then the Japanese chat UI
uses V2's existing context, response policy and reset. All assets are bundled;
there is no runtime Node.js requirement, cloud service, external font or API key.
`LOCAL MODEL` identifies the inference backend; it does not attest network disconnection.

See [Local UI architecture, Windows setup and completion gate](docs/LOCAL_UI.md).
This UI is a dedicated branch/Draft PR based on V2. Merge waits for reviewed
target-PC real-model, browser and offline evidence. V3 PR #5 is separate.

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
[model selection](docs/MODEL_SELECTION.md). V1 evidence is frozen. V2 real-model
integration and real-model review are complete; see the V2 baseline linked above.
