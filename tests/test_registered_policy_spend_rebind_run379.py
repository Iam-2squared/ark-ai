"""Registered WRITE policy must rebind before spending a process-local token."""

from threading import Event, Lock, Thread

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


class PauseInSpend:
    def __init__(self):
        self.entered = Event()
        self.resume = Event()

    def __enter__(self):
        self.entered.set()
        assert self.resume.wait(timeout=5), "spend lock was not released"
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


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
    lock = PauseInSpend()
    gate._token_lock = lock
    outcomes = []

    def worker():
        try:
            gate.authorize_registered(
                registry, call, (grant,), now_ms=10, one_shot=token
            )
            outcomes.append("incorrect-success")
        except PermissionDenied as exc:
            outcomes.append(str(exc))

    thread = Thread(target=worker)
    thread.start()
    try:
        assert lock.entered.wait(timeout=5)
        original = getattr(registration, field)
        object.__setattr__(registration, field, replacement)
    finally:
        lock.resume.set()
        thread.join(timeout=5)
    assert not thread.is_alive()
    assert len(outcomes) == 1
    assert "registered identity changed" in outcomes[0]
    assert token.token_id not in gate._consumed_tokens
    object.__setattr__(registration, field, original)
    gate._token_lock = Lock()
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


def test_read_registry_drift_before_return_is_rejected(monkeypatch):
    registration, registry, call, grant, _token = _fixture()
    object.__setattr__(registration, "effect", Effect.READ)
    # A fresh registry must be created after changing the registration.
    registry = ToolRegistry((registration,))
    gate = PermissionGate()
    original = gate.authorize

    def mutate_after_policy(*args, **kwargs):
        result = original(*args, **kwargs)
        object.__setattr__(registration, "backend_id", "other")
        return result

    monkeypatch.setattr(gate, "authorize", mutate_after_policy)
    with pytest.raises(PermissionDenied, match="registered identity changed"):
        gate.authorize_registered(registry, call, (grant,), now_ms=10)
