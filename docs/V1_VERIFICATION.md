# V1 verification

**V1 code foundation merged; final target-PC gate ACTIVE. V2 LOCKED.**
The target's Python 3.12.10, Windows x64 build tools, native llama-cpp-python 0.3.35
build/import and ARK installation passed according to user-provided console results.
They do not yet demonstrate model inference.

## Automated gate

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest
ark-bench --config tests/fixtures/echo.toml
```

CI runs Python 3.11/3.12/3.13 on Ubuntu and Windows. It checks the real platform
memory API, CLI startup/reset/exit, mock streaming, history preservation on failure,
benchmark failure evidence and non-promotion of mock output. Model weights are not
downloaded; this is infrastructure validation, not a real-model capability score.

Schema 2 replaces the misleading `offline_capable` flag with an explicit user
attestation and `offline_verified_automatically: false`. Japanese/multi-turn semantic
review and the final gate stay pending even when infrastructure success is 100%.
Reported throughput is an estimate from visible output tokens including prefill.

## Target-PC final gate

Follow [Windows setup and exact offline commands](WINDOWS_SETUP.md), using
[the selected model](MODEL_SELECTION.md) and `config.windows-qwen3.toml`.

- [ ] Real GGUF load (correct SHA, test_backend false, startup_success true)
- [ ] Coherent Japanese conversation
- [ ] Real-model multi-turn recall (and reset works)
- [ ] Cold restart and conversation with all network connections disconnected
- [ ] Two real-model benchmark runs with saved settings, metrics and reviewed answers
- [ ] Evidence recorded: both JSONs, test chat logs, manual review, commit and hardware

Only reviewed evidence from the target can change these to PASS. CLI errors and
process crashes must be included in the manual review; a crashed process cannot
reliably write its own final JSON. Save error console output if JSON is absent.
Logging stays local. Runtime has no remote LLM dependency or automatic download.

`logs/`, `benchmark-results/`, `.venv/`, `.venv-*/`, `models/`, `*.gguf` and
`config.toml` are excluded from Git. The uploaded evidence should be test conversations
only; the repository is public.
