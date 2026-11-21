"""Registered WRITE policy must rebind before spending a process-local token."""

import sys
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


def _run_during_token_lock_wait(gate, operation, mutate):
    """Pause the real authorize frame before its original lock acquisition."""
    lock = gate._token_lock
    lock.acquire()
    entered = Event()
    resume = Event()
    outcomes = []
    paused = False
    authorize_code = PermissionGate.authorize.__code__

    def trace(frame, event, _arg):
        nonlocal paused
        if (
            not paused
            and event == "line"
            and frame.f_code is authorize_code
            and frame.f_locals.get("token_lock") is lock
        ):
            paused = True
            entered.set()
            if not resume.wait(timeout=5):
                raise AssertionError("token spend did not resume")
        return trace

    def worker():
        sys.settrace(trace)
        try:
            operation()
        except Exception as exc:
            outcomes.append(f"{type(exc).__name__}: {exc}")
        else:
            outcomes.append("allowed")
        finally:
            sys.settrace(None)

    thread = Thread(target=worker)
    thread.start()
    try:
        assert entered.wait(timeout=5), "authorization did not reach token lock"
        mutate()
    finally:
        resume.set()
        lock.release()
        thread.join(timeout=5)
    assert not thread.is_alive()
    assert len(outcomes) == 1
    return outcomes[0]


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
    original = getattr(registration, field)

    def mutate():
        object.__setattr__(registration, field, replacement)

    outcome = _run_during_token_lock_wait(
        gate,
        lambda: gate.authorize_registered(
            registry, call, (grant,), now_ms=10, one_shot=token
        ),
        mutate,
    )
    assert "registered identity changed" in outcome
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
