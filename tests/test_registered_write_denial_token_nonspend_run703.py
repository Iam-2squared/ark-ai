"""Registered WRITE admission refuses invalid inputs without spending a token.

This exercises only the process-local gate and immutable registry. No backend
execution, durable consent, external side effect or real approval is claimed.
"""

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


class NoExecution:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("registered permission checks must not dispatch")


def _fixture():
    backend = NoExecution()
    call = ToolCall("fixture.write", "fixture.write", "local:fixture", {"count": 1})
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.write", "fixture.write", Effect.WRITE,
            "mock:disconnected", backend,
        ),
    ))
    grant = CapabilityGrant("fixture.write", "local:fixture", 500)
    token = OneShotAuthorization("fixture-once", call.request_id, 500)
    return backend, registry, call, grant, token


def _admit(gate, registry, call, grants, token, now=100):
    return gate.authorize_registered(
        registry, call, grants, now_ms=now, one_shot=token,
    )


@pytest.mark.parametrize("bad_now", (True, False, 100.0, -1, 2**63, "100"))
def test_invalid_clock_never_spends_registered_write_token(bad_now):
    backend, registry, call, grant, token = _fixture()
    gate = PermissionGate()
    with pytest.raises(ValueError, match="non-negative integer"):
        _admit(gate, registry, call, (grant,), token, now=bad_now)

    # A good retry is possible only because the previous invalid clock
    # was denied before the process-local token was consumed.
    bound = _admit(gate, registry, call, (grant,), token)
    assert bound.registration.effect is Effect.WRITE
    with pytest.raises(PermissionDenied, match="already consumed"):
        _admit(gate, registry, call, (grant,), token)
    assert backend.calls == 0


@pytest.mark.parametrize(
    "bad_grant",
    (
        CapabilityGrant("fixture.write", "local:other", 500),
        CapabilityGrant("fixture.write", "local:fixture", 100),
        CapabilityGrant("fixture.other", "local:fixture", 500),
    ),
)
def test_expired_or_wrong_scope_grant_does_not_spend_token(bad_grant):
    backend, registry, call, grant, token = _fixture()
    gate = PermissionGate()
    with pytest.raises(PermissionDenied, match="no active exact-scope"):
        _admit(gate, registry, call, (bad_grant,), token)

    bound = _admit(gate, registry, call, (grant,), token)
    assert bound.registration is registry.get("fixture.write")
    assert backend.calls == 0


@pytest.mark.parametrize("reason", ("wrong-request", "expired-token"))
def test_invalid_one_shot_does_not_poison_later_valid_registered_write(reason):
    backend, registry, call, grant, valid = _fixture()
    gate = PermissionGate()
    bad = OneShotAuthorization(
        valid.token_id,
        ("act_" + "0" * 64) if reason == "wrong-request" else call.request_id,
        500 if reason == "wrong-request" else 100,
    )
    with pytest.raises(PermissionDenied):
        _admit(gate, registry, call, (grant,), bad)

    bound = _admit(gate, registry, call, (grant,), valid)
    assert bound.bound_action_id.startswith("bound_")
    assert bound.registration.effect is Effect.WRITE
    assert backend.calls == 0
