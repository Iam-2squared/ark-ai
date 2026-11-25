"""Run1350: reject reflected non-exact one-shot fields before authorization callbacks."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

import ark.agency.durable_occurrence_review as occurrence
import ark.agency.policy as policy
from ark.agency import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    PermissionGate,
    ToolCall,
    ToolSpec,
)
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)
from ark.agency.registry import BoundAction, ToolRegistration, ToolRegistry


class HostileString(str):
    def __hash__(self) -> int:
        raise AssertionError("hostile token string hash must not run")

    def __eq__(self, other: object) -> bool:
        raise AssertionError("hostile token string equality must not run")

    def strip(self, chars: str | None = None) -> str:
        raise AssertionError("hostile token string method must not run")


class HostileInt(int):
    def __lt__(self, other: object) -> bool:
        raise AssertionError("hostile token integer comparison must not run")

    def __le__(self, other: object) -> bool:
        raise AssertionError("hostile token integer comparison must not run")


class NeverExecutedBackend:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("authorization fixtures must never dispatch a backend")


def _call() -> ToolCall:
    return ToolCall("fixture.write", "fixture.write", "scope:one", {"n": 1})


def _token(call: ToolCall) -> OneShotAuthorization:
    return OneShotAuthorization("synthetic-token", call.request_id, 500)


def _mutate_token(token: OneShotAuthorization, call: ToolCall, variant: str) -> None:
    if variant == "token_id_subclass":
        object.__setattr__(token, "token_id", HostileString("synthetic-token"))
    elif variant == "token_id_blank":
        object.__setattr__(token, "token_id", " ")
    elif variant == "request_id_subclass":
        object.__setattr__(token, "request_id", HostileString(call.request_id))
    elif variant == "request_id_malformed":
        object.__setattr__(token, "request_id", "act_" + "g" * 64)
    elif variant == "expiry_bool":
        object.__setattr__(token, "expires_at_ms", True)
    elif variant == "expiry_subclass":
        object.__setattr__(token, "expires_at_ms", HostileInt(500))
    elif variant == "expiry_negative":
        object.__setattr__(token, "expires_at_ms", -1)
    elif variant == "expiry_overflow":
        object.__setattr__(token, "expires_at_ms", 1 << 63)
    else:
        raise AssertionError(f"unknown token mutation fixture: {variant}")


def _grants(events: list[str]) -> Iterator[CapabilityGrant]:
    events.append("iterated")
    yield CapabilityGrant("fixture.write", "scope:one", 500)


def _registry() -> ToolRegistry:
    return ToolRegistry((
        ToolRegistration(
            "fixture.write",
            "fixture.write",
            Effect.WRITE,
            "ark.synthetic.fixture.v1",
            NeverExecutedBackend(),
        ),
    ))


_TOKEN_VARIANTS = (
    "token_id_subclass",
    "token_id_blank",
    "request_id_subclass",
    "request_id_malformed",
    "expiry_bool",
    "expiry_subclass",
    "expiry_negative",
    "expiry_overflow",
)


@pytest.mark.parametrize("variant", _TOKEN_VARIANTS)
def test_direct_permission_gate_rejects_invalid_token_fields_before_grant_iteration(
    variant: str,
) -> None:
    call = _call()
    token = _token(call)
    _mutate_token(token, call, variant)
    gate = PermissionGate()
    events: list[str] = []

    with pytest.raises(PermissionDenied, match="one-shot authorization fields"):
        gate.authorize(
            ToolSpec("fixture.write", "fixture.write", Effect.WRITE),
            call,
            _grants(events),
            now_ms=100,
            one_shot=token,
        )

    assert events == []
    assert object.__getattribute__(gate, "_consumed_tokens") == frozenset()


@pytest.mark.parametrize("variant", _TOKEN_VARIANTS)
def test_registered_permission_gate_rejects_invalid_token_fields_before_grant_iteration(
    variant: str,
) -> None:
    call = _call()
    token = _token(call)
    _mutate_token(token, call, variant)
    gate = PermissionGate()
    events: list[str] = []

    with pytest.raises(PermissionDenied, match="one-shot authorization fields"):
        gate.authorize_registered(
            _registry(),
            call,
            _grants(events),
            now_ms=100,
            one_shot=token,
        )

    assert events == []
    assert object.__getattribute__(gate, "_consumed_tokens") == frozenset()


@pytest.mark.parametrize(
    "variant",
    ("token_id_subclass", "request_id_subclass", "expiry_bool"),
)
def test_durable_occurrence_rejects_invalid_token_fields_before_registry_bind(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    variant: str,
) -> None:
    call = _call()
    token = _token(call)
    _mutate_token(token, call, variant)
    registry = _registry()
    store = SyntheticOccurrenceStore(tmp_path / "occurrences.sqlite")
    bind_calls: list[bool] = []
    original_bind = ToolRegistry.bind

    def counted_bind(self: ToolRegistry, bound_call: ToolCall) -> BoundAction:
        bind_calls.append(True)
        return original_bind(self, bound_call)

    monkeypatch.setattr(ToolRegistry, "bind", counted_bind)
    with pytest.raises(
        SyntheticReplayRejected,
        match="synthetic token fields must be exact valid values",
    ):
        store.reserve_synthetic(
            registry,
            call,
            token,
            occurrence_id="occ_" + "a" * 64,
            now_ms=42,
        )

    assert bind_calls == []
    assert store.count_synthetic() == 0


def test_permission_gate_rejects_replaced_token_admission_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call = _call()
    token = _token(call)
    gate = PermissionGate()
    monkeypatch.setattr(policy, "_admit_exact_one_shot_fields", lambda _token: None)

    with pytest.raises(PermissionDenied, match="admission implementation changed"):
        gate.authorize(
            ToolSpec("fixture.write", "fixture.write", Effect.WRITE),
            call,
            (CapabilityGrant("fixture.write", "scope:one", 500),),
            now_ms=100,
            one_shot=token,
        )


def test_synthetic_store_rejects_replaced_token_admission_helper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call = _call()
    token = _token(call)
    registry = _registry()
    store = SyntheticOccurrenceStore(tmp_path / "occurrences.sqlite")
    bind_calls: list[bool] = []
    original_bind = ToolRegistry.bind

    def counted_bind(self: ToolRegistry, bound_call: ToolCall) -> BoundAction:
        bind_calls.append(True)
        return original_bind(self, bound_call)

    monkeypatch.setattr(ToolRegistry, "bind", counted_bind)
    monkeypatch.setattr(occurrence, "_admit_exact_token_fields", lambda _token: ("x", "y", 1))

    with pytest.raises(
        SyntheticReplayRejected,
        match="synthetic token admission implementation changed",
    ):
        store.reserve_synthetic(
            registry,
            call,
            token,
            occurrence_id="occ_" + "b" * 64,
            now_ms=42,
        )

    assert bind_calls == []
    assert store.count_synthetic() == 0
