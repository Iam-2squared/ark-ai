"""A mutable grant budget cannot enlarge local WRITE token admission.

Synthetic in-process fixtures only. A successful policy check is NOT durable
consent, external execution authorization or a backend dispatch.
"""

from __future__ import annotations

import pytest

from ark.agency import policy
from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    ToolCall,
    ToolSpec,
)
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("permission diagnostics must not dispatch a backend")


def _case():
    backend = NeverExecute()
    call = ToolCall("fixture.tool", "fixture.write", "scope:private")
    spec = ToolSpec("fixture.tool", "fixture.write", Effect.WRITE)
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.tool", "fixture.write", Effect.WRITE, "local", backend,
        ),
    ))
    grant = CapabilityGrant("fixture.write", "scope:private")
    token = OneShotAuthorization("synthetic-token", call.request_id, 100)
    return backend, call, spec, registry, grant, token


def _authorize(gate, *, registered, call, spec, registry, grants, token):
    if registered:
        return gate.authorize_registered(
            registry, call, grants, now_ms=10, one_shot=token,
        )
    return gate.authorize(spec, call, grants, now_ms=10, one_shot=token)


@pytest.mark.parametrize("registered", (False, True))
@pytest.mark.parametrize("bad_budget", (True, -1, 1024.0, 2**63))
def test_rebound_grant_budget_refused_before_iterator_and_token_spend(
    monkeypatch, registered, bad_budget,
):
    backend, call, spec, registry, grant, token = _case()
    gate = policy.PermissionGate()
    touched = []

    class TrapGrants:
        def __iter__(self):
            touched.append(True)
            yield grant

    with monkeypatch.context() as patch:
        patch.setattr(policy, "_MAX_GRANTS", bad_budget)
        with pytest.raises(PermissionDenied, match="grant budget contract changed"):
            _authorize(
                gate, registered=registered, call=call, spec=spec,
                registry=registry, grants=TrapGrants(), token=token,
            )
    assert touched == []
    assert backend.calls == 0
    assert gate._consumed_tokens == set()
    _authorize(
        gate, registered=registered, call=call, spec=spec,
        registry=registry, grants=[grant], token=token,
    )
    assert gate._consumed_tokens == {"synthetic-token"}
    assert backend.calls == 0


@pytest.mark.parametrize("registered", (False, True))
def test_grant_budget_drift_mid_iterator_refused_without_spend(
    monkeypatch, registered,
):
    backend, call, spec, registry, grant, token = _case()
    gate = policy.PermissionGate()
    touched = []

    def hostile_grants():
        touched.append("first")
        yield grant
        monkeypatch.setattr(policy, "_MAX_GRANTS", 10**9)
        touched.append("second")
        yield grant

    with monkeypatch.context():
        with pytest.raises(PermissionDenied, match="grant budget contract changed"):
            _authorize(
                gate, registered=registered, call=call, spec=spec,
                registry=registry, grants=hostile_grants(), token=token,
            )
    assert touched == ["first", "second"]
    assert backend.calls == 0
    assert gate._consumed_tokens == set()
