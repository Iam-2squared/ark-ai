"""Synthetic registry backend interface pinning; no execute invocations."""

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class FixtureBackend:
    def __init__(self):
        self.execute_calls = 0

    def execute(self, call):
        self.execute_calls += 1
        return call.request_id


def _registration(backend):
    return ToolRegistration(
        "fixture.read", "fixture.read", Effect.READ, "synthetic-backend", backend
    )


def _call():
    return ToolCall("fixture.read", "fixture.read", "synthetic:scope", {})


@pytest.mark.parametrize("value", [None, 0, "not-callable"])
def test_noncallable_backend_is_rejected_during_registration(value):
    class Broken:
        execute = value

    with pytest.raises(TypeError, match="callable"):
        _registration(Broken())


def test_execution_property_not_invoked_while_validating():
    touches = []

    class Trap:
        @property
        def execute(self):
            touches.append("getter")
            raise RuntimeError("must not inspect by invoking getter")

    with pytest.raises(TypeError, match="statically callable"):
        _registration(Trap())
    assert touches == []


def test_valid_backend_is_bound_without_execution():
    backend = FixtureBackend()
    registry = ToolRegistry((_registration(backend),))
    bound = registry.bind(_call())
    assert bound.registration.backend is backend
    assert backend.execute_calls == 0


def test_reflected_backend_callable_replacement_is_rejected():
    backend = FixtureBackend()
    registry = ToolRegistry((_registration(backend),))
    backend.execute = lambda call: call.request_id
    with pytest.raises(ValueError, match="identity drifted"):
        registry.bind(_call())
    assert backend.execute_calls == 0


def test_reflected_backend_noncallable_replacement_is_rejected():
    backend = FixtureBackend()
    registry = ToolRegistry((_registration(backend),))
    backend.execute = None
    with pytest.raises(ValueError, match="backend execute interface changed"):
        registry.bind(_call())
    assert backend.execute_calls == 0


def test_class_method_replacement_is_rejected_without_dispatch():
    class Mutable:
        def execute(self, call):
            return "old"

    backend = Mutable()
    registry = ToolRegistry((_registration(backend),))
    original = Mutable.execute
    try:
        Mutable.execute = lambda self, call: "new"
        with pytest.raises(ValueError, match="identity drifted"):
            registry.bind(_call())
    finally:
        Mutable.execute = original
