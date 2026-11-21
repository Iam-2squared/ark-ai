"""Exact ToolRegistry carrier custody rejects value-equal reflective swaps.

This is a local object-identity regression, not backend attestation, consent,
authentication, or an authorization to dispatch an external tool.
"""

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("registry inspection must not dispatch")


def _distinct_equal(value):
    swapped = ("~" + value)[1:]
    assert swapped == value and swapped is not value
    return swapped


def _example():
    backend = NeverDispatch()
    registration = ToolRegistration(
        "reader", "offline.read", Effect.READ, "fixture-backend", backend,
    )
    registry = ToolRegistry((registration,))
    call = ToolCall("reader", "offline.read", "local", {"fixture": 1})
    return registry, registration, call, backend


def _exercise(registry, call, operation):
    if operation == "revision":
        return registry.revision
    if operation == "registrations":
        return registry.registrations
    if operation == "get":
        return registry.get(call.tool)
    if operation == "resolve":
        return registry.resolve(call)
    return registry.bind(call)


@pytest.mark.parametrize("field", ("name", "capability", "backend_id"))
@pytest.mark.parametrize("operation", (
    "revision", "registrations", "get", "resolve", "bind",
))
def test_registered_text_replaced_by_new_equal_string_is_denied(field, operation):
    registry, entry, call, backend = _example()
    object.__setattr__(entry, field, _distinct_equal(getattr(entry, field)))
    with pytest.raises(ValueError, match="registered tool identity drifted"):
        _exercise(registry, call, operation)
    assert backend.calls == 0


@pytest.mark.parametrize("operation", (
    "revision", "registrations", "get", "resolve", "bind",
))
def test_revision_replaced_by_new_equal_string_is_denied(operation):
    registry, _entry, call, backend = _example()
    object.__setattr__(registry, "_revision", _distinct_equal(registry.revision))
    with pytest.raises(ValueError, match="registry revision carrier changed"):
        _exercise(registry, call, operation)
    assert backend.calls == 0


@pytest.mark.parametrize("field", ("name", "capability", "backend_id"))
def test_first_yielded_registration_equal_swap_denied_before_next_entry(field):
    backend = NeverDispatch()
    first = ToolRegistration(
        "reader", "offline.read", Effect.READ, "fixture-backend", backend,
    )
    second = ToolRegistration(
        "writer", "offline.write", Effect.WRITE, "fixture-write", backend,
    )
    reached = []

    def entries():
        yield first
        object.__setattr__(first, field, _distinct_equal(getattr(first, field)))
        yield second
        reached.append("later")

    with pytest.raises(ValueError, match="changed during registry construction"):
        ToolRegistry(entries())
    assert reached == []
    assert backend.calls == 0


def test_unchanged_exact_carriers_preserve_deterministic_binding():
    registry, entry, call, backend = _example()
    bound = registry.bind(call)
    assert bound.call is call
    assert bound.registration is entry
    assert bound.registry_revision == registry.revision
    assert registry.bind(call).bound_action_id == bound.bound_action_id
    assert backend.calls == 0
