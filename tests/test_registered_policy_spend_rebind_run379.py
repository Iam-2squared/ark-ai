"""Registered WRITE policy must rebind before spending a process-local token."""

from threading import Event, Thread

import pytest

from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    ToolCall,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverBackend:
    def execute(self, call):
        raise AssertionError("a policy check must never execute a ToolBackend")


def _fixture():
    registration = ToolRegistration(
        "fixture", "write", Effect.WRITE, "mock", NeverBackend()
    )
    registry = ToolRegistry((registration,))
    call = ToolCall("fixture", "write", "scope", {"secret": "fixture-only"})
    grant = CapabilityGrant("write", "scope", 1000)
    token = OneShotAuthorization("token", call.request_id, 1000)
    return registration, registry, call, grant, token


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("backend_id", "substituted"),
        ("effect", Effect.READ),
        ("capability", "other"),
        ("name", "other"),
    ],
)
def test_registry_drift_while_spend_lock_waits_preserves_token(field, replacement):
    registration, registry, call, grant, token = _fixture()
    gate = PermissionGate()
    gate._token_lock.acquire()
    ready = Event()
    outcomes = []

    def grants():
        yield grant
        ready.set()

    def worker():
        try:
            gate.authorize_registered(
                registry, call, grants(), now_ms=10, one_shot=token
            )
            outcomes.append("incorrect-success")
        except PermissionDenied as exc:
            outcomes.append(str(exc))

    thread = Thread(target=worker)
    thread.start()
    try:
        assert ready.wait(timeout=5), "grant iterator did not reach spend boundary"
        original = getattr(registration, field)
        object.__setattr__(registration, field, replacement)
    finally:
        gate._token_lock.release()
        thread.join(timeout=5)
    assert not thread.is_alive()
    assert len(outcomes) == 1
    assert "registered identity changed" in outcomes[0]
    assert token.token_id not in gate._consumed_tokens
    object.__setattr__(registration, field, original)
    result = gate.authorize_registered(
        registry, call, (grant,), now_ms=10, one_shot=token
    )
    assert result.bound_action_id == registry.bind(call).bound_action_id
    assert token.token_id in gate._consumed_tokens


def test_registered_write_unchanged_registry_spends_once():
    _registration, registry, call, grant, token = _fixture()
    gate = PermissionGate()
    bound = gate.authorize_registered(
        registry, call, (grant,), now_ms=10, one_shot=token
    )
    assert bound.registry_revision == registry.revision
    with pytest.raises(PermissionDenied, match="already consumed"):
        gate.authorize_registered(
            registry, call, (grant,), now_ms=10, one_shot=token
        )


def test_read_registry_instance_bind_shadow_is_denied_before_return(monkeypatch):
    registration, registry, call, grant, _token = _fixture()
    object.__setattr__(registration, "effect", Effect.READ)
    registry = ToolRegistry((registration,))
    gate = PermissionGate()
    original_bind = registry.bind
    bind_count = 0

    def shadowed_bind(current):
        nonlocal bind_count
        bind_count += 1
        object.__setattr__(registration, "backend_id", "other")
        return original_bind(current)

    monkeypatch.setattr(registry, "bind", shadowed_bind)
    with pytest.raises(
        PermissionDenied,
        match="registered authorization implementation identity changed",
    ):
        gate.authorize_registered(registry, call, (grant,), now_ms=10)

    assert bind_count == 0
    assert registration.backend_id == "mock"
    assert gate._consumed_tokens == set()
