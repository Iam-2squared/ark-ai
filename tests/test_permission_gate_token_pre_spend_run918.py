"""PermissionGate's WRITE token is process-local, not a durable grant.

These tests exercise only disconnected policy decisions; no ToolBackend,
real consent, trusted clock, action audit, external effect or replay occurs.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    ToolCall,
    ToolSpec,
)
from ark.agency.policy import PermissionGate


def _inputs():
    spec = ToolSpec("fixture", "fixture.write", Effect.WRITE)
    call = ToolCall("fixture", "fixture.write", "sandbox", {"sample": True})
    grant = CapabilityGrant("fixture.write", "sandbox")
    token = OneShotAuthorization("synthetic-token", call.request_id, 1000)
    return spec, call, grant, token


@pytest.mark.parametrize("failure", ("generator", "scope", "expired", "wrong-type"))
def test_bad_grants_cannot_consume_token_before_a_later_explicit_admission(failure):
    gate = PermissionGate()
    spec, call, grant, token = _inputs()

    def interrupted():
        yield grant
        raise RuntimeError("synthetic grant iterator interruption")

    if failure == "generator":
        invalid = interrupted()
        expected_error = RuntimeError
    elif failure == "scope":
        invalid = (CapabilityGrant("fixture.write", "other"),)
        expected_error = PermissionDenied
    elif failure == "expired":
        invalid = (CapabilityGrant("fixture.write", "sandbox", 100),)
        expected_error = PermissionDenied
    else:
        invalid = ({"capability": "fixture.write", "scope": "sandbox"},)
        expected_error = PermissionDenied

    with pytest.raises(expected_error):
        gate.authorize(spec, call, invalid, now_ms=100, one_shot=token)
    assert token.token_id not in gate._consumed_tokens

    # Synthetic caller explicitly tries a new policy decision. The prior
    # failed grant enumeration cannot silently pre-spend this local token.
    gate.authorize(spec, call, (grant,), now_ms=100, one_shot=token)
    assert token.token_id in gate._consumed_tokens
    with pytest.raises(PermissionDenied):
        gate.authorize(spec, call, (grant,), now_ms=100, one_shot=token)


def test_new_gate_does_not_inherit_token_spend_from_previous_gate():
    spec, call, grant, token = _inputs()
    first = PermissionGate()
    first.authorize(spec, call, (grant,), now_ms=100, one_shot=token)
    second = PermissionGate()
    # Document the intentional fail-to-prove boundary, not a safety success:
    # a new process-local gate has no durable receipt. Real WRITE execution
    # MUST require a separate persisted occurrence + audit-before-action fence.
    assert token.token_id not in second._consumed_tokens
    second.authorize(spec, call, (grant,), now_ms=100, one_shot=token)
    assert token.token_id in second._consumed_tokens
