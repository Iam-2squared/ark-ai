"""Immutable registry and registry-bound identities for ARK tool backends."""

from __future__ import annotations

import hashlib
import inspect
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .contracts import Effect, ToolBackend, ToolCall

_MAX_REGISTRATIONS = 256  # Bound hostile registration generators before hashing.
_MAX_REGISTRATION_TEXT = 256  # Bound individual tool/identity text before hashing.

# Bounds are an import-time admission contract, not mutable tuning knobs.
# Verify before touching a caller-owned tool identity or backend descriptor.
_ORIGINAL_ADMISSION_LIMITS = (_MAX_REGISTRATIONS, _MAX_REGISTRATION_TEXT)


def _require_original_registry_limits() -> None:
    if (
        type(_MAX_REGISTRATIONS) is not int
        or type(_MAX_REGISTRATION_TEXT) is not int
        or (_MAX_REGISTRATIONS, _MAX_REGISTRATION_TEXT)
        != _ORIGINAL_ADMISSION_LIMITS
    ):
        raise ValueError("registry admission limits changed")


_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON_DUMPS = json.dumps
_ORIGINAL_INSPECT = inspect
_ORIGINAL_GETATTR_STATIC = inspect.getattr_static


def _require_original_registry_digest() -> None:
    """Refuse substituted digest/JSON code before reading registry identities.

    These local in-process identity checks are not a security sandbox,
    authenticated backend attestation, or permission to dispatch a tool.
    """
    _require_original_registry_limits()
    if (
        # Module rebinding may itself install executable __getattr__ code.
        # Compare the module identity before fetching a digest/JSON member.
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_JSON_DUMPS
    ):
        raise ValueError("registry digest dependencies changed")



def _text(name: str, value: object) -> str:
    _require_original_registry_limits()
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty exact string")
    # Native and shell-facing identities must not embed NUL separators.
    # Refuse before inspecting backend.execute or serializing a revision.
    if "\x00" in value:
        raise ValueError(f"{name} contains a NUL separator")

    if len(value) > _MAX_REGISTRATION_TEXT:
        raise ValueError(f"{name} exceeds registry identifier budget")
    # Revision and bound-action identities serialize as UTF-8. Restrict the
    # actual byte budget and reject lone surrogate code points at ingress,
    # before a backend descriptor, registry digest or policy gate is touched.
    try:
        byte_count = len(value.encode("utf-8", errors="strict"))
    except UnicodeError as exc:
        raise ValueError(f"{name} is not valid UTF-8 text") from exc
    if byte_count > _MAX_REGISTRATION_TEXT:
        raise ValueError(f"{name} exceeds registry identifier budget")
    return value


def _canonical_json(value: object) -> bytes:
    _require_original_registry_digest()
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
    # The static lookup is a security-relevant local fault-injection seam.
    # If a caller replaces inspect.getattr_static, it could dynamically
    # evaluate a backend.execute property before a registry is even bound.
    if (
        inspect is not _ORIGINAL_INSPECT
        or inspect.getattr_static is not _ORIGINAL_GETATTR_STATIC
    ):
        raise TypeError("backend static inspection dependency changed")
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
        _require_original_registration_contract()
        _text("tool name", self.name)
        _text("capability", self.capability)
        if type(self.effect) is not Effect:
            raise TypeError("effect must be an Effect")
        _text("backend_id", self.backend_id)
        # The static check is the complete structural interface contract.
        # isinstance(..., a runtime-checkable Protocol) can invoke a hostile
        # backend's __getattribute__("execute") on Python 3.11. Registration
        # must not call user code, even to validate an inert mock backend.
        _backend_execute_descriptor(self.backend)


@dataclass(frozen=True, slots=True)
class BoundAction:
    """A ToolCall resolved against one exact immutable registry revision."""

    registry_revision: str
    call: ToolCall
    registration: ToolRegistration
    bound_action_id: str


