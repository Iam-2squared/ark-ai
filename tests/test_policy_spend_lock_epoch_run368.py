"""Process-local spend checks must reject drift after grant iteration."""

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


@pytest.mark.parametrize("mutation", ["grant_scope", "grant_expiry", "spec_effect", "spec_name"])
def test_spend_rechecks_policy_epoch_after_contended_lock(mutation):
    gate = PermissionGate()
    call = ToolCall("synthetic_write", "fixture", "scope", {"x": 1})
    spec = ToolSpec("synthetic_write", "fixture", Effect.WRITE)
    grant = CapabilityGrant("fixture", "scope", 1000)
    token = OneShotAuthorization("synthetic-token", call.request_id, 1000)
    gate._token_lock.acquire()
    ready = Event()
    outcomes = []

    def grants():
        yield grant
        ready.set()

    def worker():
        try:
            gate.authorize(spec, call, grants(), now_ms=10, one_shot=token)
            outcomes.append("incorrectly-allowed")
        except PermissionDenied as exc:
            outcomes.append(str(exc))

    thread = Thread(target=worker)
    thread.start()
    try:
        assert ready.wait(timeout=5), "grant iterator did not reach spend boundary"
        if mutation == "grant_scope":
            object.__setattr__(grant, "scope", "other")
        elif mutation == "grant_expiry":
            object.__setattr__(grant, "expires_at_ms", 0)
        elif mutation == "spec_effect":
            object.__setattr__(spec, "effect", Effect.READ)
        else:
            object.__setattr__(spec, "name", "other")
    finally:
        gate._token_lock.release()
        thread.join(timeout=5)
    assert not thread.is_alive()
    assert len(outcomes) == 1
    assert "changed" in outcomes[0]
    assert token.token_id not in gate._consumed_tokens

    # Restore only the synthetic carrier values; the rejected attempt did not
    # consume the token and the original process-local lock remains installed.
    object.__setattr__(grant, "scope", "scope")
    object.__setattr__(grant, "expires_at_ms", 1000)
    object.__setattr__(spec, "effect", Effect.WRITE)
    object.__setattr__(spec, "name", "synthetic_write")
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
