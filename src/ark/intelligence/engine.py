"""Transactional current-conversation coordinator over the V1 backend protocol."""

from __future__ import annotations

import math
from time import perf_counter
from uuid import uuid4

from ..models import GenerationConfig, ModelBackend
from .context import ContextManager
from .contracts import Capabilities, GenerationRequest, Message, Response, TaskMode
from .policy import POLICY_VERSION, system_instruction


class Intelligence:
    def __init__(
        self,
        backend: ModelBackend,
        capabilities: Capabilities,
        *,
        generation: GenerationConfig | None = None,
        context: ContextManager | None = None,
    ):
        if not capabilities.chat_template_supported:
            raise ValueError("a chat-compatible backend/template is required")
        self.backend, self.capabilities = backend, capabilities
        self.generation = generation or GenerationConfig()
        self.context = context or ContextManager(capabilities.context_capacity)
        if self.context.capacity > capabilities.context_capacity:
            raise ValueError("context budget exceeds configured backend capacity")
        self._history: tuple[Message, ...] = ()
        self._validate_controls()

    def _validate_controls(self) -> None:
        g = self.generation
        if type(g.max_tokens) is not int or g.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if not math.isfinite(g.temperature) or g.temperature < 0:
            raise ValueError("temperature must be finite and nonnegative")
        if not math.isfinite(g.top_p) or not 0 < g.top_p <= 1:
            raise ValueError("top_p must be in (0, 1]")
        if type(g.seed) is not int:
            raise ValueError("seed must be an integer")
        if not {"max_tokens", "temperature", "top_p", "seed"}.issubset(
            self.capabilities.generation_controls
        ):
            raise ValueError("backend does not declare required generation controls")

    @property
    def history(self) -> tuple[Message, ...]:
        return self._history

    def reset(self) -> None:
        self._history = ()

    def chat(self, text: str, mode: TaskMode = TaskMode.CONCISE) -> Response:
        mode = TaskMode(mode)
        text = text.strip()
        if not text:
            raise ValueError("message must not be empty")
        prepared = self.context.prepare(
            system_instruction(mode),
            self._history,
            text,
            self.generation.max_tokens,
        )
        request = GenerationRequest(str(uuid4()), mode, prepared, self.generation, POLICY_VERSION)
        started = perf_counter()
        answer = self.backend.generate([m.to_dict() for m in prepared.messages], self.generation)
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError("model returned an empty or invalid response")
        answer = answer.strip()
        latency = perf_counter() - started
        metrics = getattr(self.backend, "last_metrics", None)
        response = Response(
            request,
            answer,
            latency,
            metrics.first_token_seconds if metrics else None,
            metrics.completion_tokens if metrics else None,
            metrics.tokens_per_second if metrics else None,
        )
        self._history = (
            *prepared.retained_history,
            Message("user", text),
            Message("assistant", answer),
        )
        return response
