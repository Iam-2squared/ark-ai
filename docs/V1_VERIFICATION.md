# V1 verification

## Automated gate

Run:

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest
ark-bench --config tests/fixtures/echo.toml
```

CI uses the deterministic offline echo backend. It validates model interchangeability,
conversation state, error handling, logging, configuration, CLI packaging, and the
benchmark result schema without downloading a model.

## Target-PC offline gate

This is the only gate that CI cannot honestly certify.

1. Install the local extra: `python -m pip install -e '.[local]'`.
2. Place a chat-compatible GGUF under `models/` (ignored by Git).
3. Copy `config.example.toml` to `config.toml` and set the path.
4. Disconnect the network.
5. Run `ark --config config.toml` and hold a multi-turn Japanese conversation.
6. Run `ark-bench --config config.toml` and retain the JSON result.

Record model filename, quantization, CPU, RAM, context size, thread count, wall time,
failure count, and peak process memory. V1 is fully passed only after this target-PC run.
