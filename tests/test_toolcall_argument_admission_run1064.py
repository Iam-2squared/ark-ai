"""Run1064: frozen ToolCall argument carriers are admitted before callbacks.

ToolCall v1 remains compatible with general Mapping inputs at construction.
The opt-in registry/permission boundary must not reconstruct or hash a
reflected mappingproxy backed by caller code before proving its exact carrier.
All values and backends in this file are synthetic; no backend is dispatched.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from types import MappingProxyType

import pytest

import ark.agency.registry as registry_module
from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    PermissionDenied,
    ToolCall,
    ToolSpec,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class _ForeignMapping(Mapping[str, object]):
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def _reject(self, operation: str):
        self.events.append(operation)
        raise AssertionError("foreign mapping callback ran before admission")

    def __getitem__(self, key: str) -> object:
        return self._reject("__getitem__")

    def __iter__(self) -> Iterator[str]:
        return self._reject("__iter__")

    def __len__(self) -> int:
        return self._reject("__len__")

    def items(self):
        return self._reject("items")


class _NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("argument-admission fixture must not dispatch")


def _registry(backend: _NeverExecute) -> ToolRegistry:
    return ToolRegistry((
        ToolRegistration(
            "fixture.read",
            "fixture.read",
            Effect.READ,
            "disconnected.mock.v1",
            backend,
        ),
    ))


def _foreign_call(events: list[str]) -> ToolCall:
    call = ToolCall("fixture.read", "fixture.read", "synthetic:scope", {})
    # Fault-inject a reflected mutation after the frozen v1 constructor.
    object.__setattr__(
        call,
        "arguments",
        MappingProxyType(_ForeignMapping(events)),
    )
    return call


def _grants(events: list[str]):
    events.append("grant iterator entered")
    yield CapabilityGrant("fixture.read", "synthetic:scope")


def test_registry_bind_rejects_foreign_mappingproxy_before_toolcall_reconstruction():
    events: list[str] = []
    backend = _NeverExecute()
    registry = _registry(backend)
    call = _foreign_call(events)

    with pytest.raises(
        ValueError,
        match="ToolCall mapping proxy is not backed by an exact dict",
    ):
        registry.bind(call)

    assert events == []
    assert backend.calls == 0


def test_direct_permission_gate_rejects_foreign_mappingproxy_before_grants():
    events: list[str] = []
    gate = PermissionGate()
    call = _foreign_call(events)
    grant_events: list[str] = []

    with pytest.raises(
        PermissionDenied,
        match="ToolCall arguments carrier changed before authorization",
    ):
        PermissionGate.authorize(
            gate,
            ToolSpec("fixture.read", "fixture.read", Effect.READ),
            call,
            _grants(grant_events),
            now_ms=100,
        )

    assert events == []
    assert grant_events == []


def test_registered_permission_gate_rejects_foreign_mappingproxy_before_hashing():
    events: list[str] = []
    grant_events: list[str] = []
    backend = _NeverExecute()
    gate = PermissionGate()
    registry = _registry(backend)
    call = _foreign_call(events)

    with pytest.raises(
        PermissionDenied,
        match="ToolCall arguments carrier changed before authorization",
    ):
        PermissionGate.authorize_registered(
            gate,
            registry,
            call,
            _grants(grant_events),
            now_ms=100,
        )

    assert events == []
    assert grant_events == []
    assert backend.calls == 0


def test_argument_budget_rejects_equal_valued_integer_subclass_before_comparison(
    monkeypatch,
):
    events: list[str] = []

    class _HostileInt(int):
        def __eq__(self, other: object) -> bool:
            events.append("integer equality callback")
            raise AssertionError("non-exact resource limit was compared")

    monkeypatch.setattr(
        registry_module,
        "_MAX_TOOL_CALL_ARGUMENT_NODES",
        _HostileInt(registry_module._MAX_TOOL_CALL_ARGUMENT_NODES),
    )
    call = ToolCall("fixture.read", "fixture.read", "synthetic:scope", {})

    with pytest.raises(
        ValueError,
        match="ToolCall argument admission dependencies changed",
    ):
        registry_module._admit_frozen_toolcall_arguments(call.arguments)

    assert events == []


def test_registry_bind_keeps_valid_frozen_json_carriers_and_never_dispatches():
    backend = _NeverExecute()
    registry = _registry(backend)
    call = ToolCall(
        "fixture.read",
        "fixture.read",
        "synthetic:scope",
        {"nested": {"日本語": [1, True, None, 1.5]}},
    )

    bound = registry.bind(call)

    assert bound.call is call
    assert bound.registry_revision == registry.revision
    assert backend.calls == 0
