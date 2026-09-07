"""Conversation core for ARK V1."""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import GenerationConfig, ModelBackend

DEFAULT_SYSTEM_PROMPT = (
    "You are ARK, a local-first personal AI. Be accurate, concise, and explicit when uncertain."
)


@dataclass
class ArkCore:
    backend: ModelBackend
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    history: list[dict[str, str]] = field(default_factory=list)

    def reset(self) -> None:
        self.history.clear()

    def messages(self, user_text: str) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": self.system_prompt},
            *self.history,
            {"role": "user", "content": user_text},
        ]

    def chat(self, user_text: str) -> str:
        text = user_text.strip()
        if not text:
            raise ValueError("message must not be empty")
        response = self.backend.generate(self.messages(text), self.generation).strip()
        self.history.extend(
            [
                {"role": "user", "content": text},
                {"role": "assistant", "content": response},
            ]
        )
        return response
