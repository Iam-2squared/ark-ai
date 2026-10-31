"""Registration identity strings are bounded before hashing; vectors unchanged."""

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class DisconnectedBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("registry construction must never dispatch")


def _registration(backend, **overrides):
    fields = dict(
        name="offline.reader",
        capability="offline.read",
        effect=Effect.READ,
        backend_id="mock-reader",
        backend=backend,
    )
    fields.update(overrides)
    return ToolRegistration(**fields)


@pytest.mark.parametrize("field", ("name", "capability", "backend_id"))
def test_oversized_registration_identity_refuses_before_registry_hash(field):
    backend = DisconnectedBackend()
    with pytest.raises(ValueError, match="registry identifier budget"):
        _registration(backend, **{field: "x" * 257})
    assert backend.calls == 0


@pytest.mark.parametrize("field", ("name", "capability", "backend_id"))
def test_exact_registry_identity_budget_remains_deterministic(field):
    backend = DisconnectedBackend()
    registration = _registration(backend, **{field: "x" * 256})
    first = ToolRegistry((registration,))
    second = ToolRegistry((registration,))
    assert first.revision == second.revision
    assert first.get(registration.name) is registration
    assert backend.calls == 0


def test_existing_normal_registration_binds_without_backend_dispatch():
    backend = DisconnectedBackend()
    registration = _registration(backend)
    bound = ToolRegistry((registration,)).bind(
        ToolCall("offline.reader", "offline.read", "local"),
    )
    assert bound.registration is registration
    assert bound.call.tool == registration.name
    assert backend.calls == 0
