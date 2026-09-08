"""Configuration loading for ARK V1."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from .models import GenerationConfig


@dataclass(frozen=True)
class ArkConfig:
    backend: str = "llama-cpp"
    model_path: str | None = None
    model_family: str | None = None
    parameter_size: str | None = None
    quantization: str | None = None
    context_size: int = 4096
    threads: int | None = None
    log_directory: str = "logs"
    generation: GenerationConfig = GenerationConfig()


def load_config(path: str | Path | None = None) -> ArkConfig:
    """Load TOML configuration, with ARK_MODEL_PATH as a safe local override."""
    data: dict[str, object] = {}
    if path is not None:
        config_path = Path(path).expanduser()
        if not config_path.is_file():
            raise FileNotFoundError(f"configuration not found: {config_path}")
        with config_path.open("rb") as handle:
            data = tomllib.load(handle)

    model = _table(data, "model")
    generation = _table(data, "generation")
    logging = _table(data, "logging")
    model_path = os.environ.get("ARK_MODEL_PATH") or _optional_str(model.get("path"))
    return ArkConfig(
        backend=str(model.get("backend", "llama-cpp")),
        model_path=model_path,
        model_family=_optional_str(model.get("family")),
        parameter_size=_optional_str(model.get("parameter_size")),
        quantization=_optional_str(model.get("quantization")),
        context_size=int(model.get("context_size", 4096)),
        threads=_optional_int(model.get("threads")),
        log_directory=str(logging.get("directory", "logs")),
        generation=GenerationConfig(
            max_tokens=int(generation.get("max_tokens", 512)),
            temperature=float(generation.get("temperature", 0.7)),
            top_p=float(generation.get("top_p", 0.95)),
            seed=int(generation.get("seed", 42)),
        ),
    )


def _table(data: dict[str, object], key: str) -> dict[str, object]:
    value = data.get(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"[{key}] must be a TOML table")
    return value


def _optional_int(value: object) -> int | None:
    return None if value is None else int(value)


def _optional_str(value: object) -> str | None:
    return None if value is None else str(value)
