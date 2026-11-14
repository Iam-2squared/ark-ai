"""Original detached READ plan constructor is never an executable callback.

Only local mock registration is used; no backend dispatch, spending or grant
consumption is permitted by these tests or the review itself.
"""

from __future__ import annotations

import pytest

import ark.agency.disconnected_read_preflight as read
from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("detached READ review dispatched a backend")


def _case():
    backend = NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("reader", "fixture.read", Effect.READ, "mock", backend),
    ))
    plan = PlanGraph((
        PlanStep("a", ToolCall("reader", "fixture.read", "sandbox")),
    ))
    gate = PermissionGate()
    claims = (CapabilityGrant("fixture.read", "sandbox", 100),)
    return plan, registry, gate, claims, backend


def _review(case):
    plan, registry, gate, claims, _ = case
    return read.preview_registered_read_plan(
        plan, registry, gate, claims, observed_at_ms=50,
    )


def test_preinstalled_constructor_rejected_before_registry_binding(monkeypatch):
    case = _case()
    invoked = []

    def hostile(self, *args, **kwargs):
        invoked.append(True)
        raise AssertionError("substituted result initializer executed")

    with monkeypatch.context() as patch:
        patch.setattr(read.DisconnectedReadPreflight, "__init__", hostile)
        patch.setattr(
            ToolRegistry, "bind",
            lambda *_args: pytest.fail("registry touched before constructor veto"),
        )
        with pytest.raises(
            read.DisconnectedReadPreflightRejected, match="authority descriptor changed",
        ):
            _review(case)
    assert invoked == []
    assert case[-1].calls == 0
    assert not case[2]._consumed_tokens


@pytest.mark.parametrize("digest_call", (1, 2))
def test_constructor_replaced_during_digest_is_rejected_before_execution(
    monkeypatch, digest_call,
):
    case = _case()
    original_digest = read._digest
    calls = []
    executed = []

    def hostile(self, *args, **kwargs):
        executed.append(True)
        raise AssertionError("replacement constructor executed")

    def digest(payload):
        calls.append(True)
        if len(calls) == digest_call:
            monkeypatch.setattr(read.DisconnectedReadPreflight, "__init__", hostile)
        return original_digest(payload)

    with monkeypatch.context() as patch:
        patch.setattr(read, "_digest", digest)
        with pytest.raises(
            read.DisconnectedReadPreflightRejected, match="authority descriptor changed",
        ):
            _review(case)
    assert len(calls) >= digest_call
    assert executed == []
    assert case[-1].calls == 0
    assert not case[2]._consumed_tokens


def test_original_constructor_returns_content_free_non_authorizing_result():
    case = _case()
    result = _review(case)
    assert type(result) is read.DisconnectedReadPreflight
    assert result.ready_step_ids == ("a",)
    assert result.dispatch_authorized is False
    assert result.external_result_verified is False
    assert result.authenticated_clock_or_consent is False
    assert result.automatic_replay_authorized is False
    assert case[-1].calls == 0
    assert not case[2]._consumed_tokens