_REGISTRATION_TYPE = ToolRegistration
_REGISTRATION_FIELDS = ("name", "capability", "effect", "backend_id", "backend")
_REGISTRATION_METHODS = ("__init__", "__post_init__")
_REGISTRATION_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_REGISTRATION_FIELDS = tuple(
    vars(_REGISTRATION_TYPE)[name] for name in _REGISTRATION_FIELDS
)
_ORIGINAL_REGISTRATION_METHODS = tuple(
    vars(_REGISTRATION_TYPE)[name] for name in _REGISTRATION_METHODS
)
_ORIGINAL_REGISTRATION_HOOKS = tuple(
    vars(_REGISTRATION_TYPE).get(name) for name in _REGISTRATION_HOOKS
)


def _require_original_registration_contract() -> None:
    """Reject class-level substitution before reading registration fields.

    Frozen instance fields do not prevent replacing a class slot descriptor
    with a property that executes arbitrary code during registry inspection.
    This local identity check is not remote backend attestation.
    """
    if (
        ToolRegistration is not _REGISTRATION_TYPE
        or any(
            vars(_REGISTRATION_TYPE).get(name) is not original
            for names, originals in (
                (_REGISTRATION_FIELDS, _ORIGINAL_REGISTRATION_FIELDS),
                (_REGISTRATION_METHODS, _ORIGINAL_REGISTRATION_METHODS),
                (_REGISTRATION_HOOKS, _ORIGINAL_REGISTRATION_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise ValueError("tool registration contract changed")


_BOUND_TYPE = BoundAction
_ORIGINAL_BOUND_INIT = vars(_BOUND_TYPE)["__init__"]
# Binding a frozen dataclass still reads its slots after construction.
# Replaced class descriptors/getters could execute caller-supplied code
# before the returned identity is verified. Pin them at module import.
_BOUND_FIELDS = ("registry_revision", "call", "registration", "bound_action_id")
_BOUND_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_BOUND_FIELDS = tuple(
    vars(_BOUND_TYPE)[name] for name in _BOUND_FIELDS
)
_ORIGINAL_BOUND_HOOKS = tuple(
    vars(_BOUND_TYPE).get(name) for name in _BOUND_HOOKS
)
_TOOL_CALL_TYPE = ToolCall
_TOOL_CALL_ORIGINALS = (
    "__init__", "__post_init__", "request_id", "arguments_sha256",
)
_ORIGINAL_TOOL_CALL_DESCRIPTORS = tuple(
    vars(_TOOL_CALL_TYPE)[name] for name in _TOOL_CALL_ORIGINALS
)
_TOOL_CALL_INPUT_FIELDS = ("tool", "capability", "scope", "arguments")
_ORIGINAL_TOOL_CALL_INPUT_FIELDS = tuple(
    vars(_TOOL_CALL_TYPE)[name] for name in _TOOL_CALL_INPUT_FIELDS
)
_TOOL_CALL_LOOKUP_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_TOOL_CALL_LOOKUP_HOOKS = tuple(
    vars(_TOOL_CALL_TYPE).get(name) for name in _TOOL_CALL_LOOKUP_HOOKS
)


def _require_original_toolcall_contract() -> None:
    # Dataclass initialization invokes __post_init__ dynamically. A patched
    # constructor/property must not run before registry identity validation.
    if (
        ToolCall is not _TOOL_CALL_TYPE
    ):
        raise ValueError("ToolCall identity constructor changed")
    if any(
        vars(_TOOL_CALL_TYPE).get(name) is not original
        for name, original in zip(
            _TOOL_CALL_ORIGINALS, _ORIGINAL_TOOL_CALL_DESCRIPTORS, strict=True,
        )
    ):
        raise ValueError("ToolCall identity constructor changed")
    # Class-level slot/getter replacement can execute hostile code before
    # even the first ToolCall field read in direct policy or registry paths.
    if (
        any(
            vars(_TOOL_CALL_TYPE).get(name) is not original
            for name, original in zip(
                _TOOL_CALL_INPUT_FIELDS,
                _ORIGINAL_TOOL_CALL_INPUT_FIELDS, strict=True,
            )
        )
        or any(
            vars(_TOOL_CALL_TYPE).get(name) is not original
            for name, original in zip(
                _TOOL_CALL_LOOKUP_HOOKS,
                _ORIGINAL_TOOL_CALL_LOOKUP_HOOKS, strict=True,
            )
        )
    ):
        raise ValueError("ToolCall identity constructor changed")



def _require_original_bound_constructor() -> None:
    # A class-level constructor can be monkeypatched even for frozen slots.
    # Reject the replacement before any injected code can execute.
    if (
        BoundAction is not _BOUND_TYPE
        or vars(_BOUND_TYPE).get("__init__") is not _ORIGINAL_BOUND_INIT
        or any(
            vars(_BOUND_TYPE).get(name) is not original
            for name, original in zip(
                _BOUND_FIELDS, _ORIGINAL_BOUND_FIELDS, strict=True,
            )
        )
        or any(
            vars(_BOUND_TYPE).get(name) is not original
            for name, original in zip(
                _BOUND_HOOKS, _ORIGINAL_BOUND_HOOKS, strict=True,
            )
        )
    ):
        raise ValueError("registry bound result constructor changed")


class ToolRegistry:
    """Immutable exact-name registry with deterministic revision identity."""

    _SCHEMA_VERSION = 1

    def __init__(self, registrations: Iterable[ToolRegistration]) -> None:
        _require_original_registration_contract()
        _require_original_registry_digest()
        # Registrations can arrive from caller-controlled generators. Never
        # exhaust an unbounded iterator before enforcing the construction
        # budget, and never silently accept a reflected mutation of an
        # earlier yielded registration while reading a later one.
        snapshot: list[ToolRegistration] = []
        retained: list[tuple[ToolRegistration, str, str, Effect, str, ToolBackend, object]] = []

        def assert_ingress_epoch() -> None:
            _require_original_registration_contract()
            _require_original_registry_digest()
            for entry, name, capability, effect, backend_id, backend, execute in retained:
                try:
                    stable = (
                        type(entry) is ToolRegistration
                        and type(entry.name) is str and entry.name is name
                        and type(entry.capability) is str
                        and entry.capability is capability
                        and entry.effect is effect
                        and type(entry.backend_id) is str
                        and entry.backend_id is backend_id
                        and entry.backend is backend
                        and _backend_execute_descriptor(backend) is execute
                    )
                except (AttributeError, TypeError, ValueError) as exc:
                    raise ValueError(
                        "registered tool changed during registry construction"
                    ) from exc
                if not stable:
                    raise ValueError(
                        "registered tool changed during registry construction"
                    )

        for registration in registrations:
            assert_ingress_epoch()
            if len(snapshot) >= _MAX_REGISTRATIONS:
                raise ValueError("registry construction budget exceeded")
            if type(registration) is not ToolRegistration:
                raise TypeError("registrations must contain exact ToolRegistration values")
            retained.append((
                registration, registration.name, registration.capability,
                registration.effect, registration.backend_id, registration.backend,
                _backend_execute_descriptor(registration.backend),
            ))
            snapshot.append(registration)
            assert_ingress_epoch()
        # StopIteration itself can run user code in a generator's finally.
        assert_ingress_epoch()

        ordered = sorted(snapshot, key=lambda registration: registration.name)
        assert_ingress_epoch()
        if len({registration.name for registration in ordered}) != len(ordered):
            raise ValueError("duplicate tool name")

        mapping = {registration.name: registration for registration in ordered}
        assert_ingress_epoch()
        self._registrations: Mapping[str, ToolRegistration] = MappingProxyType(mapping)
        self._registry_mapping_epoch = self._registrations
        # Capture the FIRST-observed values rather than values recomputed
        # after revision serialization (itself a callback boundary).
        self._registration_epoch = tuple(sorted(retained, key=lambda row: row[1]))
        self._revision = self._compute_revision(ordered)
        self._revision_epoch = self._revision
        assert_ingress_epoch()
        self._assert_registration_epoch()

    def _assert_registration_epoch(self) -> None:
        """Detect reflected drift of registered identity without executing tools.

        This is only a local drift check; it is NOT backend attestation against
        malicious in-process rewriting of every private reference.
        """
        _require_original_registration_contract()
        _require_original_registry_digest()
        if (
            type(self._revision) is not str
            or self._revision is not self._revision_epoch
        ):
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
                or entry.name is not name or entry.capability is not capability
                or entry.effect is not effect or entry.backend_id is not backend_id
                or entry.backend is not backend
                or current_execute is not execute
                or self._registrations.get(name) is not entry
            ):
                raise ValueError("registered tool identity drifted after construction")
        _require_original_registry_digest()
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
        _require_original_registration_contract()
        _require_original_registry_digest()
        if type(call) is not ToolCall:
            raise TypeError("call must be an exact ToolCall")
        _require_original_toolcall_contract()
        # Direct resolution must obey the same original-input boundary as
        # bind(). A callback in get() may reflectively retarget a frozen call
        # or alter registered backend/effect identity after its first check.
        # Capture the ORIGINAL caller-owned scalar carriers before ToolCall
        # construction, which may itself be a synthetic callback boundary.
        original = (call.tool, call.capability, call.scope, call.arguments)
        stable = ToolCall(*original)
        _require_original_toolcall_contract()
        epoch = (stable.tool, stable.capability, stable.scope, stable.request_id)


        def assert_call_epoch() -> None:
            _require_original_registry_digest()
            _require_original_toolcall_contract()
            if (
                type(call.tool) is not str
                or type(call.capability) is not str
                or type(call.scope) is not str
                or (call.tool, call.capability, call.scope, call.request_id)
                != epoch
                or any(
                    value is not first
                    for value, first in zip(
                        (call.tool, call.capability, call.scope, call.arguments),
                        original, strict=True,
                    )
                )
            ):
                raise ValueError("ToolCall identity changed during registry resolution")
            _require_original_toolcall_contract()

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
        _require_original_toolcall_contract()
        return registration

    def bind(self, call: ToolCall) -> BoundAction:
        _require_original_registration_contract()
        _require_original_registry_digest()
        # Call objects are frozen, but reflected mutation is still possible
        # during a registry lookup. Refuse a bound ID based on mixed snapshots.
        # This check is not an authorization grant or a concurrency primitive.
        if type(call) is not ToolCall:
            raise TypeError("call must be an exact ToolCall")
        _require_original_bound_constructor()
        _require_original_toolcall_contract()
        # Preserve the *original* argument carrier as well as its digest.
        # A callback can replace a frozen ToolCall's arguments with a new,
        # value-equal mapping after resolve() has finished its own checks.
        # That is a new caller input epoch even when request_id is unchanged.
        original = (call.tool, call.capability, call.scope, call.arguments)
        stable = ToolCall(*original)
        _require_original_toolcall_contract()
        original_request_id = stable.request_id

        def assert_call_unchanged() -> None:
            _require_original_registry_digest()
            _require_original_toolcall_contract()
            if (
                type(call.tool) is not str
                or type(call.capability) is not str
                or type(call.scope) is not str
                or (call.tool, call.capability, call.scope)
                != (stable.tool, stable.capability, stable.scope)
                or call.request_id != original_request_id
                or any(
                    value is not first
                    for value, first in zip(
                        (call.tool, call.capability, call.scope, call.arguments),
                        original, strict=True,
                    )
                )
            ):
                raise ValueError("ToolCall identity changed during registry binding")
            _require_original_toolcall_contract()

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
        # A reentrant hash or registry lookup can replace the frozen result
        # constructor after the initial admission check.
        _require_original_bound_constructor()
        bound = _BOUND_TYPE(
            registry_revision=revision,
            call=call,
            registration=registration,
            bound_action_id=bound_action_id,
        )
        # BoundAction is a frozen carrier, not an immutable proof. A patched
        # constructor can reflectively mutate the call, registration or its
        # own fields *after* the earlier hash/registry checks. Never return
        # an inconsistent action identity or authorize backend execution.
        assert_call_unchanged()
        self._assert_registration_epoch()
        assert_call_unchanged()
        _require_original_bound_constructor()
        if (
            type(bound) is not _BOUND_TYPE
            or bound.registry_revision is not revision
            or bound.call is not call
            or bound.registration is not registration
            or bound.bound_action_id is not bound_action_id
        ):
            raise ValueError("registry bound result changed during construction")
        return bound

    @classmethod
    def _compute_revision(cls, registrations: list[ToolRegistration]) -> str:
        _require_original_registry_digest()
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
