"""Process-local spend checks must reject drift after grant iteration."""

import sys
from threading import Event, Lock, Thread

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


@pytest.mark.parametrize("mutation", ["grant_scope", "grant_expiry", "spec_effect", "spec_name"])
def test_spend_rechecks_policy_epoch_after_contended_lock(mutation):
    gate = PermissionGate()
    call = ToolCall("synthetic_write", "fixture", "scope", {"x": 1})
    spec = ToolSpec("synthetic_write", "fixture", Effect.WRITE)
    grant = CapabilityGrant("fixture", "scope", 1000)
    token = OneShotAuthorization("synthetic-token", call.request_id, 1000)

    def mutate():
        if mutation == "grant_scope":
            object.__setattr__(grant, "scope", "other")
        elif mutation == "grant_expiry":
            object.__setattr__(grant, "expires_at_ms", 0)
        elif mutation == "spec_effect":
            object.__setattr__(spec, "effect", Effect.READ)
        else:
            object.__setattr__(spec, "name", "other")

    outcome = _run_during_token_lock_wait(
        gate,
        lambda: gate.authorize(spec, call, (grant,), now_ms=10, one_shot=token),
        mutate,
    )
    assert outcome == (
        "PermissionDenied: authorization input changed during token spend"
    )
    assert token.token_id not in gate._consumed_tokens

    # Recover the original immutable-contract values and verify no token was
    # spent on the rejected attempt. No real backend exists in this test.
    object.__setattr__(grant, "scope", "scope")
    object.__setattr__(grant, "expires_at_ms", 1000)
    object.__setattr__(spec, "effect", Effect.WRITE)
    object.__setattr__(spec, "name", "synthetic_write")
    gate.authorize(spec, call, (grant,), now_ms=10, one_shot=token)
    assert token.token_id in gate._consumed_tokens


def test_reflective_token_lock_replacement_is_denied_before_grant_iteration():
    gate = PermissionGate()
    call = ToolCall("synthetic_write", "fixture", "scope", {"x": 1})
    spec = ToolSpec("synthetic_write", "fixture", Effect.WRITE)
    grant = CapabilityGrant("fixture", "scope", 1000)
    token = OneShotAuthorization("replacement-lock-token", call.request_id, 1000)
    object.__setattr__(gate, "_token_lock", Lock())
    visited = []

    def grants():
        visited.append(True)
        yield grant

    with pytest.raises(PermissionDenied, match="state changed outside token spend"):
        gate.authorize(spec, call, grants(), now_ms=10, one_shot=token)

    assert visited == []
    assert gate._consumed_tokens == set()


def test_unchanged_grant_epoch_can_spend_once():
    gate = PermissionGate()
    call = ToolCall("synthetic_write", "fixture", "scope", {})
    spec = ToolSpec("synthetic_write", "fixture", Effect.WRITE)
    grant = CapabilityGrant("fixture", "scope", 500)
    token = OneShotAuthorization("another-synthetic-token", call.request_id, 500)
    gate.authorize(spec, call, (grant,), now_ms=0, one_shot=token)
    with pytest.raises(PermissionDenied, match="already consumed"):
        gate.authorize(spec, call, (grant,), now_ms=0, one_shot=token)
