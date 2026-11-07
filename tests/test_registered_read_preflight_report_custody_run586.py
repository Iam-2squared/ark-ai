"""A disconnected registered READ report never becomes authority by monkeypatch."""

from __future__ import annotations

import pytest

import ark.agency.disconnected_registered_read_preflight as read
from ark.agency.contracts import CapabilityGrant, Effect, ToolCall
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("mock review must not dispatch")


def _input():
    backend = _NeverDispatch()
    registry = ToolRegistry((
        ToolRegistration("local.inspect", "local.inspect",
                         Effect.READ, "mock:1", backend),
    ))
    call = ToolCall("local.inspect", "local.inspect", "scope:private", {"n": 1})
    grant = CapabilityGrant("local.inspect", "scope:private", 1000)
    return registry, PermissionGate(), call, (grant,), backend


def _review(items):
    registry, gate, call, grants, _backend = items
    return read.review_disconnected_registered_read(
        registry, gate, call, grants, now_ms=100,
    )


@pytest.mark.parametrize("name", read._REPORT_DENIALS)
def test_false_looking_denial_replacement_rejected_before_binding(
    monkeypatch, name,
):
    items = _input()
    monkeypatch.setattr(read.DisconnectedReadPreflight, name, property(lambda _: False))

    def no_bind(*_args, **_kwargs):
        pytest.fail("registry binding reached after report authority definition changed")

    monkeypatch.setattr(ToolRegistry, "bind", no_bind)
    with pytest.raises(read.DisconnectedReadPreflightRejected, match="definition changed"):
        _review(items)
    assert items[-1].calls == 0


@pytest.mark.parametrize("name", read._REPORT_DENIALS)
def test_true_authority_replacement_rejected_at_ingress(monkeypatch, name):
    items = _input()
    monkeypatch.setattr(read.DisconnectedReadPreflight, name, property(lambda _: True))
    with pytest.raises(read.DisconnectedReadPreflightRejected, match="definition changed"):
        _review(items)
    assert items[-1].calls == 0


def test_false_denial_getter_cannot_retarget_request_identity(monkeypatch):
    items = _input()
    original = read.DisconnectedReadPreflight.__getattribute__
    calls = []

    def substitute(self, name):
        calls.append(name)
        if name == "backend_dispatched":
            request = original(self, "request_id")
            replacement = (" " + request)[1:]
            assert replacement == request and replacement is not request
            object.__setattr__(self, "request_id", replacement)
            return False
        return original(self, name)

    monkeypatch.setattr(read.DisconnectedReadPreflight, "__getattribute__", substitute)
    with pytest.raises(
        read.DisconnectedReadPreflightRejected,
        match="definition changed",
    ):
        _review(items)
    assert calls == []
    assert items[-1].calls == 0


def test_false_denial_getter_cannot_replace_later_denial(monkeypatch):
    items = _input()
    original = read.DisconnectedReadPreflight.__getattribute__

    def substitute(self, name):
        if name == "backend_dispatched":
            monkeypatch.setattr(
                read.DisconnectedReadPreflight,
                "external_read_authorized", property(lambda _: False),
            )
            return False
        return original(self, name)

    monkeypatch.setattr(read.DisconnectedReadPreflight, "__getattribute__", substitute)
    with pytest.raises(read.DisconnectedReadPreflightRejected, match="definition changed"):
        _review(items)
    assert items[-1].calls == 0


def test_original_read_preflight_remains_inert_and_tokenless():
    items = _input()
    report = _review(items)
    assert report.backend_dispatched is False
    assert report.external_read_authorized is False
    assert report.write_authorized is False
    assert report.trusted_clock_verified is False
    assert report.durable_permission_proven is False
    assert items[-1].calls == 0
    assert not items[1]._consumed_tokens
