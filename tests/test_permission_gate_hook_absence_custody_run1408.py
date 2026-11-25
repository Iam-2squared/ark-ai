"""Run1408: PermissionGate and its input carriers pin absent class hooks."""

from __future__ import annotations

import pytest

import ark.agency.policy as policy
from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    ToolCall,
    ToolSpec,
)
from ark.agency.policy import PermissionGate


_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_CARRIERS = (
    ("gate", PermissionGate, "_GATE_HOOK_ABSENT"),
    ("grant", CapabilityGrant, "_GRANT_HOOK_ABSENT"),
    ("spec", ToolSpec, "_SPEC_HOOK_ABSENT"),
    ("token", OneShotAuthorization, "_TOKEN_HOOK_ABSENT"),
)


def _write_fixture():
    call = ToolCall("writer", "fixture.write", "local:scope", {"n": 1})
    spec = ToolSpec("writer", "fixture.write", Effect.WRITE)
    grant = CapabilityGrant("fixture.write", "local:scope")
    token = OneShotAuthorization("synthetic-token", call.request_id, 1000)
    return spec, call, grant, token


def _set_class_attribute(
    carrier: type,
    name: str,
    value: object,
) -> tuple[bool, object | None]:
    namespace = vars(carrier)
    was_present = name in namespace
    original = namespace.get(name)
    type.__setattr__(carrier, name, value)
    return was_present, original


def _restore_class_attribute(
    carrier: type,
    name: str,
    original: tuple[bool, object | None],
) -> None:
    was_present, value = original
    if was_present:
        type.__setattr__(carrier, name, value)
    else:
        type.__delattr__(carrier, name)


def _authorize(
    gate: PermissionGate,
    spec: ToolSpec,
    call: ToolCall,
    grant: CapabilityGrant,
    token: OneShotAuthorization,
) -> None:
    # Bypass a deliberately substituted PermissionGate lookup hook so the
    # retained method can run its own class-epoch guard first.
    authorize = object.__getattribute__(gate, "authorize")
    authorize(spec, call, (grant,), now_ms=10, one_shot=token)


@pytest.mark.parametrize(
    ("carrier_name", "hook"),
    ((carrier_name, hook) for carrier_name, _, _ in _CARRIERS for hook in _HOOKS),
)
def test_explicit_none_is_not_confused_with_an_absent_gate_or_input_hook(
    carrier_name: str,
    hook: str,
) -> None:
    spec, call, grant, token = _write_fixture()
    gate = PermissionGate()
    carrier = next(item[1] for item in _CARRIERS if item[0] == carrier_name)
    original = _set_class_attribute(carrier, hook, None)
    try:
        with pytest.raises(PermissionDenied):
            _authorize(gate, spec, call, grant, token)
    finally:
        _restore_class_attribute(carrier, hook, original)

    assert token.token_id not in object.__getattribute__(gate, "_consumed_tokens")


@pytest.mark.parametrize(("carrier_name", "hook", "sentinel_name"), (
    ("gate", "__getattr__", "_GATE_HOOK_ABSENT"),
    ("grant", "__getattr__", "_GRANT_HOOK_ABSENT"),
    ("spec", "__getattr__", "_SPEC_HOOK_ABSENT"),
    ("token", "__getattr__", "_TOKEN_HOOK_ABSENT"),
))
def test_exact_absence_sentinel_installed_as_a_hook_is_rejected(
    carrier_name: str,
    hook: str,
    sentinel_name: str,
) -> None:
    spec, call, grant, token = _write_fixture()
    gate = PermissionGate()
    carrier = next(item[1] for item in _CARRIERS if item[0] == carrier_name)
    sentinel = getattr(policy, sentinel_name)
    original = _set_class_attribute(carrier, hook, sentinel)
    try:
        with pytest.raises(PermissionDenied):
            _authorize(gate, spec, call, grant, token)
    finally:
        _restore_class_attribute(carrier, hook, original)

    assert token.token_id not in object.__getattribute__(gate, "_consumed_tokens")


@pytest.mark.parametrize(
    "sentinel_name",
    (
        "_GATE_HOOK_ABSENT",
        "_GRANT_HOOK_ABSENT",
        "_SPEC_HOOK_ABSENT",
        "_TOKEN_HOOK_ABSENT",
    ),
)
def test_replaced_absence_sentinel_is_rejected_before_write_token_spend(
    sentinel_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, call, grant, token = _write_fixture()
    gate = PermissionGate()
    monkeypatch.setattr(policy, sentinel_name, object())

    with pytest.raises(PermissionDenied):
        _authorize(gate, spec, call, grant, token)

    assert token.token_id not in object.__getattribute__(gate, "_consumed_tokens")


@pytest.mark.parametrize(
    "vector_name",
    ("_GATE_HOOK_NAMES", "_GRANT_HOOKS", "_SPEC_HOOKS", "_TOKEN_HOOKS"),
)
def test_equal_valued_replacement_hook_vector_is_rejected(
    vector_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, call, grant, token = _write_fixture()
    gate = PermissionGate()
    original = getattr(policy, vector_name)
    replacement = tuple(list(original))
    assert replacement == original
    assert replacement is not original
    monkeypatch.setattr(policy, vector_name, replacement)

    with pytest.raises(PermissionDenied):
        _authorize(gate, spec, call, grant, token)

    assert token.token_id not in object.__getattribute__(gate, "_consumed_tokens")


def test_original_gate_and_input_hook_inventories_remain_valid() -> None:
    policy._require_original_gate_class()
    policy._require_original_spec_and_token()
    policy._require_original_grant_validator()
