"""Registry registration must not perform dynamic protocol attribute lookups.

Synthetic backend methods are never dispatched by these tests.
"""

import pytest

import ark.agency.registry as registry_module
from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


@pytest.mark.parametrize("behavior", ("raise", "record", "return"))
def test_registration_and_binding_do_not_lookup_execute_dynamically(behavior):
    touches = []

    class Backend:
        def __getattribute__(self, name):
            if name == "execute":
                touches.append(name)
                if behavior == "raise":
                    raise AssertionError("dynamic execute lookup attempted")
                if behavior == "return":
                    return lambda _call: "forged"
            return object.__getattribute__(self, name)

        def execute(self, _call):
            raise AssertionError("backend dispatch is forbidden")

    backend = Backend()
    registration = ToolRegistration(
        "fixture.read", "fixture.read", Effect.READ, "backend:fixture", backend,
    )
    registry = ToolRegistry((registration,))
    call = ToolCall("fixture.read", "fixture.read", "fixture:scope")
    bound = registry.bind(call)
    assert bound.call is call
    assert bound.registration is registration
    assert registry.resolve(call) is registration
    assert registry.get("fixture.read") is registration
    assert registry.revision == bound.registry_revision
    assert touches == []


def test_registration_uses_static_interface_not_protocol_instancecheck(monkeypatch):
    class UnsafeMetaclass(type):
        def __instancecheck__(cls, _instance):
            raise AssertionError("runtime protocol inspected backend")

    class FakeProtocol(metaclass=UnsafeMetaclass):
        pass

    class Backend:
        def execute(self, _call):
            raise AssertionError("backend dispatch is forbidden")

    monkeypatch.setattr(registry_module, "ToolBackend", FakeProtocol)
    backend = Backend()
    registered = ToolRegistration(
        "fixture.read", "fixture.read", Effect.READ, "backend:fixture", backend,
    )
    assert ToolRegistry((registered,)).get("fixture.read") is registered


def test_static_backend_descriptor_still_rejects_noncalls_without_getter():
    touched = []

    class Hostile:
        @property
        def execute(self):
            touched.append("getter")
            raise AssertionError("hostile property should not execute")

    with pytest.raises(TypeError, match="statically callable"):
        ToolRegistration(
            "fixture.read", "fixture.read", Effect.READ,
            "backend:fixture", Hostile(),
        )
    assert touched == []


def test_reflected_execute_rebinding_is_still_detected_without_dynamic_lookup():
    touched = []

    class Backend:
        def __getattribute__(self, name):
            if name == "execute":
                touched.append("getter")
                raise AssertionError("dynamic execute lookup attempted")
            return object.__getattribute__(self, name)

        def execute(self, _call):
            raise AssertionError("backend dispatch is forbidden")

    backend = Backend()
    registered = ToolRegistration(
        "fixture.read", "fixture.read", Effect.READ, "backend:fixture", backend,
    )
    registry = ToolRegistry((registered,))
    object.__setattr__(backend, "execute", lambda _call: "different")
    with pytest.raises(ValueError, match="identity drifted"):
        _ = registry.revision
    assert touched == []
