"""Registry effect identity and scope-limited grants in disconnected reviews.

These tests never invoke a backend and do not claim durable WRITE approval.
An inert READ preflight cannot be carried forward as permission for a
different WRITE registration sharing the same request identity.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    PermissionDenied,
    ToolCall,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecuteBackend:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("disconnected policy review invoked a backend")


def _registry(
    effect: Effect, backend: NeverExecuteBackend, backend_id: str = "rev-a",
) -> ToolRegistry:
    return ToolRegistry((
        ToolRegistration(
            "fixture.local", "fixture.read", effect, backend_id, backend,
        ),
    ))


def test_valid_read_grant_never_downgrades_registered_write() -> None:
    backend = NeverExecuteBackend()
    call = ToolCall(
        "fixture.local", "fixture.read", "scope:private", {"value": 3},
    )
    grants = (CapabilityGrant("fixture.read", "scope:private", 2_000),)
    reader = _registry(Effect.READ, backend)
    writer = _registry(Effect.WRITE, backend)
    gate = PermissionGate()

    read = gate.authorize_registered(reader, call, grants, now_ms=1_000)
    assert read.call is call
    assert read.registration.effect is Effect.READ
    assert read.registry_revision == reader.revision
    assert read.bound_action_id == reader.bind(call).bound_action_id
    assert reader.revision != writer.revision
    assert read.bound_action_id != writer.bind(call).bound_action_id

    # A valid scoped READ grant is insufficient to perform the same request
    # registered as WRITE. No one-shot authority exists in this scenario.
    with pytest.raises(PermissionDenied):
        gate.authorize_registered(writer, call, grants, now_ms=1_000)
    assert backend.calls == 0


@pytest.mark.parametrize(
    ("capability", "scope", "expires_at_ms", "now_ms"),
    (
        ("other.capability", "scope:private", 2_000, 1_000),
        ("fixture.read", "scope:another", 2_000, 1_000),
        ("fixture.read", "scope:private", 500, 1_000),
        ("fixture.read", "scope:private", 1_000, 1_000),
    ),
)
def test_read_scope_and_expiry_exactly_fenced_without_dispatch(
    capability: str, scope: str, expires_at_ms: int, now_ms: int,
) -> None:
    backend = NeverExecuteBackend()
    registry = _registry(Effect.READ, backend)
    call = ToolCall("fixture.local", "fixture.read", "scope:private", {})
    gate = PermissionGate()
    grant = CapabilityGrant(capability, scope, expires_at_ms)
    with pytest.raises(PermissionDenied):
        gate.authorize_registered(
            registry, call, (grant,), now_ms=now_ms,
        )
    assert backend.calls == 0


@pytest.mark.parametrize(
    ("new_effect", "new_backend_id"),
    (
        (Effect.WRITE, "rev-a"),
        (Effect.READ, "rev-b"),
        (Effect.WRITE, "rev-b"),
    ),
)
def test_registered_effect_or_backend_revision_changes_bound_identity(
    new_effect: Effect, new_backend_id: str,
) -> None:
    backend = NeverExecuteBackend()
    call = ToolCall(
        "fixture.local", "fixture.read", "scope:private", {"fixture": True},
    )
    old = _registry(Effect.READ, backend, "rev-a")
    changed = _registry(new_effect, backend, new_backend_id)
    old_bound = old.bind(call)
    new_bound = changed.bind(call)

    assert old.revision != changed.revision
    assert old_bound.bound_action_id != new_bound.bound_action_id
    assert old_bound.call.request_id == new_bound.call.request_id
    assert new_bound.registration.effect is new_effect
    assert backend.calls == 0
