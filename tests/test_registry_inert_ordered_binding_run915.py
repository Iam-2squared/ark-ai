"""Registry-bound mock identities stay deterministic and never execute.

These tests exercise identity construction only; no real ToolBackend or
external action, permission grant or durable execution is involved.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class DenyOnlyBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("registry construction must never dispatch")


def _registrations():
    first = DenyOnlyBackend()
    second = DenyOnlyBackend()
    return (
        ToolRegistration(
            "fixture.alpha", "local.read", Effect.READ, "mock-alpha", first,
        ),
        ToolRegistration(
            "fixture.beta", "local.read", Effect.READ, "mock-beta", second,
        ),
    )


def test_registration_order_does_not_change_bound_fixture_identity():
    alpha, beta = _registrations()
    one = ToolRegistry((alpha, beta))
    two = ToolRegistry((beta, alpha))
    call = ToolCall("fixture.alpha", "local.read", "synthetic", {"item": 1})

    bound_one = one.bind(call)
    bound_two = two.bind(call)
    assert one.revision == two.revision
    assert bound_one.registry_revision == bound_two.registry_revision
    assert bound_one.bound_action_id == bound_two.bound_action_id
    assert bound_one.registration is alpha
    assert bound_two.registration is alpha
    assert bound_one.call is bound_two.call is call
    assert alpha.backend.calls == 0
    assert beta.backend.calls == 0


@pytest.mark.parametrize("field", ("capability", "backend_id"))
def test_reflected_registration_change_denied_before_binding(field):
    alpha, beta = _registrations()
    registry = ToolRegistry((alpha, beta))
    object.__setattr__(alpha, field, "altered.identity")
    call = ToolCall("fixture.alpha", "local.read", "synthetic", {"item": 1})
    with pytest.raises(ValueError):
        registry.bind(call)
    assert alpha.backend.calls == 0
    assert beta.backend.calls == 0


def test_capability_mismatch_never_invokes_backend():
    alpha, beta = _registrations()
    registry = ToolRegistry((alpha, beta))
    with pytest.raises(ValueError, match="capability"):
        registry.bind(
            ToolCall("fixture.alpha", "not-the-granted-capability", "synthetic")
        )
    assert alpha.backend.calls == 0
    assert beta.backend.calls == 0
