"""Stable contracts for ARK tool, planning, and action foundations."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Protocol, runtime_checkable


class PermissionDenied(RuntimeError):
    pass


class PlanConflictError(RuntimeError):
    pass


class ActionAuditSchemaError(RuntimeError):
    pass


class Effect(StrEnum):
    READ = "read"
    WRITE = "write"


class StepState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    capability: str
    effect: Effect = Effect.READ

    def __post_init__(self) -> None:
        _text("tool name", self.name)
        _text("capability", self.capability)
        if type(self.effect) is not Effect:
            raise TypeError("effect must be an Effect")


@dataclass(frozen=True, slots=True)
class ToolCall:
    tool: str
    capability: str
    scope: str
    arguments: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _text("tool", self.tool)
        _text("capability", self.capability)
        _text("scope", self.scope)
        if not isinstance(self.arguments, Mapping):
            raise TypeError("arguments must be a mapping")
        try:
            frozen = _freeze_json(self.arguments)
            _canonical_json(frozen)
        except (TypeError, ValueError, UnicodeError) as exc:
            raise ValueError("arguments must be canonical JSON-compatible values") from exc
        object.__setattr__(self, "arguments", frozen)

    @property
    def arguments_sha256(self) -> str:
        return hashlib.sha256(_canonical_json(self.arguments)).hexdigest()

    @property
    def request_id(self) -> str:
        payload = {
            "arguments_sha256": self.arguments_sha256,
            "capability": self.capability,
            "scope": self.scope,
            "tool": self.tool,
        }
        return "act_" + hashlib.sha256(_canonical_json(payload)).hexdigest()


@dataclass(frozen=True, slots=True)
class CapabilityGrant:
    capability: str
    scope: str
    expires_at_ms: int | None = None

    def __post_init__(self) -> None:
        _text("capability", self.capability)
        _text("scope", self.scope)
        if self.expires_at_ms is not None and (
            type(self.expires_at_ms) is not int
            or not 0 <= self.expires_at_ms <= (1 << 63) - 1
        ):
            raise ValueError("expires_at_ms must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class OneShotAuthorization:
    token_id: str
    request_id: str
    expires_at_ms: int

    def __post_init__(self) -> None:
        _text("token_id", self.token_id)
        if type(self.request_id) is not str or re.fullmatch(
            r"act_[0-9a-f]{64}", self.request_id
        ) is None:
            raise ValueError("request_id must identify one canonical action request")
        if (
            type(self.expires_at_ms) is not int
            or not 0 <= self.expires_at_ms <= (1 << 63) - 1
        ):
            raise ValueError("expires_at_ms must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class ToolResult:
    request_id: str
    result: object


@dataclass(frozen=True, slots=True)
class PlanStep:
    step_id: str
    call: ToolCall
    depends_on: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text("step_id", self.step_id)
        if type(self.call) is not ToolCall:
            raise TypeError("call must be an exact ToolCall")
        if isinstance(self.depends_on, (str, bytes)) or not isinstance(
            self.depends_on, Sequence
        ):
            raise TypeError("depends_on must be an ordered sequence of step IDs")
        dependencies = tuple(self.depends_on)
        for dependency in dependencies:
            _text("dependency step_id", dependency)
        if len(set(dependencies)) != len(dependencies):
            raise ValueError("depends_on may not contain duplicates")
        object.__setattr__(self, "depends_on", dependencies)


@dataclass(frozen=True, slots=True)
class PlanStepStatus:
    step_id: str
    state: StepState
    revision: int = 0

    def __post_init__(self) -> None:
        _text("step_id", self.step_id)
        if type(self.state) is not StepState:
            raise TypeError("state must be a StepState")
        if (
            type(self.revision) is not int
            or not 0 <= self.revision <= 2**63 - 1
        ):
            raise ValueError("revision must be a non-negative integer within SQLite range")


@dataclass(frozen=True, slots=True)
class ActionAuditEvent:
    event_id: int
    request_id: str
    tool: str
    capability: str
    scope: str
    arguments_sha256: str
    outcome: str
    occurred_at_ms: int


@runtime_checkable
class ToolBackend(Protocol):
    def execute(self, call: ToolCall) -> object: ...


# Bound caller-controlled structures before hashing, registry admission or a
# WRITE token check. These are local fail-closed resource limits, not an
# authorization policy or a change to valid canonical request identifiers.
_MAX_ARGUMENT_NODES = 4096
_MAX_ARGUMENT_DEPTH = 32
_MAX_ARGUMENT_TEXT_CHARS = 65536
_MAX_ARGUMENT_TEXT_BYTES = 256 * 1024


def _freeze_json(value: object) -> object:
    nodes = 0
    text_bytes = 0

    def charge_text(text: str) -> None:
        nonlocal text_bytes
        if len(text) > _MAX_ARGUMENT_TEXT_CHARS:
            raise ValueError("JSON argument text budget exceeded")
        text_bytes += len(text.encode("utf-8"))
        if text_bytes > _MAX_ARGUMENT_TEXT_BYTES:
            raise ValueError("JSON argument text budget exceeded")

    def freeze(item: object, depth: int) -> object:
        nonlocal nodes
        if depth > _MAX_ARGUMENT_DEPTH:
            raise ValueError("JSON argument nesting budget exceeded")
        nodes += 1
        if nodes > _MAX_ARGUMENT_NODES:
            raise ValueError("JSON argument node budget exceeded")
        if item is None or type(item) in {bool, int}:
            return item
        if type(item) is str:
            charge_text(item)
            return item
        if type(item) is float:
            _canonical_json(item)
            return item
        if isinstance(item, Mapping):
            snapshot: dict[str, object] = {}
            for key, child in item.items():
                if type(key) is not str:
                    raise TypeError("JSON object keys must be exact strings")
                charge_text(key)
                if key in snapshot:
                    raise ValueError("duplicate JSON object key")
                snapshot[key] = freeze(child, depth + 1)
            return MappingProxyType(snapshot)
        if isinstance(item, (list, tuple)):
            return tuple(freeze(child, depth + 1) for child in item)
        raise TypeError(f"unsupported JSON value type: {type(item).__name__}")

    return freeze(value, 0)


def _jsonable(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    return value


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(
            _jsonable(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _text(name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty exact string")
