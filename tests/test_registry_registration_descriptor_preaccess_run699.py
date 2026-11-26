"""Local ToolRegistration descriptor custody, without backend dispatch.

This only rejects in-process reflection of registered identity. It is not a
trusted backend attestation, a permission grant or durable WRITE authorization.
"""

from __future__ import annotations

from contextlib import contextmanager

import pytest

import ark.agency.registry as registry_module
from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("registry must not dispatch backend")


def _fixture() -> tuple[ToolRegistry, ToolRegistration, ToolCall, NeverExecute]:
    backend = NeverExecute()
    registration = ToolRegistration(
        "offline.fixture", "offline.read", Effect.READ, "mock:offline", backend,
    )
    registry = ToolRegistry((registration,))
    call = ToolCall("offline.fixture", "offline.read", "local:fixture", {"a": 1})
    return registry, registration, call, backend


@contextmanager
def _replace_class_member(member: str, touched: list[str]):
    missing = object()
    original = vars(ToolRegistration).get(member, missing)

    def hostile(*_args, **_kwargs):
        touched.append(member)
        raise AssertionError("substituted registration descriptor was executed")

    # Do not rewrite the CPython __new__ slot in a shared pytest process.
    substitute = property(hostile) if member in {
        "name", "capability", "effect", "backend_id", "backend",
    } else hostile
    setattr(ToolRegistration, member, substitute)
    try:
        yield
    finally:
        if original is missing:
            delattr(ToolRegistration, member)
        else:
            setattr(ToolRegistration, member, original)


@pytest.mark.parametrize(
    "member",
    ("name", "capability", "effect", "backend_id", "backend",
     "__init__", "__post_init__", "__getattribute__", "__getattr__"),
)
@pytest.mark.parametrize(
    "operation", ("revision", "registrations", "get", "resolve", "bind"),
)
def test_registered_identity_refuses_substituted_class_before_field_read(
    member: str, operation: str,
) -> None:
    registry, _registration, call, backend = _fixture()
    touched: list[str] = []
    with _replace_class_member(member, touched):
        with pytest.raises(ValueError, match="tool registration contract changed"):
            if operation == "revision":
                _ = registry.revision
            elif operation == "registrations":
                _ = registry.registrations
            elif operation == "get":
                registry.get("offline.fixture")
            elif operation == "resolve":
                registry.resolve(call)
            else:
                registry.bind(call)
    assert touched == []
    assert backend.calls == 0


@pytest.mark.parametrize(
    "member", ("name", "capability", "effect", "backend_id", "backend"),
)
def test_constructor_rejects_substituted_field_before_getter(
    member: str,
) -> None:
    backend = NeverExecute()
    touched: list[str] = []
    with _replace_class_member(member, touched):
        # The frozen dataclass may refuse object.__setattr__ before reaching
        # __post_init__ when its class slot becomes a setter-less property.
        # Either rejection is safe only if the hostile getter never runs.
        with pytest.raises((AttributeError, ValueError)):
            ToolRegistration(
                "offline.fixture", "offline.read", Effect.READ,
                "mock:offline", backend,
            )
    assert touched == []
    assert backend.calls == 0


def test_registration_generator_rejects_descriptor_swapped_between_yields() -> None:
    first = ToolRegistration(
        "offline.a", "offline.read", Effect.READ, "mock:a", NeverExecute(),
    )
    second = ToolRegistration(
        "offline.b", "offline.read", Effect.READ, "mock:b", NeverExecute(),
    )
    touched: list[str] = []
    advanced: list[str] = []

    def registrations():
        yield first
        advanced.append("swapping")
        with _replace_class_member("backend", touched):
            yield second
            advanced.append("must-not-advance")

    with pytest.raises(ValueError, match="tool registration contract changed"):
        ToolRegistry(registrations())
    assert advanced == ["swapping"]
    assert touched == []


def test_registration_export_replacement_is_rejected_without_fake_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry, _registration, call, backend = _fixture()
    constructed: list[str] = []

    class FakeRegistration:
        def __init__(self, *_args, **_kwargs):
            constructed.append("constructed")
            raise AssertionError("fake registration must not run")

    monkeypatch.setattr(registry_module, "ToolRegistration", FakeRegistration)
    with pytest.raises(ValueError, match="tool registration contract changed"):
        registry.bind(call)
    assert constructed == []
    assert backend.calls == 0


def test_unmodified_registration_retains_deterministic_no_dispatch_binding() -> None:
    registry, registration, call, backend = _fixture()
    bound = registry.bind(call)
    assert bound.registration is registration
    assert registry.get("offline.fixture") is registration
    assert registry.revision == bound.registry_revision
    assert bound.bound_action_id == registry.bind(call).bound_action_id
    assert backend.calls == 0
