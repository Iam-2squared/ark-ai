"""Registry-bound atomic intent is an inert, effect-fenced identity only.

A changed registry revision must change the bound action. READ identities and
reflective effect drift must never mint WRITE intent or invoke ToolBackend.
"""

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.disconnected_atomic_preaction_ledger import AtomicPreactionRejected
from ark.agency.disconnected_atomic_registry_bridge import (
    derive_registered_atomic_intent,
)
from ark.agency.registry import ToolRegistration, ToolRegistry

_OCCURRENCE = "occ_" + "a" * 64


class NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, _call: ToolCall):
        self.calls += 1
        raise AssertionError("synthetic registry binding must not execute")


def _registry(backend_id: str, effect: Effect):
    backend = NeverExecute()
    registration = ToolRegistration(
        "fixture.inspect", "fixture.read", effect, backend_id, backend,
    )
    registry = ToolRegistry((registration,))
    call = ToolCall(
        "fixture.inspect", "fixture.read", "synthetic", {"n": 1},
    )
    return registry, registration, call, backend


def test_write_intent_changes_when_backend_revision_changes_without_execution():
    first, _, call, backend_one = _registry("mock:identity-v1", Effect.WRITE)
    second, _, another_call, backend_two = _registry(
        "mock:identity-v2", Effect.WRITE,
    )
    original = derive_registered_atomic_intent(
        first, call, occurrence_id=_OCCURRENCE,
    )
    changed = derive_registered_atomic_intent(
        second, another_call, occurrence_id=_OCCURRENCE,
    )
    assert first.revision != second.revision
    assert call.request_id == another_call.request_id
    assert original.request_sha256 == changed.request_sha256
    assert original.bound_action_id != changed.bound_action_id
    assert original.occurrence_id == changed.occurrence_id == _OCCURRENCE
    assert backend_one.calls == backend_two.calls == 0


def test_read_registration_cannot_be_recast_as_write_intent():
    registry, _, call, backend = _registry("mock:read", Effect.READ)
    with pytest.raises(AtomicPreactionRejected):
        derive_registered_atomic_intent(
            registry, call, occurrence_id=_OCCURRENCE,
        )
    assert backend.calls == 0


def test_reflective_effect_change_is_rejected_before_backend_invocation():
    registry, entry, call, backend = _registry("mock:read", Effect.READ)
    revision = registry.revision
    object.__setattr__(entry, "effect", Effect.WRITE)
    with pytest.raises((AtomicPreactionRejected, ValueError)):
        derive_registered_atomic_intent(
            registry, call, occurrence_id=_OCCURRENCE,
        )
    assert backend.calls == 0
    assert revision.startswith("tools_")
