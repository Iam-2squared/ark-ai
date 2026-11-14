"""Disconnected plan READ diagnostics never gain authority from forged carriers.

All cases use a backend that raises if called. Neither these tests nor their
preflight results authorize live READ, WRITE, replay, consent or clock trust.
"""

import pytest

import ark.agency.disconnected_read_preflight as mod
from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NoDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("disconnected preflight must not dispatch")


def _setup():
    backend = _NoDispatch()
    registry = ToolRegistry((
        ToolRegistration("read.fixture", "fixture.read", Effect.READ, "mock", backend),
    ))
    plan = PlanGraph((
        PlanStep("a", ToolCall("read.fixture", "fixture.read", "offline", {"n": 1})),
    ))
    gate = PermissionGate()
    grants = (CapabilityGrant("fixture.read", "offline", expires_at_ms=100),)
    return plan, registry, gate, grants, backend


def _run(items):
    plan, registry, gate, grants, _backend = items
    return mod.preview_registered_read_plan(
        plan, registry, gate, grants, observed_at_ms=5,
    )


@pytest.mark.parametrize("flag", (
    "dispatch_authorized", "external_result_verified",
    "authenticated_clock_or_consent", "automatic_replay_authorized",
))
@pytest.mark.parametrize("spoof", (False, True))
def test_substituted_denial_descriptor_is_rejected_even_when_false(
    monkeypatch, flag, spoof,
):
    items = _setup()
    monkeypatch.setattr(
        mod.DisconnectedReadPreflight, flag,
        property(lambda self: spoof),
    )
    with pytest.raises(
        mod.DisconnectedReadPreflightRejected, match="authority descriptor changed",
    ):
        _run(items)
    assert items[-1].calls == 0
    assert items[2]._consumed_tokens == set()


@pytest.mark.parametrize("location", ("class", "instance"))
@pytest.mark.parametrize("style", ("forged", "delegating"))
def test_forged_registered_gate_method_never_counts_as_verified_grant(
    monkeypatch, location, style,
):
    items = _setup()
    _plan, registry, gate, _grants, backend = items
    original = PermissionGate.authorize_registered

    def alternate(self, reg, call, grants, *, now_ms, one_shot=None):
        if style == "forged":
            return reg.bind(call)
        return original(
            self, reg, call, grants, now_ms=now_ms, one_shot=one_shot,
        )

    if location == "class":
        monkeypatch.setattr(PermissionGate, "authorize_registered", alternate)
    else:
        monkeypatch.setattr(
            gate, "authorize_registered",
            lambda reg, call, grants, *, now_ms, one_shot=None: alternate(
                gate, reg, call, grants, now_ms=now_ms, one_shot=one_shot,
            ),
        )
    with pytest.raises(
        mod.DisconnectedReadPreflightRejected,
        match="registered READ gate implementation changed",
    ):
        _run(items)
    assert backend.calls == 0
    assert gate._consumed_tokens == set()
    assert registry.revision


def test_digest_callback_cannot_install_false_looking_authority(monkeypatch):
    items = _setup()
    original = mod._digest

    def changed_digest(payload):
        computed = original(payload)
        if isinstance(payload, dict):
            monkeypatch.setattr(
                mod.DisconnectedReadPreflight,
                "dispatch_authorized", property(lambda self: False),
            )
        return computed

    monkeypatch.setattr(mod, "_digest", changed_digest)
    with pytest.raises(
        mod.DisconnectedReadPreflightRejected, match="authority descriptor changed",
    ):
        _run(items)
    assert items[-1].calls == 0


def test_unmodified_preflight_still_has_no_dispatch_or_grants_to_execute():
    items = _setup()
    result = _run(items)
    assert result.ready_step_ids == ("a",)
    assert result.dispatch_authorized is False
    assert result.external_result_verified is False
    assert result.authenticated_clock_or_consent is False
    assert result.automatic_replay_authorized is False
    assert items[-1].calls == 0
    assert items[2]._consumed_tokens == set()
