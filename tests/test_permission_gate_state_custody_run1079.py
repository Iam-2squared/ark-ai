"""PermissionGate rejects replacement or mutation of its local token ledger."""

from threading import Lock

import pytest

from ark.agency import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    PermissionGate,
    ToolCall,
    ToolRegistration,
    ToolRegistry,
    ToolSpec,
)
from ark.agency.disconnected_mock_executor import MockToolBackend


def _write_inputs():
    gate = PermissionGate()
    call = ToolCall("fixture.write", "fixture.write", "synthetic:scope")
    spec = ToolSpec("fixture.write", "fixture.write", Effect.WRITE)
    grant = CapabilityGrant("fixture.write", "synthetic:scope")
    first = OneShotAuthorization("fixture-token-1", call.request_id, 100)
    second = OneShotAuthorization("fixture-token-2", call.request_id, 100)
    return gate, call, spec, grant, first, second


def test_ordinary_assignment_cannot_replace_gate_state():
    gate, call, spec, grant, first, _ = _write_inputs()
    gate.authorize(spec, call, (grant,), now_ms=10, one_shot=first)

    with pytest.raises(AttributeError, match="state is immutable"):
        gate._consumed_tokens = set()
    with pytest.raises(AttributeError, match="state is immutable"):
        gate._token_lock = Lock()
    with pytest.raises(AttributeError, match="state is immutable"):
        gate._state_epoch = (set(), Lock(), frozenset())

    with pytest.raises(PermissionDenied, match="already consumed"):
        gate.authorize(spec, call, (grant,), now_ms=10, one_shot=first)


@pytest.mark.parametrize("field,value_factory", (
    ("_consumed_tokens", set),
    ("_token_lock", Lock),
))
def test_reflective_state_replacement_fails_before_a_second_spend(
    field, value_factory,
):
    gate, call, spec, grant, first, second = _write_inputs()
    gate.authorize(spec, call, (grant,), now_ms=10, one_shot=first)
    object.__setattr__(gate, field, value_factory())

    with pytest.raises(PermissionDenied, match="PermissionGate state changed"):
        gate.authorize(spec, call, (grant,), now_ms=10, one_shot=second)


def test_in_place_token_removal_fails_closed():
    gate, call, spec, grant, first, second = _write_inputs()
    gate.authorize(spec, call, (grant,), now_ms=10, one_shot=first)
    gate._consumed_tokens.clear()

    with pytest.raises(PermissionDenied, match="PermissionGate state changed"):
        gate.authorize(spec, call, (grant,), now_ms=10, one_shot=second)


def test_reentrant_grant_iterator_cannot_clear_consumed_token_history():
    gate, call, spec, grant, first, second = _write_inputs()
    gate.authorize(spec, call, (grant,), now_ms=10, one_shot=first)

    def grants():
        gate._consumed_tokens.clear()
        yield grant

    with pytest.raises(PermissionDenied, match="PermissionGate state changed"):
        gate.authorize(spec, call, grants(), now_ms=10, one_shot=second)


def test_registered_authorization_checks_gate_state_before_registry_binding():
    gate, call, _, grant, first, second = _write_inputs()
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.write",
            "fixture.write",
            Effect.WRITE,
            "ark.mock.fixture.v1",
            MockToolBackend(),
        ),
    ))
    gate.authorize_registered(
        registry, call, (grant,), now_ms=10, one_shot=first,
    )
    gate._consumed_tokens.clear()

    with pytest.raises(PermissionDenied, match="PermissionGate state changed"):
        gate.authorize_registered(
            registry, call, (grant,), now_ms=10, one_shot=second,
        )
