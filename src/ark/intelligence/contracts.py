"""Immutable boundaries between policy, current context, and model runtime."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ..models import GenerationConfig


class TaskMode(StrEnum):
    CONCISE = "concise"
    EXPLANATION = "explanation"
    CODING = "coding"
    STRUCTURED = "structured"


@dataclass(frozen=True)
class Message:
    role: str
    content: str

    def __post_init__(self) -> None:
        if self.role not in {"system", "user", "assistant"}:
            raise ValueError("unsupported message role")
        if not self.content.strip():
            raise ValueError("empty message")

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True)
class Capabilities:
    context_capacity: int
    chat_template_supported: bool
    source: str
    languages: tuple[str, ...] = ()
    coding_evidence: str = "not_measured"
    generation_controls: tuple[str, ...] = ("max_tokens", "temperature", "top_p", "seed")

    def __post_init__(self) -> None:
        if type(self.context_capacity) is not int or self.context_capacity <= 0:
            raise ValueError("context capacity must be a positive integer")
        if not self.source.strip():
            raise ValueError("capability metadata requires provenance")


@dataclass(frozen=True)
class PreparedContext:
    messages: tuple[Message, ...]
    retained_history: tuple[Message, ...]
    prompt_tokens_estimate: int
    counting_method: str
    dropped_turns: int
    context_capacity: int
    reserved_output_tokens: int
    safety_margin: int

    @property
    def utilization_estimate(self) -> float:
        return (
            self.prompt_tokens_estimate + self.reserved_output_tokens + self.safety_margin
        ) / self.context_capacity


@dataclass(frozen=True)
class GenerationRequest:
    request_id: str
    mode: TaskMode
    context: PreparedContext
    controls: GenerationConfig
    policy_version: str


@dataclass(frozen=True)
class Response:
    request: GenerationRequest
    text: str
    latency_seconds: float
    first_token_seconds: float | None
    completion_tokens_estimate: int | None
    tokens_per_second_estimate: float | None
