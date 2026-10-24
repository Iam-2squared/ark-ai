"""Immutable registry and registry-bound identities for ARK tool backends."""

from __future__ import annotations

import hashlib
import inspect
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


def _backend_execute_descriptor(backend: object) -> object:
    """Inspect execution interface without invoking a property or backend."""
    try:
        descriptor = inspect.getattr_static(backend, "execute")
    except AttributeError as exc:
        raise TypeError("backend must expose a callable execute method") from exc
    if not callable(descriptor):
        raise TypeError("backend execute must be statically callable")
    return descriptor


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
        _backend_execute_descriptor(self.backend)
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
        # Pin the exact mapping object to detect reflected replacement, including
        # a value-equal replacement proxy. Never dispatch a backend here.
        self._registry_mapping_epoch = self._registrations
        self._revision = self._compute_revision(ordered)
        self._registration_epoch = tuple(
            (
                entry, entry.name, entry.capability, entry.effect,
                entry.backend_id, entry.backend, _backend_execute_descriptor(entry.backend),
            )
            for entry in ordered
        )

    def _assert_registration_epoch(self) -> None:
        """Detect reflected drift of registered identity without executing tools.

        This is only a local drift check; it is NOT backend attestation against
        malicious in-process rewriting of every private reference.
        """
        if type(self._revision) is not str:
            raise ValueError("registry revision carrier changed")
        if (
            type(self._registrations) is not MappingProxyType
            or self._registrations is not self._registry_mapping_epoch
        ):
            raise ValueError("registry identity map changed after construction")
        entries = self._registration_epoch
        if type(entries) is not tuple or len(entries) != len(self._registrations):
            raise ValueError("registry epoch structure was changed")
        for entry, name, capability, effect, backend_id, backend, execute in entries:
            try:
                current_execute = _backend_execute_descriptor(backend)
            except TypeError as exc:
                raise ValueError("backend execute interface changed") from exc
            if (
                type(entry) is not ToolRegistration
                or type(name) is not str or type(capability) is not str
                or type(effect) is not Effect or type(backend_id) is not str
                or type(entry.name) is not str or type(entry.capability) is not str
                or type(entry.backend_id) is not str
                or entry.name != name or entry.capability != capability
                or entry.effect is not effect or entry.backend_id != backend_id
                or entry.backend is not backend
                or current_execute is not execute
                or self._registrations.get(name) is not entry
            ):
                raise ValueError("registered tool identity drifted after construction")
        if self._compute_revision([item[0] for item in entries]) != self._revision:
            raise ValueError("registry revision drifted after construction")

    @property
    def revision(self) -> str:
        self._assert_registration_epoch()
        return self._revision

    @property
    def registrations(self) -> Mapping[str, ToolRegistration]:
        self._assert_registration_epoch()
        return self._registrations

    def get(self, name: str) -> ToolRegistration:
        _text("tool name", name)
        self._assert_registration_epoch()
        try:
            return self._registrations[name]
        except KeyError as exc:
            raise KeyError(f"unknown tool: {name}") from exc

    def resolve(self, call: ToolCall) -> ToolRegistration:
        if type(call) is not ToolCall:
            raise TypeError("call must be an exact ToolCall")
        # Direct resolution must obey the same original-input boundary as
        # bind(). A callback in get() may reflectively retarget a frozen call
        # or alter registered backend/effect identity after its first check.
        stable = ToolCall(call.tool, call.capability, call.scope, call.arguments)
        epoch = (
            stable.tool, stable.capability, stable.scope, stable.request_id,
            call.arguments,
        )

        def assert_call_epoch() -> None:
            if (
                type(call.tool) is not str
                or type(call.capability) is not str
                or type(call.scope) is not str
                or (call.tool, call.capability, call.scope, call.request_id)
                != epoch[:4]
                or call.arguments is not epoch[4]
            ):
                raise ValueError("ToolCall identity changed during registry resolution")

        assert_call_epoch()
        registration = self.get(stable.tool)
        assert_call_epoch()
        self._assert_registration_epoch()
        assert_call_epoch()
        # A replaced get() may return an unregistered backend or a cloned
        # entry while leaving the immutable registry map itself untouched.
        # Registry revision identity only attests entries in that pinned map.
        if self._registrations.get(stable.tool) is not registration:
            raise ValueError("registry lookup returned unregistered identity")
        if registration.capability != stable.capability:
            raise ValueError("tool call capability does not match registry")
        return registration

    def bind(self, call: ToolCall) -> BoundAction:
        # Call objects are frozen, but reflected mutation is still possible
        # during a registry lookup. Refuse a bound ID based on mixed snapshots.
        # This check is not an authorization grant or a concurrency primitive.
        if type(call) is not ToolCall:
            raise TypeError("call must be an exact ToolCall")
        stable = ToolCall(call.tool, call.capability, call.scope, call.arguments)
        original_request_id = stable.request_id

        def assert_call_unchanged() -> None:
            if (
                type(call.tool) is not str
                or type(call.capability) is not str
                or type(call.scope) is not str
                or (call.tool, call.capability, call.scope)
                != (stable.tool, stable.capability, stable.scope)
                or call.request_id != original_request_id
            ):
                raise ValueError("ToolCall identity changed during registry binding")

        assert_call_unchanged()
        registration = self.resolve(call)
        assert_call_unchanged()
        revision = self.revision
        assert_call_unchanged()
        payload = {
            "backend_id": registration.backend_id,
            "capability": registration.capability,
            "effect": registration.effect.value,
            "registry_revision": revision,
            "request_id": original_request_id,
            "tool": registration.name,
        }
        bound_action_id = "bound_" + hashlib.sha256(_canonical_json(payload)).hexdigest()
        assert_call_unchanged()
        self._assert_registration_epoch()
        assert_call_unchanged()
        return BoundAction(
            registry_revision=revision,
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
