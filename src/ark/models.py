"""Model interfaces and the V1 local GGUF backend."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Protocol


@dataclass(frozen=True)
class GenerationConfig:
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.95


@dataclass(frozen=True)
class GenerationMetrics:
    elapsed_seconds: float
    first_token_seconds: float
    completion_tokens: int

    @property
    def tokens_per_second(self) -> float:
        return self.completion_tokens / self.elapsed_seconds if self.elapsed_seconds else 0.0


class ModelBackend(Protocol):
    @property
    def name(self) -> str: ...

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> str: ...

    @property
    def last_metrics(self) -> GenerationMetrics | None: ...


class LlamaCppBackend:
    """Runs a GGUF model locally through llama-cpp-python.

    The import is intentionally lazy so ARK's core/tests do not require the
    native dependency. Install with: pip install -e '.[local]'
    """

    def __init__(
        self,
        model_path: str | Path,
        *,
        context_size: int = 4096,
        threads: int | None = None,
    ):
        path = Path(model_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"GGUF model not found: {path}")
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError("Install the local backend with: pip install -e '.[local]'") from exc

        kwargs: dict[str, object] = {
            "model_path": str(path),
            "n_ctx": context_size,
            "verbose": False,
        }
        if threads is not None:
            kwargs["n_threads"] = threads
        self._llm = Llama(**kwargs)
        self._name = path.name
        self._last_metrics: GenerationMetrics | None = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def last_metrics(self) -> GenerationMetrics | None:
        return self._last_metrics

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> str:
        started = perf_counter()
        chunks = self._llm.create_chat_completion(
            messages=messages,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            stream=True,
        )
        parts: list[str] = []
        first_token_seconds: float | None = None
        for chunk in chunks:
            content = chunk["choices"][0].get("delta", {}).get("content")
            if content:
                if first_token_seconds is None:
                    first_token_seconds = perf_counter() - started
                parts.append(str(content))
        elapsed = perf_counter() - started
        text = "".join(parts).strip()
        token_count = len(self._llm.tokenize(text.encode("utf-8"), add_bos=False))
        self._last_metrics = GenerationMetrics(
            elapsed_seconds=elapsed,
            first_token_seconds=first_token_seconds or elapsed,
            completion_tokens=token_count,
        )
        return text


class EchoBackend:
    """Deterministic offline backend used only for tests and smoke checks."""

    name = "echo-test-backend"

    def __init__(self) -> None:
        self._last_metrics: GenerationMetrics | None = None

    @property
    def last_metrics(self) -> GenerationMetrics | None:
        return self._last_metrics

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> str:
        del config
        started = perf_counter()
        user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        response = f"ECHO: {user}"
        elapsed = perf_counter() - started
        self._last_metrics = GenerationMetrics(elapsed, elapsed, len(response.split()))
        return response
