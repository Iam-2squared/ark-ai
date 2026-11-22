"""Exact original policy carriers must survive WRITE approval callbacks.

All grants, identities and tokens are synthetic. Token consumption is only
process-local and never conveys durable consent or dispatch authority.
"""

import sys
from threading import Event, Thread

import pytest

from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    ToolCall,
    ToolSpec,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class NoBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("permission tests must not dispatch")


def _case():
    call = ToolCall("fixture", "mock.write", "offline")
    spec = ToolSpec("fixture", "mock.write", Effect.WRITE)
    grant = CapabilityGrant("mock.write", "offline", 1000)
    token = OneShotAuthorization("local-token-unique", call.request_id, 1000)
    backend = NoBackend()
    registry = ToolRegistry((
        ToolRegistration("fixture", "mock.write", Effect.WRITE, "mock", backend),
    ))
    return PermissionGate(), spec, call, grant, token, registry, backend


def _distinct(value):
    if type(value) is int:
        copy = int(str(value))
    else:
        copy = ("!" + value)[1:]
    assert copy == value and copy is not value
    return copy


def _carrier_to_mutate(case, field):
    _gate, spec, call, _grant, token, _registry, _backend = case
    if field.startswith("spec_"):
        return spec, field.removeprefix("spec_")
    if field.startswith("call_"):
        return call, field.removeprefix("call_")
    return token, field.removeprefix("token_")


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



@pytest.mark.parametrize("registered", (False, True))
@pytest.mark.parametrize("phase", ("grants", "spend"))
@pytest.mark.parametrize("field", (
    "call_tool",
    "call_capability",
    "call_scope",
    "token_token_id",
    "token_request_id",
    "token_expires_at_ms",
))
def test_equal_value_original_call_or_token_swap_never_spends(
    registered, phase, field,
):
    case = _case()
    gate, spec, call, grant, token, registry, backend = case
    target, attr = _carrier_to_mutate(case, field)
    original = getattr(target, attr)
    modified = []

    def mutate():
        assert not modified
        object.__setattr__(target, attr, _distinct(original))
        modified.append(True)

    def grants():
        yield grant
        if phase == "grants":
            mutate()

    def invoke():
        if registered:
            gate.authorize_registered(
                registry, call, grants(), now_ms=10, one_shot=token,
            )
        else:
            gate.authorize(spec, call, grants(), now_ms=10, one_shot=token)

    if phase == "spend":
        outcome = _run_during_token_lock_wait(gate, invoke, mutate)
        assert "identity" in outcome or "input changed" in outcome
    else:
        with pytest.raises(PermissionDenied, match="identity|input changed"):
            invoke()
    assert modified == [True]
    assert gate._consumed_tokens == set()
    assert backend.calls == 0


@pytest.mark.parametrize("phase", ("grants", "spend"))
@pytest.mark.parametrize("field", ("spec_name", "spec_capability"))
def test_equal_value_tool_spec_swap_cannot_authorize_direct_write(phase, field):
    case = _case()
    gate, spec, call, grant, token, _registry, backend = case
    target, attr = _carrier_to_mutate(case, field)
    original = getattr(target, attr)
    modified = []

    def mutate():
        object.__setattr__(target, attr, _distinct(original))
        modified.append(True)

    def grants():
        yield grant
        if phase == "grants":
            mutate()

    def invoke():
        gate.authorize(spec, call, grants(), now_ms=10, one_shot=token)

    if phase == "spend":
        outcome = _run_during_token_lock_wait(gate, invoke, mutate)
        assert "input changed" in outcome
    else:
        with pytest.raises(PermissionDenied, match="input changed"):
            invoke()
    assert modified == [True]
    assert gate._consumed_tokens == set()
    assert backend.calls == 0


@pytest.mark.parametrize("registered", (False, True))
def test_unchanged_policy_still_spends_once_without_dispatch(registered):
    gate, spec, call, grant, token, registry, backend = _case()
    if registered:
        result = gate.authorize_registered(
            registry, call, (grant,), now_ms=10, one_shot=token,
        )
        assert result.call is call
    else:
        assert gate.authorize(
            spec, call, (grant,), now_ms=10, one_shot=token,
        ) is None
    assert gate._consumed_tokens == {"local-token-unique"}
    assert backend.calls == 0
