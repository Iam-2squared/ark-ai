"""Model interfaces and the V1 local GGUF backend."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class GenerationConfig:
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.95


class ModelBackend(Protocol):
    @property
    def name(self) -> str: ...

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> str: ...


class LlamaCppBackend:
    """Runs a GGUF model locally through llama-cpp-python.

    The import is intentionally lazy so ARK's core/tests do not require the
    native dependency. Install with: pip install -e '.[local]'
    """

    def __init__(self, model_path: str | Path, *, context_size: int = 4096, threads: int | None = None):
        path = Path(model_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"GGUF model not found: {path}")
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError("Install the local backend with: pip install -e '.[local]'") from exc

        kwargs: dict[str, object] = {"model_path": str(path), "n_ctx": context_size, "verbose": False}
        if threads is not None:
            kwargs["n_threads"] = threads
        self._llm = Llama(**kwargs)
        self._name = path.name

    @property
    def name(self) -> str:
        return self._name

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> str:
        result = self._llm.create_chat_completion(
            messages=messages,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
        )
        return str(result["choices"][0]["message"]["content"] or "").strip()


class EchoBackend:
    """Deterministic offline backend used only for tests and smoke checks."""

    name = "echo-test-backend"

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> str:
        del config
        user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return f"ECHO: {user}"
