"""Registered authorization refuses ToolRegistry instance-method shadows.

Synthetic registry and backend only. No real consent, tool dispatch, durable
approval, external action or trusted-clock claim is involved.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    ToolCall,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import BoundAction, ToolRegistration, ToolRegistry


class _NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("registered authorization must not dispatch")


def _fixture():
    backend = _NeverExecute()
    registration = ToolRegistration(
        "fixture.write",
        "fixture.write",
        Effect.WRITE,
        "disconnected.mock.v1",
        backend,
    )
    registry = ToolRegistry((registration,))
    call = ToolCall(
        "fixture.write",
        "fixture.write",
        "synthetic:scope",
        {"value": "local-only"},
    )
    gate = PermissionGate()
    grant = CapabilityGrant("fixture.write", "synthetic:scope")
    token = OneShotAuthorization("synthetic-token", call.request_id, 500)
    return backend, registration, registry, call, gate, grant, token


def test_slot_only_registry_rejects_instance_method_assignment() -> None:
    _backend, _registration, registry, _call, _gate, _grant, _token = _fixture()

    for member in ("bind", "resolve", "get", "revision", "_assert_registration_epoch"):
        replacement = lambda *_args, **_kwargs: None
        with pytest.raises(AttributeError, match="immutable"):
            setattr(registry, member, replacement)
        with pytest.raises(AttributeError):
            object.__setattr__(registry, member, replacement)


@pytest.mark.parametrize(
    "member",
    ("bind", "resolve", "get", "_assert_registration_epoch", "_compute_revision"),
)
def test_registered_write_rejects_class_level_registry_method_replacements_before_callbacks(
    member: str, monkeypatch,
) -> None:
    backend, registration, registry, call, gate, grant, token = _fixture()
    invoked: list[str] = []
    iterated: list[str] = []

    if member == "bind":
        # A forged but exact BoundAction can otherwise be returned twice by
        # an instance-shadowed bind() and appear stable to the old comparison.
        replacement = BoundAction(
            registry.revision, call, registration, "bound_forged_identity",
        )
        def shadowed(*_args, **_kwargs):
            invoked.append(member)
            return replacement
    else:
        def shadowed(*_args, **_kwargs):
            invoked.append(member)
            raise AssertionError("shadowed registry method executed")

    monkeypatch.setattr(type(registry), member, shadowed)

    def grants():
        iterated.append("started")
        yield grant

    with pytest.raises(
        PermissionDenied,
        match="registered authorization implementation identity changed",
    ):
        gate.authorize_registered(
            registry, call, grants(), now_ms=100, one_shot=token,
        )

    assert invoked == []
    assert iterated == []
    assert token.token_id not in gate._consumed_tokens
    assert backend.calls == 0


def test_read_authorization_also_rejects_class_level_bind_replacement(monkeypatch):
    backend, _registration, registry, call, gate, grant, _token = _fixture()
    invoked: list[str] = []

    def forged_bind(self, request):
        invoked.append("bind")
        return BoundAction(self.revision, request, _registration, "bound_forged")

    with monkeypatch.context() as patch:
        patch.setattr(ToolRegistry, "bind", forged_bind)
        with pytest.raises(
            PermissionDenied,
            match="registered authorization implementation identity changed",
        ):
            # READ has no one-shot token, but still requires an exact registry
            # binding. The old class check only pinned bind when a token existed.
            gate.authorize_registered(
                registry,
                call,
                (CapabilityGrant("fixture.write", "synthetic:scope"),),
                now_ms=100,
            )

    assert invoked == []
    assert backend.calls == 0


def test_grant_iterator_cannot_shadow_registry_after_initial_binding():
    backend, _registration, registry, call, gate, grant, token = _fixture()
    invoked: list[str] = []

    def shadowed_get(*_args, **_kwargs):
        invoked.append("get")
        raise AssertionError("shadowed get must not execute")

    def grants():
        yield grant
        registry.get = shadowed_get
        yield grant

    with pytest.raises(
        PermissionDenied,
        match="registered authorization implementation identity changed",
    ):
        gate.authorize_registered(
            registry, call, grants(), now_ms=100, one_shot=token,
        )

    assert invoked == []
    assert token.token_id not in gate._consumed_tokens
    assert backend.calls == 0
