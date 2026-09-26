"""Stable contracts for ARK tool, planning, and action foundations."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Protocol, runtime_checkable


class PermissionDenied(RuntimeError):
    pass


class PlanConflictError(RuntimeError):
    pass


class ActionAuditSchemaError(RuntimeError):
    pass


class Effect(str, Enum):
    READ = "read"
    WRITE = "write"


class StepState(str, Enum):
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
        if not isinstance(self.effect, Effect):
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
        try:
            _canonical_json(dict(self.arguments))
        except (TypeError, ValueError) as exc:
            raise ValueError("arguments must be canonical JSON-compatible values") from exc

    @property
    def arguments_sha256(self) -> str:
        return hashlib.sha256(_canonical_json(dict(self.arguments))).hexdigest()

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
            type(self.expires_at_ms) is not int or self.expires_at_ms < 0
        ):
            raise ValueError("expires_at_ms must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class OneShotAuthorization:
    token_id: str
    request_id: str
    expires_at_ms: int

    def __post_init__(self) -> None:
        _text("token_id", self.token_id)
        if not self.request_id.startswith("act_"):
            raise ValueError("request_id must identify one exact action request")
        if type(self.expires_at_ms) is not int or self.expires_at_ms < 0:
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
        if len(set(self.depends_on)) != len(self.depends_on):
            raise ValueError("depends_on may not contain duplicates")


@dataclass(frozen=True, slots=True)
class PlanStepStatus:
    step_id: str
    state: StepState
    revision: int = 0

    def __post_init__(self) -> None:
        if type(self.revision) is not int or self.revision < 0:
            raise ValueError("revision must be a non-negative integer")


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


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _text(name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
