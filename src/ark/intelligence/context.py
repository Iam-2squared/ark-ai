"""Budget current conversation using whole-turn eviction and transactional preparation."""

from __future__ import annotations

from collections.abc import Callable

from .contracts import Message, PreparedContext

TokenCounter = Callable[[tuple[Message, ...]], int]


class ContextBudgetError(ValueError):
    """The system plus current input and output reserve cannot fit."""


def estimate_tokens(messages: tuple[Message, ...]) -> int:
    """UTF-8-byte heuristic, including framing; not an exact model tokenizer."""
    return 16 + sum(len(m.content.encode("utf-8")) + 32 for m in messages)


class ContextManager:
    def __init__(
        self,
        capacity: int,
        *,
        safety_margin: int = 64,
        counter: TokenCounter = estimate_tokens,
        counting_method: str = "utf8_bytes_plus_framing_estimate_v1",
    ):
        if type(capacity) is not int or capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        if type(safety_margin) is not int or safety_margin < 0:
            raise ValueError("safety margin must be a nonnegative integer")
        self.capacity, self.safety_margin = capacity, safety_margin
        self.counter, self.counting_method = counter, counting_method

    def prepare(
        self,
        system: str,
        history: tuple[Message, ...],
        user: str,
        output_tokens: int,
    ) -> PreparedContext:
        if type(output_tokens) is not int or output_tokens <= 0:
            raise ValueError("output reserve must be a positive integer")
        if len(history) % 2 or any(
            m.role != ("user" if i % 2 == 0 else "assistant") for i, m in enumerate(history)
        ):
            raise ValueError("history must contain ordered complete user/assistant turns")
        kept = history
        while True:
            messages = (Message("system", system), *kept, Message("user", user))
            count = self.counter(messages)
            if type(count) is not int or count < 0:
                raise ValueError("token counter must return a nonnegative integer")
            if count + output_tokens + self.safety_margin <= self.capacity:
                return PreparedContext(
                    messages,
                    kept,
                    count,
                    self.counting_method,
                    (len(history) - len(kept)) // 2,
                    self.capacity,
                    output_tokens,
                    self.safety_margin,
                )
            if not kept:
                raise ContextBudgetError("system and current input exceed context budget")
            kept = kept[2:]
