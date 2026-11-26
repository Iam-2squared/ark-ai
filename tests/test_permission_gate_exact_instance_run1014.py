"""Run1009: PermissionGate rejects subclasses before instance attribute lookup.

A subclass can override __getattribute__ and redirect process-local token/lock
custody even when its inherited public methods appear unchanged to static
inspection. Both public authorization entrypoints therefore require the exact
import-original PermissionGate type before touching the instance or grants.
All grants, calls and registries below are synthetic; no backend executes.
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
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("synthetic PermissionGate test must not dispatch")


def test_both_authorization_entrypoints_reject_gate_subclasses_before_callbacks():
    attribute_reads: list[str] = []
    grant_iterations: list[str] = []

    class _ObservedGate(PermissionGate):
        def __getattribute__(self, name: str):
            attribute_reads.append(name)
            raise AssertionError("subclass attribute lookup must not run")

    with pytest.raises(PermissionDenied, match="exact PermissionGate"):
        _ObservedGate()
    gate = object.__new__(_ObservedGate)
    backend = _NeverExecute()
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.write",
            "fixture.write",
            Effect.WRITE,
            "disconnected.mock.v1",
            backend,
        ),
    ))
    call = ToolCall("fixture.write", "fixture.write", "synthetic:scope", {"n": 1})
    spec = ToolSpec("fixture.write", "fixture.write", Effect.WRITE)
    grant = CapabilityGrant("fixture.write", "synthetic:scope")
    token = OneShotAuthorization("synthetic-token", call.request_id, 500)

    def grants():
        grant_iterations.append("iterated")
        yield grant

    # Call the original unbound methods so instance method lookup cannot mask
    # the exact-type admission boundary being tested.
    with pytest.raises(PermissionDenied, match="exact PermissionGate"):
        PermissionGate.authorize(
            gate,
            spec,
            call,
            grants(),
            now_ms=100,
            one_shot=token,
        )
    with pytest.raises(PermissionDenied, match="exact PermissionGate"):
        PermissionGate.authorize_registered(
            gate,
            registry,
            call,
            grants(),
            now_ms=100,
            one_shot=token,
        )

    assert attribute_reads == []
    assert grant_iterations == []
    assert backend.calls == 0
