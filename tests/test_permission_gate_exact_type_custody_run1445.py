"""Run1445: exact PermissionGate type, state and registry-bound custody."""

from __future__ import annotations

import pytest

import ark.agency.policy as policy
from ark.agency import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    ToolCall,
    ToolRegistration,
    ToolRegistry,
)


@pytest.mark.parametrize("hook", ("__new__", "__getattribute__", "__getattr__"))
def test_permission_gate_lookup_hook_replacement_is_denied_before_execution(
    monkeypatch: pytest.MonkeyPatch,
    hook: str,
) -> None:
    gate = policy.PermissionGate()
    invoked: list[str] = []

    def forbidden(*_args: object, **_kwargs: object) -> object:
        invoked.append(hook)
        raise AssertionError("substituted PermissionGate lookup hook executed")

    with monkeypatch.context() as patch:
        patch.setattr(policy.PermissionGate, hook, forbidden, raising=False)
        with pytest.raises(
            policy.PermissionDenied,
            match="PermissionGate implementation identity changed",
        ):
            policy.PermissionGate.authorize(gate, object(), object(), (), now_ms=0)

    assert invoked == []
    policy._assert_gate_instance_epoch(gate)


@pytest.mark.parametrize("hook", ("__new__", "__getattribute__", "__getattr__"))
def test_permission_gate_lookup_hook_explicit_none_is_not_absence(
    monkeypatch: pytest.MonkeyPatch,
    hook: str,
) -> None:
    gate = policy.PermissionGate()
    with monkeypatch.context() as patch:
        patch.setattr(policy.PermissionGate, hook, None, raising=False)
        with pytest.raises(
            policy.PermissionDenied,
            match="PermissionGate implementation identity changed",
        ):
            policy.PermissionGate.authorize_registered(
                gate, object(), object(), (), now_ms=0,
            )

    policy._assert_gate_instance_epoch(gate)


def test_permission_gate_hook_inventory_alias_is_pinned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    replacement = tuple(list(policy._GATE_HOOK_NAMES))
    assert replacement == policy._GATE_HOOK_NAMES
    assert replacement is not policy._GATE_HOOK_NAMES

    with monkeypatch.context() as patch:
        patch.setattr(policy, "_GATE_HOOK_NAMES", replacement)
        with pytest.raises(
            policy.PermissionDenied,
            match="PermissionGate implementation identity changed",
        ):
            policy._require_original_gate_class()


def test_permission_gate_hook_absence_sentinel_is_pinned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(policy, "_GATE_HOOK_ABSENT", object())
        with pytest.raises(
            policy.PermissionDenied,
            match="PermissionGate implementation identity changed",
        ):
            policy._require_original_gate_class()


def test_permission_gate_hook_cannot_be_replaced_by_its_absence_sentinel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate = policy.PermissionGate()
    with monkeypatch.context() as patch:
        patch.setattr(
            policy.PermissionGate,
            "__getattribute__",
            policy._GATE_HOOK_ABSENT,
            raising=False,
        )
        with pytest.raises(
            policy.PermissionDenied,
            match="PermissionGate implementation identity changed",
        ):
            policy.PermissionGate.authorize(gate, object(), object(), (), now_ms=0)


def test_permission_gate_subclass_is_rejected_before_hostile_lookup() -> None:
    invoked: list[str] = []

    class HostileGate(policy.PermissionGate):
        def __getattribute__(self, name: str) -> object:
            invoked.append(name)
            raise AssertionError("subclass lookup hook must not run")

    with pytest.raises(
        policy.PermissionDenied,
        match="exact PermissionGate instance",
    ):
        HostileGate()

    assert invoked == []


@pytest.mark.parametrize(
    ("slot", "replacement"),
    (
        ("_consumed_tokens", frozenset(("forged-token",))),
        ("_token_lock", object()),
    ),
)
def test_reflective_gate_state_replacement_is_denied_before_grant_iteration(
    slot: str,
    replacement: object,
) -> None:
    gate = policy.PermissionGate()
    object.__setattr__(gate, slot, replacement)
    invoked: list[str] = []

    def grants():
        invoked.append("iterated")
        yield CapabilityGrant("fixture.read", "fixture:scope")

    with pytest.raises(
        policy.PermissionDenied,
        match="PermissionGate token or lock custody changed",
    ):
        gate.authorize(
            policy.ToolSpec("fixture.read", "fixture.read", Effect.READ),
            ToolCall("fixture.read", "fixture.read", "fixture:scope"),
            grants(),
            now_ms=10,
        )

    assert invoked == []


def test_registered_write_uses_registry_effect_and_never_dispatches() -> None:
    class InertBackend:
        def __init__(self) -> None:
            self.calls = 0

        def execute(self, _call: ToolCall) -> None:
            self.calls += 1

    backend = InertBackend()
    registration = ToolRegistration(
        "fixture.write",
        "fixture.write",
        Effect.WRITE,
        "fixture-backend",
        backend,
    )
    registry = ToolRegistry((registration,))
    gate = policy.PermissionGate()
    call = ToolCall(
        "fixture.write",
        "fixture.write",
        "fixture:scope",
        {"path": "synthetic-private-fixture"},
    )
    grants = (CapabilityGrant("fixture.write", "fixture:scope"),)

    # The registered path derives WRITE from the immutable registration; it
    # cannot be downgraded by a caller-supplied READ ToolSpec.
    with pytest.raises(policy.PermissionDenied, match="one-shot"):
        gate.authorize_registered(registry, call, grants, now_ms=10)

    token = OneShotAuthorization("fixture-token", call.request_id, 100)
    bound = gate.authorize_registered(
        registry,
        call,
        grants,
        now_ms=10,
        one_shot=token,
    )
    assert bound.registration is registration
    assert bound.registration.effect is Effect.WRITE
    assert bound.call is call
    assert bound.registry_revision == registry.revision
    assert bound.bound_action_id.startswith("bound_")
    assert backend.calls == 0

    with pytest.raises(policy.PermissionDenied, match="already consumed"):
        gate.authorize_registered(
            registry,
            call,
            grants,
            now_ms=10,
            one_shot=token,
        )
    assert backend.calls == 0
