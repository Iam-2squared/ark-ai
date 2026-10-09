"""Immutable registry and registry-bound identities for ARK tool backends."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .contracts import Effect, ToolBackend, ToolCall


def _text(name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty exact string")
    return value


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


@dataclass(frozen=True, slots=True)
class ToolRegistration:
    """One immutable registry entry."""

    name: str
    capability: str
    effect: Effect
    backend_id: str
    backend: ToolBackend

    def __post_init__(self) -> None:
        _text("tool name", self.name)
        _text("capability", self.capability)
        if type(self.effect) is not Effect:
            raise TypeError("effect must be an Effect")
        _text("backend_id", self.backend_id)
        if not isinstance(self.backend, ToolBackend):
            raise TypeError("backend must implement ToolBackend")


@dataclass(frozen=True, slots=True)
class BoundAction:
    """A ToolCall resolved against one exact immutable registry revision."""

    registry_revision: str
    call: ToolCall
    registration: ToolRegistration
    bound_action_id: str


class ToolRegistry:
    """Immutable exact-name registry with deterministic revision identity."""

    _SCHEMA_VERSION = 1

    def __init__(self, registrations: Iterable[ToolRegistration]) -> None:
        snapshot = tuple(registrations)
        for registration in snapshot:
            if type(registration) is not ToolRegistration:
                raise TypeError("registrations must contain exact ToolRegistration values")

        ordered = sorted(snapshot, key=lambda registration: registration.name)
        if len({registration.name for registration in ordered}) != len(ordered):
            raise ValueError("duplicate tool name")

        mapping = {registration.name: registration for registration in ordered}
        self._registrations: Mapping[str, ToolRegistration] = MappingProxyType(mapping)
        self._revision = self._compute_revision(ordered)

    @property
    def revision(self) -> str:
        return self._revision

    @property
    def registrations(self) -> Mapping[str, ToolRegistration]:
        return self._registrations

    def get(self, name: str) -> ToolRegistration:
        _text("tool name", name)
        try:
            return self._registrations[name]
        except KeyError as exc:
            raise KeyError(f"unknown tool: {name}") from exc

    def resolve(self, call: ToolCall) -> ToolRegistration:
        if type(call) is not ToolCall:
            raise TypeError("call must be an exact ToolCall")
        registration = self.get(call.tool)
        if registration.capability != call.capability:
            raise ValueError("tool call capability does not match registry")
        return registration

    def bind(self, call: ToolCall) -> BoundAction:
        registration = self.resolve(call)
        payload = {
            "backend_id": registration.backend_id,
            "capability": registration.capability,
            "effect": registration.effect.value,
            "registry_revision": self.revision,
            "request_id": call.request_id,
            "tool": registration.name,
        }
        bound_action_id = "bound_" + hashlib.sha256(_canonical_json(payload)).hexdigest()
        return BoundAction(
            registry_revision=self.revision,
            call=call,
            registration=registration,
            bound_action_id=bound_action_id,
        )

    @classmethod
    def _compute_revision(cls, registrations: list[ToolRegistration]) -> str:
        payload = {
            "schema_version": cls._SCHEMA_VERSION,
            "tools": [
                {
                    "backend_id": registration.backend_id,
                    "capability": registration.capability,
                    "effect": registration.effect.value,
                    "name": registration.name,
                }
                for registration in registrations
            ],
        }
        return "tools_" + hashlib.sha256(_canonical_json(payload)).hexdigest()
