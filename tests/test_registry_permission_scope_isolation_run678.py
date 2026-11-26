"""Registered READ and WRITE cannot borrow each other's local authority.

All backends deliberately fail if called. A process-local one-shot spend is
NOT restart-safe durable consent or permission for a real external action.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    ToolCall,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class _ForbiddenBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("registry policy attempted real execution")


def _registry():
    backend = _ForbiddenBackend()
    entries = (
        ToolRegistration(
            "offline.lookup", "shared.capability", Effect.READ,
            "fixture:read-v1", backend,
        ),
        ToolRegistration(
            "offline.mutate", "shared.capability", Effect.WRITE,
            "fixture:write-v1", backend,
        ),
    )
    return ToolRegistry(entries), backend, entries


def test_same_capability_does_not_downgrade_registered_write():
    registry, backend, _entries = _registry()
    gate = PermissionGate()
    grants = (CapabilityGrant("shared.capability", "local:private", 200),)
    read_call = ToolCall(
        "offline.lookup", "shared.capability", "local:private", {"v": 1},
    )
    write_call = ToolCall(
        "offline.mutate", "shared.capability", "local:private", {"v": 1},
    )
    admitted_read = gate.authorize_registered(
        registry, read_call, grants, now_ms=100,
    )
    assert admitted_read.call is read_call
    assert admitted_read.registration.effect is Effect.READ

    with pytest.raises(PermissionDenied):
        gate.authorize_registered(
            registry, write_call, grants, now_ms=100,
        )
    assert gate._consumed_tokens == set()
    assert backend.calls == 0


def test_token_for_read_identity_cannot_spend_on_registered_write():
    registry, backend, _entries = _registry()
    gate = PermissionGate()
    grants = (CapabilityGrant("shared.capability", "local:private", 200),)
    read_call = ToolCall(
        "offline.lookup", "shared.capability", "local:private", {"v": 1},
    )
    write_call = ToolCall(
        "offline.mutate", "shared.capability", "local:private", {"v": 1},
    )
    wrong_token = OneShotAuthorization(
        "fixture-token", read_call.request_id, 200,
    )
    with pytest.raises(PermissionDenied):
        gate.authorize_registered(
            registry, write_call, grants, now_ms=100,
            one_shot=wrong_token,
        )
    assert gate._consumed_tokens == set()
    assert backend.calls == 0


def test_registry_revision_is_canonical_across_registration_order():
    registry, backend, entries = _registry()
    reordered = ToolRegistry(tuple(reversed(entries)))
    call = ToolCall(
        "offline.lookup", "shared.capability", "local:private", {"v": 1},
    )
    first = registry.bind(call)
    second = reordered.bind(call)
    assert first.registry_revision == second.registry_revision
    assert first.bound_action_id == second.bound_action_id
    assert first.registration is entries[0]
    assert second.registration is entries[0]
    assert backend.calls == 0


def test_process_local_write_spend_is_once_only_for_exact_action():
    registry, backend, _entries = _registry()
    gate = PermissionGate()
    call = ToolCall(
        "offline.mutate", "shared.capability", "local:private", {"v": 1},
    )
    token = OneShotAuthorization("fixture-once-token", call.request_id, 200)
    grants = (CapabilityGrant("shared.capability", "local:private", 200),)
    bound = gate.authorize_registered(
        registry, call, grants, now_ms=100, one_shot=token,
    )
    assert bound.registration.effect is Effect.WRITE
    assert gate._consumed_tokens == {"fixture-once-token"}
    with pytest.raises(PermissionDenied):
        gate.authorize_registered(
            registry, call, grants, now_ms=100, one_shot=token,
        )
    assert gate._consumed_tokens == {"fixture-once-token"}
    assert backend.calls == 0
