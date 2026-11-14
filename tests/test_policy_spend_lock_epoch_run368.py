"""Process-local spend checks must reject drift after grant iteration."""

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


class PauseBeforeSpend:
    def __init__(self):
        self.entered = Event()
        self.resume = Event()

    def __enter__(self):
        self.entered.set()
        assert self.resume.wait(timeout=5), "test lock did not resume"

    def __exit__(self, exc_type, exc, traceback):
        return False


@pytest.mark.parametrize("mutation", ["grant_scope", "grant_expiry", "spec_effect", "spec_name"])
def test_spend_rechecks_policy_epoch_after_contended_lock(mutation):
    gate = PermissionGate()
    call = ToolCall("synthetic_write", "fixture", "scope", {"x": 1})
    spec = ToolSpec("synthetic_write", "fixture", Effect.WRITE)
    grant = CapabilityGrant("fixture", "scope", 1000)
    token = OneShotAuthorization("synthetic-token", call.request_id, 1000)
    gate._token_lock = PauseBeforeSpend()
    outcomes = []

    def worker():
        try:
            gate.authorize(spec, call, (grant,), now_ms=10, one_shot=token)
            outcomes.append("incorrectly-allowed")
        except PermissionDenied as exc:
            outcomes.append(str(exc))

    thread = Thread(target=worker)
    thread.start()
    try:
        assert gate._token_lock.entered.wait(timeout=5)
        if mutation == "grant_scope":
            object.__setattr__(grant, "scope", "other")
        elif mutation == "grant_expiry":
            object.__setattr__(grant, "expires_at_ms", 0)
        elif mutation == "spec_effect":
            object.__setattr__(spec, "effect", Effect.READ)
        else:
            object.__setattr__(spec, "name", "other")
    finally:
        gate._token_lock.resume.set()
        thread.join(timeout=5)
    assert not thread.is_alive()
    assert outcomes == ["authorization input changed during token spend"]
    assert token.token_id not in gate._consumed_tokens

    # Recover the original immutable-contract values and verify no token was
    # spent on the rejected attempt. No real backend exists in this test.
    object.__setattr__(grant, "scope", "scope")
    object.__setattr__(grant, "expires_at_ms", 1000)
    object.__setattr__(spec, "effect", Effect.WRITE)
    object.__setattr__(spec, "name", "synthetic_write")
    gate._token_lock = Lock()
    gate.authorize(spec, call, (grant,), now_ms=10, one_shot=token)
    assert token.token_id in gate._consumed_tokens


def test_unchanged_grant_epoch_can_spend_once():
    gate = PermissionGate()
    call = ToolCall("synthetic_write", "fixture", "scope", {})
    spec = ToolSpec("synthetic_write", "fixture", Effect.WRITE)
    grant = CapabilityGrant("fixture", "scope", 500)
    token = OneShotAuthorization("another-synthetic-token", call.request_id, 500)
    gate.authorize(spec, call, (grant,), now_ms=0, one_shot=token)
    with pytest.raises(PermissionDenied, match="already consumed"):
        gate.authorize(spec, call, (grant,), now_ms=0, one_shot=token)
