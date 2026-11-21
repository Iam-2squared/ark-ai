"""Registered READ preflight reports refuse executable field/constructor code.

The registered mock backend is never invoked. No WRITE grant, token spend,
external READ, trusted clock or independently retained approval is inferred.
"""

from __future__ import annotations

import pytest

from ark.agency import disconnected_registered_read_preflight as preflight
from ark.agency.contracts import CapabilityGrant, Effect, ToolCall
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NoExecution:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("backend must never execute")


def _input():
    backend = _NoExecution()
    registry = ToolRegistry((
        ToolRegistration("fixture.inspect", "fixture.inspect",
                         Effect.READ, "offline:1", backend),
    ))
    call = ToolCall("fixture.inspect", "fixture.inspect", "local:private", {"x": 1})
    gate = PermissionGate()
    grants = (CapabilityGrant("fixture.inspect", "local:private", 1000),)
    return registry, gate, call, grants, backend


def _run(values):
    registry, gate, call, grants, _backend = values
    return preflight.review_disconnected_registered_read(
        registry, gate, call, grants, now_ms=100,
    )


@pytest.mark.parametrize(
    "replacement", ("report-class", "constructor", "request-slot", "lookup"),
)
def test_fake_report_code_rejected_before_binding(
    monkeypatch, replacement,
):
    values = _input()
    calls = []

    def unsafe(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("injected preflight report code executed")

    if replacement == "report-class":
        class Counterfeit:
            def __init__(self, *args):
                unsafe(*args)

        monkeypatch.setattr(preflight, "DisconnectedReadPreflight", Counterfeit)
    elif replacement == "constructor":
        monkeypatch.setattr(
            preflight.DisconnectedReadPreflight, "__init__", unsafe,
        )
    elif replacement == "request-slot":
        monkeypatch.setattr(
            preflight.DisconnectedReadPreflight, "request_id",
            property(unsafe),
        )
    else:
        monkeypatch.setattr(
            preflight.DisconnectedReadPreflight, "__getattribute__", unsafe,
        )

    with pytest.raises(
        preflight.DisconnectedReadPreflightRejected,
        match="report authority definition changed",
    ):
        _run(values)
    assert calls == []
    assert values[-1].calls == 0
    assert values[1]._consumed_tokens == set()


def test_honest_registered_read_remains_inert_and_request_bound():
    values = _input()
    report = _run(values)
    assert report.request_id == values[2].request_id
    assert report.registry_revision == values[0].revision
    assert report.bound_action_id == values[0].bind(values[2]).bound_action_id
    assert report.backend_dispatched is False
    assert report.external_read_authorized is False
    assert report.write_authorized is False
    assert report.trusted_clock_verified is False
    assert report.durable_permission_proven is False
    assert values[-1].calls == 0
    assert values[1]._consumed_tokens == set()
