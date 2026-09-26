"""Stable contracts for ARK's local-first long-term memory."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Protocol, runtime_checkable


class MemoryConflictError(RuntimeError):
    """Raised when optimistic revision expectations do not match stored state."""


class MemorySchemaError(RuntimeError):
    """Raised when persisted memory cannot be safely interpreted."""


@dataclass(frozen=True, slots=True)
class MemoryScope:
    owner_id: str
    namespace: str = "default"

    def __post_init__(self) -> None:
        _text("owner_id", self.owner_id, 256)
        _text("namespace", self.namespace, 256)


@dataclass(frozen=True, slots=True)
class MemoryWrite:
    scope: MemoryScope
    source_id: str
    content: str
    metadata: Mapping[str, str] = field(default_factory=dict)
    expires_at_ms: int | None = None

    def __post_init__(self) -> None:
        _text("source_id", self.source_id, 512)
        _text("content", self.content, 1_000_000)
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")
        if len(self.metadata) > 64:
            raise ValueError("metadata exceeds 64 entries")
        snapshot: dict[str, str] = {}
        for key, value in self.metadata.items():
            _text("metadata key", key, 4096)
            if not isinstance(value, str):
                raise TypeError("metadata values must be strings")
            if len(value) > 4096:
                raise ValueError("metadata value exceeds maximum length")
            snapshot[key] = value
        object.__setattr__(self, "metadata", MappingProxyType(snapshot))
        if self.expires_at_ms is not None and (
            type(self.expires_at_ms) is not int or self.expires_at_ms < 0
        ):
            raise ValueError("expires_at_ms must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    memory_id: str
    scope: MemoryScope
    source_id: str
    content: str
    metadata: Mapping[str, str]
    created_at_ms: int
    updated_at_ms: int
    expires_at_ms: int | None
    revision: int
    content_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True, slots=True)
class MemoryQuery:
    scope: MemoryScope
    text: str = ""
    limit: int = 10
    include_expired: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError("text must be a string")
        if type(self.limit) is not int or not 1 <= self.limit <= 100:
            raise ValueError("limit must be an integer from 1 to 100")
        if type(self.include_expired) is not bool:
            raise TypeError("include_expired must be a bool")


@dataclass(frozen=True, slots=True)
class MemoryEvent:
    event_id: int
    memory_id: str
    scope: MemoryScope
    operation: str
    revision: int
    occurred_at_ms: int


@runtime_checkable
class MemoryBackend(Protocol):
    def put(self, write: MemoryWrite, *, expected_revision: int = 0) -> MemoryRecord: ...

    def get(
        self, memory_id: str, scope: MemoryScope, *, include_expired: bool = False
    ) -> MemoryRecord | None: ...

    def search(self, query: MemoryQuery) -> list[MemoryRecord]: ...

    def delete(self, memory_id: str, scope: MemoryScope, *, expected_revision: int) -> bool: ...

    def purge_expired(self, *, scope: MemoryScope | None = None) -> int: ...

    def events(
        self, scope: MemoryScope, *, after_event_id: int = 0, limit: int = 100
    ) -> list[MemoryEvent]: ...


def _text(name: str, value: object, max_length: int) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must not be blank")
    if len(value) > max_length:
        raise ValueError(f"{name} exceeds maximum length {max_length}")
