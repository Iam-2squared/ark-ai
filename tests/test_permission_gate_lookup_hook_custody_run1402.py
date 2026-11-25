"""Run1402: PermissionGate lookup hooks are part of exact class custody."""

from __future__ import annotations

import pytest

import ark.agency.policy as policy


@pytest.mark.parametrize("hook", ("__getattribute__", "__getattr__"))
def test_lookup_hook_replacement_is_denied_before_instance_state_reads(
    monkeypatch: pytest.MonkeyPatch,
    hook: str,
) -> None:
    gate = policy.PermissionGate()
    invoked: list[str] = []

    def forbidden(_self: object, _name: str) -> object:
        invoked.append(hook)
        raise AssertionError("substituted PermissionGate lookup hook executed")

    with monkeypatch.context() as patch:
        patch.setattr(policy.PermissionGate, hook, forbidden, raising=False)
        with pytest.raises(
            policy.PermissionDenied,
            match="PermissionGate implementation identity changed",
        ):
            # Static class invocation avoids entering the hostile instance
            # lookup hook before the method's first class-custody check.
            policy.PermissionGate.authorize(
                gate, object(), object(), (), now_ms=0,
            )

    assert invoked == []
    policy._assert_gate_instance_epoch(gate)


@pytest.mark.parametrize("hook", ("__getattribute__", "__getattr__"))
def test_lookup_hook_set_to_none_is_not_confused_with_inherited_absence(
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


def test_lookup_hook_inventory_alias_is_pinned_even_when_values_are_equal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    replacement = tuple(list(policy._GATE_LOOKUP_HOOK_NAMES))
    assert replacement == policy._GATE_LOOKUP_HOOK_NAMES
    assert replacement is not policy._GATE_LOOKUP_HOOK_NAMES

    with monkeypatch.context() as patch:
        patch.setattr(policy, "_GATE_LOOKUP_HOOK_NAMES", replacement)
        with pytest.raises(
            policy.PermissionDenied,
            match="PermissionGate implementation identity changed",
        ):
            policy._require_original_gate_class()


def test_lookup_hook_absence_sentinel_is_pinned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(policy, "_GATE_LOOKUP_HOOK_ABSENT", object())
        with pytest.raises(
            policy.PermissionDenied,
            match="PermissionGate implementation identity changed",
        ):
            policy._require_original_gate_class()


def test_lookup_hook_cannot_be_set_to_the_absence_sentinel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate = policy.PermissionGate()
    with monkeypatch.context() as patch:
        patch.setattr(
            policy.PermissionGate,
            "__getattribute__",
            policy._GATE_LOOKUP_HOOK_ABSENT,
            raising=False,
        )
        with pytest.raises(
            policy.PermissionDenied,
            match="PermissionGate implementation identity changed",
        ):
            policy.PermissionGate.authorize(
                gate, object(), object(), (), now_ms=0,
            )


def test_exact_permission_gate_still_passes_original_class_and_instance_guards() -> None:
    gate = policy.PermissionGate()

    policy._require_original_gate_class()
    policy._assert_gate_instance_epoch(gate)


def test_subclass_is_rejected_before_its_lookup_hook_runs() -> None:
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
